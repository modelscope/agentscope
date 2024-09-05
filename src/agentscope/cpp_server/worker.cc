#include <cstdlib>
#include <fcntl.h>
#include <sys/mman.h>
#include <semaphore.h>
#include <sys/stat.h>
#include <unistd.h>
#include <sys/wait.h>
#include <random>
#include <errno.h>
#include <sys/types.h>
#include <signal.h>
#include <sys/sem.h>

#include "worker.h"

using std::getenv;
using std::to_string;

using namespace pybind11::literals;

using WorkerArgs::AgentArgs;
using WorkerArgs::CreateAgentArgs;
using WorkerArgs::ModelConfigsArgs;
using WorkerArgs::ObserveArgs;
using WorkerArgs::ReplyArgs;
using WorkerArgs::MsgReturn;
using WorkerArgs::AgentListReturn;

Task::Task(const int task_id)
    : _task_id(task_id),
      _task_result(),
      _task_finished(false)
{
}

int Task::task_id()
{
    return this->_task_id;
}

string Task::get_result()
{
    unique_lock<mutex> lock(_task_mutex);
    _task_cv.wait(lock, [this]()
                  { return this->_task_finished; });
    return _task_result;
}

void P(int semid, unsigned short sem_num)
{
    struct sembuf sb = {sem_num, -1, 0};
    semop(semid, &sb, 1);
}

void V(int semid, unsigned short sem_num)
{
    struct sembuf sb = {sem_num, 1, 0};
    semop(semid, &sb, 1);
}

Worker::Worker(
    const string &host,
    const string &port,
    const string &server_id,
    const string &studio_url,
    const unsigned int max_tasks,
    const unsigned int max_timeout_seconds,
    const unsigned int num_workers) : _host(host), _port(port), _server_id(server_id),
                                      _main_worker_pid(getpid()),
                                      _num_workers(std::max(num_workers, 1u)),
                                      _worker_id(-1),
                                      _sem_num_per_sem_id(10000),
                                      _call_shm_size(1024),
                                      _max_call_id(calc_max_call_id()),
                                      _small_obj_size(1000),
                                      _small_obj_shm_size(1024),
                                      _call_worker_shm_name("/call_" + port),
                                      _func_args_shm_prefix("/args_" + port + "_"),
                                      _func_result_shm_prefix("/result_" + port + "_"),
                                      _worker_avail_sem_prefix("/avail_" + port + "_"),
                                      _func_ready_sem_prefix("/func_" + port + "_"),
                                      _small_obj_pool_shm_name("/small_obj_pool_shm_" + port),
                                      _use_logger(calc_use_logger()),
                                      _num_tasks(0),
                                      _max_tasks(std::max(max_tasks, 1u)),
                                      _max_timeout_seconds(std::max(max_timeout_seconds, 1u))
{
    py::object serialize_lib = py::module::import("agentscope.serialize");
    _serialize = serialize_lib.attr("serialize");
    _deserialize = serialize_lib.attr("deserialize");
    py::gil_scoped_release release;
    struct stat info;
    if (stat("./logs/", &info) != 0)
    {
        mkdir("./logs", 0755);
    }

    // init call worker shm
    _call_worker_shm_fd = shm_open(_call_worker_shm_name.c_str(), O_CREAT | O_RDWR, 0666);
    if (_call_worker_shm_fd == -1)
    {
        perror("Error: shm_open in Worker::Worker()");
        kill(_main_worker_pid, SIGINT);
    }
    ftruncate(_call_worker_shm_fd, _num_workers * _call_shm_size);
    void *call_worker_shm = mmap(NULL, _num_workers * _call_shm_size, PROT_READ | PROT_WRITE, MAP_SHARED, _call_worker_shm_fd, 0);
    if (call_worker_shm == MAP_FAILED)
    {
        perror("Error: mmap in Worker::Worker()");
        kill(_main_worker_pid, SIGINT);
    }
    _call_worker_shm = (char *)call_worker_shm;

    // init small object pool
    _small_obj_pool_shm_fd = shm_open(_small_obj_pool_shm_name.c_str(), O_CREAT | O_RDWR, 0666);
    if (_small_obj_pool_shm_fd == -1)
    {
        perror("Error: shm_open in create _small_obj_pool_shm_fd");
        kill(_main_worker_pid, SIGINT);
    }
    ftruncate(_small_obj_pool_shm_fd, _max_call_id * _small_obj_shm_size);
    _small_obj_pool_shm = mmap(NULL, _max_call_id * _small_obj_shm_size, PROT_READ | PROT_WRITE, MAP_SHARED, _small_obj_pool_shm_fd, 0);
    if (_small_obj_pool_shm == MAP_FAILED)
    {
        perror("Error: mmap in _small_obj_pool_shm");
        kill(_main_worker_pid, SIGINT);
    }
    memset(_small_obj_pool_shm, 0, _max_call_id * _small_obj_shm_size);
    for (auto i = 0u; i < _max_call_id; i++)
    {
        _call_id_pool.push(i);
    }

    // init call semaphores
    string filename = "./logs/" + _port + ".log";
    int fd = open(filename.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd == -1)
    {
        perror("Error: Failed to open file");
        kill(_main_worker_pid, SIGINT);
    }
    close(fd);
    unsigned short *_sem_values = new unsigned short[_sem_num_per_sem_id]();
    for (int i = 0; i * _sem_num_per_sem_id < _max_call_id; i++)
    {
        key_t key = ftok(filename.c_str(), i);
        if (key == -1)
        {
            perror("Error: ftok in Worker::Worker()");
            kill(_main_worker_pid, SIGINT);
        }
        int semid = semget(key, _sem_num_per_sem_id, 0666 | IPC_CREAT);
        if (semid == -1)
        {
            perror("Error: semget in Worker::Worker()");
            kill(_main_worker_pid, SIGINT);
        }
        semctl(semid, 0, SETALL, _sem_values);
        _call_sem_ids.push_back(semid);
    }
    delete[] _sem_values;

    // launch workers
    for (auto i = 0u; i < _num_workers; i++)
    {
        string worker_avail_sem_name = _worker_avail_sem_prefix + to_string(i);
        string func_ready_sem_name = _func_ready_sem_prefix + to_string(i);
        sem_t *worker_avail_sem = sem_open(worker_avail_sem_name.c_str(), O_CREAT, 0666, 0);
        sem_t *func_ready_sem = sem_open(func_ready_sem_name.c_str(), O_CREAT, 0666, 0);
        _worker_semaphores.push_back(make_pair(worker_avail_sem, func_ready_sem));

        pid_t pid = fork();
        if (pid > 0)
        {
            // parent process
            _worker_pids.push_back(pid);
        }
        else if (pid == 0)
        {
            // child process
            string filename = "./logs/" + _port + "-" + to_string(i) + ".log";
            int fd = open(filename.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
            if (fd == -1)
            {
                perror("Error: Failed to open file");
                kill(_main_worker_pid, SIGINT);
            }
            if (dup2(fd, STDOUT_FILENO) == -1 || dup2(fd, STDERR_FILENO) == -1)
            {
                perror("Error: Failed to redirect stdout/stderr");
                kill(_main_worker_pid, SIGINT);
            }
            close(fd);

            _worker_id = i;
            char *shm_ptr = _call_worker_shm + i * _call_shm_size;
            sem_post(worker_avail_sem);
            while (true)
            {
                sem_wait(func_ready_sem);
                int call_id = *(int *)shm_ptr;
                int function_id = *(int *)(shm_ptr + sizeof(int));
                logger("call_id = " + to_string(call_id) + " function_id = " + to_string(function_id));
                thread work;
                switch (function_id)
                {
                case function_ids::create_agent:
                {
                    work = thread(&Worker::create_agent_worker, this, call_id);
                    break;
                }
                case function_ids::delete_agent:
                {
                    work = thread(&Worker::delete_agent_worker, this, call_id);
                    break;
                }
                case function_ids::delete_all_agents:
                {
                    work = thread(&Worker::delete_all_agents_worker, this, call_id);
                    break;
                }
                case function_ids::clone_agent:
                {
                    work = thread(&Worker::clone_agent_worker, this, call_id);
                    break;
                }
                case function_ids::get_agent_list:
                {
                    work = thread(&Worker::get_agent_list_worker, this, call_id);
                    break;
                }
                case function_ids::set_model_configs:
                {
                    work = thread(&Worker::set_model_configs_worker, this, call_id);
                    break;
                }
                case function_ids::get_agent_memory:
                {
                    work = thread(&Worker::get_agent_memory_worker, this, call_id);
                    break;
                }
                case function_ids::reply:
                {
                    work = thread(&Worker::reply_worker, this, call_id);
                    break;
                }
                case function_ids::observe:
                {
                    work = thread(&Worker::observe_worker, this, call_id);
                    break;
                }
                case function_ids::server_info:
                {
                    work = thread(&Worker::server_info_worker, this, call_id);
                    break;
                }
                }
                work.detach();
                sem_post(worker_avail_sem);
            }
            kill(_main_worker_pid, SIGINT);
        }
        else if (pid < 0)
        {
            perror("Error: fork failed in Worker::Worker()");
            kill(_main_worker_pid, SIGINT);
        }
    }
}

Worker::~Worker() // for main process to release resources
{
    // release call_worker_shm
    close(_call_worker_shm_fd);
    munmap(_call_worker_shm, _num_workers * _call_shm_size);

    // release small object pool
    close(_small_obj_pool_shm_fd);
    munmap(_small_obj_pool_shm, _max_call_id * _small_obj_shm_size);

    // release worker semaphores
    for (auto iter : _worker_semaphores)
    {
        sem_t *worker_avail_sem = iter.first;
        sem_t *func_ready_sem = iter.second;
        sem_close(func_ready_sem);
        sem_close(worker_avail_sem);
    }

    if (_main_worker_pid == getpid())
    {
        for (auto pid : _worker_pids)
        {
            kill(pid, SIGINT);
            waitpid(pid, NULL, 0);
        }

        shm_unlink(_call_worker_shm_name.c_str());
        shm_unlink(_small_obj_pool_shm_name.c_str());
        // release call semaphores
        for (auto semid : _call_sem_ids)
        {
            semctl(semid, 0, IPC_RMID);
        }

        // release worker semaphores
        for (auto i = 0u; i < _worker_semaphores.size(); i++)
        {
            string worker_avail_sem_name = _worker_avail_sem_prefix + to_string(i);
            string func_ready_sem_name = _func_ready_sem_prefix + to_string(i);
            sem_unlink(worker_avail_sem_name.c_str());
            sem_unlink(func_ready_sem_name.c_str());
        }

        // release large object shm
        for (auto call_id = 0u; call_id < _max_call_id; call_id++)
        {
            for (auto prefix : {_func_args_shm_prefix, _func_result_shm_prefix})
            {
                string shm_name = prefix + to_string(call_id);
                int shm_fd = shm_open(shm_name.c_str(), O_RDONLY, 0666);
                if (shm_fd != -1)
                {
                    close(shm_fd);
                    shm_unlink(shm_name.c_str());
                }
            }
        }
    }
    else
    {
        kill(_main_worker_pid, SIGINT);
    }
}

int Worker::find_avail_worker_id()
{
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, _num_workers - 1);
    int i;
    for (auto cnt = 0u; cnt < 4 * _num_workers; cnt++)
    {
        i = dis(gen);
        if (sem_trywait(_worker_semaphores[i].first) == 0)
        {
            logger("get worker id: " + to_string(i));
            return i;
        }
    }
    sem_wait(_worker_semaphores[i].first);
    logger("get worker id: " + to_string(i));
    return i;
}

int Worker::get_call_id()
{
    unique_lock<mutex> lock(_call_id_mutex);
    _call_id_cv.wait(lock, [this]
                     { return !_call_id_pool.empty(); });
    int call_id = _call_id_pool.front();
    _call_id_pool.pop();
    return call_id;
}

string Worker::get_content(const string &prefix, const int call_id)
{
    char *small_obj_shm = (char *)_small_obj_pool_shm + call_id * _small_obj_shm_size;
    int *occupied = (int *)small_obj_shm;
    logger("get_content 0: occupied = " + to_string(*occupied) + " call_id = " + to_string(call_id) + " " + to_string(*(int *)(small_obj_shm)) + " " + to_string(*(int *)(small_obj_shm + sizeof(int))));
    if (*occupied)
    {
        int content_size = *(int *)(small_obj_shm + sizeof(int));
        string result(small_obj_shm + sizeof(int) * 2, small_obj_shm + sizeof(int) * 2 + content_size);
        logger("get_content in pool " + to_string(call_id) + " [" + result + "]");
        *occupied = false;
        return result;
    }
    string shm_name = prefix + to_string(call_id);
    int shm_fd = shm_open(shm_name.c_str(), O_RDONLY, 0666);
    if (shm_fd == -1)
    {
        perror(("Error: shm_open in get_content: " + shm_name).c_str());
        kill(_main_worker_pid, SIGINT);
    }
    struct stat shm_stat;
    if (fstat(shm_fd, &shm_stat) == -1)
    {
        close(shm_fd);
        perror(("Error: fstat in get_content: " + shm_name).c_str());
        kill(_main_worker_pid, SIGINT);
    }
    auto shm_size = shm_stat.st_size;
    logger("get_content 1: shm_name = " + shm_name + " shm_size = " + to_string(shm_size));
    void *shm = mmap(NULL, shm_size, PROT_READ, MAP_SHARED, shm_fd, 0);
    if (shm == MAP_FAILED)
    {
        perror(("Error: mmap in get_content: " + shm_name).c_str());
        kill(_main_worker_pid, SIGINT);
    }
    int content_size = *(int *)shm;
    string content((char *)shm + sizeof(int), (char *)shm + sizeof(int) + content_size);
    logger("get_content 2: shm_name = " + shm_name + " content_size = " + to_string(content_size) + " content = [" + content + "]");
    munmap(shm, shm_size);
    close(shm_fd);
    shm_unlink(shm_name.c_str());
    return content;
}

void Worker::set_content(const string &prefix, const int call_id, const string &content)
{
    logger("set_content: " + to_string(content.size()) + " content = [" + content + "]");
    if (content.size() <= _small_obj_size)
    {
        logger("set_content in pool ");
        char *small_obj_shm = (char *)_small_obj_pool_shm + call_id * _small_obj_shm_size;
        *(int *)small_obj_shm = true;
        *(int *)(small_obj_shm + sizeof(int)) = content.size();
        memcpy(small_obj_shm + sizeof(int) * 2, content.c_str(), content.size());
        return;
    }
    string shm_name = prefix + to_string(call_id);
    int shm_fd = shm_open(shm_name.c_str(), O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1)
    {
        perror(("Error: shm_open in set_content: " + shm_name).c_str());
        kill(_main_worker_pid, SIGINT);
    }
    logger("set_content: " + shm_name + " content = [" + content + "]");
    int shm_size = content.size() + sizeof(int);
    ftruncate(shm_fd, shm_size);
    void *shm = mmap(NULL, shm_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (shm == MAP_FAILED)
    {
        perror(("Error: mmap in set_content: " + shm_name).c_str());
        kill(_main_worker_pid, SIGINT);
    }
    *(int *)shm = (int)content.size();
    memcpy((char *)shm + sizeof(int), content.c_str(), content.size());
    munmap(shm, shm_size);
    close(shm_fd);
    logger("set_content: " + shm_name + " final, shm_size = " + to_string(shm_size));
}

string Worker::get_args_repr(const int call_id)
{
    return get_content(_func_args_shm_prefix, call_id);
}

void Worker::set_args_repr(const int call_id, const string &args_repr)
{
    set_content(_func_args_shm_prefix, call_id, args_repr);
}

string Worker::get_result(const int call_id)
{
    P(_call_sem_ids[call_id / _sem_num_per_sem_id], call_id % _sem_num_per_sem_id);
    string result = get_content(_func_result_shm_prefix, call_id);
    {
        unique_lock lock(_call_id_mutex);
        _call_id_pool.push(call_id);
        _call_id_cv.notify_one();
    }
    return result;
}

void Worker::set_result(const int call_id, const string &result)
{
    set_content(_func_result_shm_prefix, call_id, result);
    V(_call_sem_ids[call_id / _sem_num_per_sem_id], call_id % _sem_num_per_sem_id);
}

int Worker::get_worker_id_by_agent_id(const string &agent_id)
{
    shared_lock<shared_mutex> lock(_agent_id_map_mutex);
    if (_agent_id_map.find(agent_id) != _agent_id_map.end())
    {
        return _agent_id_map[agent_id];
    }
    else
    {
        return -1;
    }
}

pair<int, int> Worker::get_task_id_and_callback_id()
{
    if (_tasks_head_mutex.try_lock())
    {
        // remove front
        while (!_tasks.empty() && _tasks.front().second->_task_finished && (_tasks.size() >= _max_tasks || is_timeout(_tasks.front().first)))
        {
            std::cout << "takes " << _tasks.front().second->task_id() << std::endl;
            _tasks.pop_front();
        }
        _tasks_head_mutex.unlock();
    }
    unique_lock<mutex> lock(_tasks_tail_mutex);
    int task_id = _num_tasks;
    _num_tasks++;
    int callback_id = get_call_id();
    int current_timestamp = get_current_timestamp();
    logger("get_task_id_and_callback_id 1: task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id));
    _tasks.emplace_back(make_pair(current_timestamp, std::make_unique<Task>(task_id)));
    auto &task = _tasks.back().second;
    lock.unlock();
    thread work = thread([this, callback_id, &task]()
                         {
                             this->logger("Task " + to_string(task->task_id()) + " is running");
                             task->_task_result = this->get_result(callback_id);
                             this->logger("Task " + to_string(task->task_id()) + " is finished with task->_task_result = [" + task->_task_result + "]");
                             unique_lock<mutex> task_lock(task->_task_mutex);
                             task->_task_finished = true;
                             task->_task_cv.notify_all(); });
    work.detach();
    logger("get_task_id_and_callback_id 2: task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " finished. ");
    return make_pair(task_id, callback_id);
}

pair<bool, string> Worker::get_task_result(const int task_id)
{
    logger("get_task_result 1: task_id = " + to_string(task_id));
    shared_lock<shared_mutex> lock(_tasks_head_mutex);
    const auto &first_task = _tasks.front();
    int first_task_id = first_task.second->task_id();
    int idx = task_id - first_task_id;
    logger("get_task_result 2: task_id = " + to_string(task_id) + " idx = " + to_string(idx));
    if (0 <= idx && idx < (int)_tasks.size())
    {
        string result_str = _tasks[idx].second->get_result();
        logger("get_task_result 3: task_id = " + to_string(task_id) + " idx = " + to_string(idx) + " result_str = [" + result_str + "]");
        MsgReturn result;
        result.ParseFromString(result_str);
        logger("get_task_result 4: task_id = " + to_string(task_id) + " idx = " + to_string(idx) + " result_ok = " + to_string(result.ok()) + " result_str = [" + result_str + "]");
        return make_pair(result.ok(), result.message());
    }
    else
    {
        return make_pair(false, "");
    }
}

int Worker::call_worker_func(const int worker_id, const function_ids func_id, const Message *args, const bool need_wait)
{
    if (need_wait)
    {
        sem_wait(_worker_semaphores[worker_id].first);
    }
    int call_id = get_call_id();
    *(int *)(_call_worker_shm + worker_id * _call_shm_size) = call_id;
    *(int *)(_call_worker_shm + worker_id * _call_shm_size + sizeof(int)) = func_id;
    logger("call_worker_func 1: " + to_string(func_id) + " call_id = " + to_string(call_id));
    if (args != nullptr)
    {
        string args_str = args->SerializeAsString();
        set_args_repr(call_id, args_str);
    }
    sem_post(_worker_semaphores[worker_id].second);
    logger("call_worker_func 3: " + to_string(func_id) + " call_id = " + to_string(call_id) + " finished!");
    return call_id;
}

string Worker::call_create_agent(const string &agent_id, const string &agent_init_args, const string &agent_source_code)
{
    if (get_worker_id_by_agent_id(agent_id) != -1)
    {
        return "Agent with agent_id [" + agent_id + "] already exists.";
    }
    logger("call_create_agent 1:" + agent_id);
    int worker_id = find_avail_worker_id();
    CreateAgentArgs args;
    args.set_agent_id(agent_id);
    args.set_agent_init_args(agent_init_args);
    args.set_agent_source_code(agent_source_code);
    int call_id = call_worker_func(worker_id, function_ids::create_agent, &args, false);
    logger("call_create_agent 2:" + agent_id + " call_id = " + to_string(call_id) + " worker_id = " + to_string(worker_id));
    string result = get_result(call_id);
    if (result.empty())
    {
        unique_lock<shared_mutex> lock(_agent_id_map_mutex);
        _agent_id_map.insert(std::make_pair(agent_id, worker_id));
    }
    logger("call_create_agent 3: " + agent_id + " call_id = " + to_string(call_id) + " worker_id = " + to_string(worker_id) + " result = [" + result + "]");
    return result;
}

void Worker::create_agent_worker(const int call_id)
{
    logger("create_agent_worker: call_id = " + to_string(call_id) + " start!");
    string args_repr = get_args_repr(call_id);
    CreateAgentArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();
    string agent_init_args = args.agent_init_args();
    string agent_source_code = args.agent_source_code();
    logger("create_agent_worker: call_id = " + to_string(call_id) + " agent_id = " + agent_id);

    py::gil_scoped_acquire acquire;
    py::tuple create_result = py::module::import("agentscope.cpp_server").attr("create_agent")(agent_id, py::bytes(agent_init_args), py::bytes(agent_source_code));
    py::object agent = create_result[0];
    py::object error_msg = create_result[1];
    string result = error_msg.cast<string>();
    if (result.empty())
    {
        unique_lock<shared_mutex> lock(_agent_pool_mutex);
        _agent_pool.insert(std::make_pair(agent_id, agent));
    }
    logger("create_agent_worker: call_id = " + to_string(call_id) + " result = " + result);
    set_result(call_id, result);
}

string Worker::call_delete_agent(const string &agent_id)
{
    int worker_id = get_worker_id_by_agent_id(agent_id);
    if (worker_id == -1)
    {
        return "Try to delete a non-existent agent [" + agent_id + "].";
    }
    AgentArgs args;
    args.set_agent_id(agent_id);
    int call_id = call_worker_func(worker_id, function_ids::delete_agent, &args);
    {
        unique_lock<shared_mutex> lock(_agent_id_map_mutex);
        _agent_id_map.erase(agent_id);
    }
    string result = get_result(call_id);
    return result;
}

void Worker::delete_agent_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    AgentArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();

    py::gil_scoped_acquire acquire;
    unique_lock<shared_mutex> lock(_agent_pool_mutex);
    auto agent = _agent_pool[agent_id];
    if (py::hasattr(agent, "__del__"))
    {
        agent.attr("__del__")();
    }
    _agent_pool.erase(agent_id);
    set_result(call_id, "");
}

string Worker::call_delete_all_agents()
{
    vector<int> call_id_list;
    {
        unique_lock<shared_mutex> lock(_agent_id_map_mutex);
        for (auto worker_id = 0u; worker_id < _num_workers; worker_id++)
        {
            int call_id = call_worker_func(worker_id, function_ids::delete_all_agents, nullptr);
            call_id_list.push_back(call_id);
        }
        _agent_id_map.clear();
    }
    string final_result;
    for (auto call_id : call_id_list)
    {
        string result = get_result(call_id);
        final_result += result;
    }
    return final_result;
}

void Worker::delete_all_agents_worker(const int call_id)
{
    py::gil_scoped_acquire acquire;
    unique_lock<shared_mutex> lock(_agent_pool_mutex);
    for (auto &agent : _agent_pool)
    {
        if (py::hasattr(agent.second, "__del__"))
        {
            agent.second.attr("__del__")();
        }
    }
    _agent_pool.clear();
    set_result(call_id, "");
}

pair<bool, string> Worker::call_clone_agent(const string &agent_id)
{
    int worker_id = get_worker_id_by_agent_id(agent_id);
    if (worker_id == -1)
    {
        return make_pair(false, "Try to clone a non-existent agent [" + agent_id + "].");
    }
    AgentArgs args;
    args.set_agent_id(agent_id);
    int call_id = call_worker_func(worker_id, function_ids::clone_agent, &args);
    string clone_agent_id = get_result(call_id);
    {
        unique_lock<shared_mutex> lock(_agent_id_map_mutex);
        _agent_id_map.insert(std::make_pair(clone_agent_id, worker_id));
    }
    return make_pair(true, clone_agent_id);
}

void Worker::clone_agent_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    AgentArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();

    py::gil_scoped_acquire acquire;
    shared_lock<shared_mutex> read_lock(_agent_pool_mutex);
    py::object agent = _agent_pool[agent_id];
    py::object agent_class = agent.attr("__class__");
    py::object agent_args = agent.attr("_init_settings")["args"];
    py::object agent_kwargs = agent.attr("_init_settings")["kwargs"];
    read_lock.unlock();
    py::object clone_agent = agent_class(*agent_args, **agent_kwargs);
    string clone_agent_id = clone_agent.attr("agent_id").cast<string>();
    {
        unique_lock<shared_mutex> lock(_agent_pool_mutex);
        _agent_pool.insert(std::make_pair(clone_agent_id, clone_agent));
    }
    set_result(call_id, clone_agent_id);
}

string Worker::call_get_agent_list()
{
    vector<int> call_id_list;
    {
        shared_lock<shared_mutex> lock(_agent_id_map_mutex);
        for (auto worker_id = 0u; worker_id < _num_workers; worker_id++)
        {
            int call_id = call_worker_func(worker_id, function_ids::get_agent_list, nullptr);
            call_id_list.push_back(call_id);
        }
    }
    // string final_result = "[";
    vector<string> result_list;
    for (auto call_id : call_id_list)
    {
        string result_str = get_result(call_id);
        AgentListReturn result;
        result.ParseFromString(result_str);
        for (const auto &agent_str : result.agent_str_list())
        {
            result_list.push_back(agent_str);
        }
        // logger("call_get_agent_list 1: call_id = " + to_string(call_id) + " result = [" + result + "]");
        // if (final_result != "[" && !result.empty())
        //     final_result += ",";
        // final_result += result;
    }
    // final_result += "]";
    py::gil_scoped_acquire acquire;
    logger("call_get_agent_list 1: result_list.size() = [" + to_string(result_list.size()) + "]");
    // py::object serialize_lib = py::module::import("agentscope.serialize");
    string final_result = _serialize(result_list).cast<string>();
    logger("call_get_agent_list 2: result = [" + final_result + "]");
    return final_result;
}

void Worker::get_agent_list_worker(const int call_id)
{
    py::gil_scoped_acquire acquire;
    // vector<string> agent_str_list;
    AgentListReturn result;
    {
        shared_lock<shared_mutex> lock(_agent_pool_mutex);
        for (auto &iter : _agent_pool)
        {
            // agent_str_list.push_back(iter.second.attr("__str__")().cast<string>());
            result.add_agent_str_list(iter.second.attr("__str__")().cast<string>());
        }
    }
    // string result = py::module::import("json").attr("dumps")(agent_str_list).cast<string>();
    // py::object serialize_lib = py::module::import("agentscope.serialize");
    // string result = serialize_lib.attr("serialize")(agent_str_list).cast<string>();
    // set_result(call_id, result.substr(1, result.size() - 2));
    set_result(call_id, result.SerializeAsString());
}

string Worker::call_set_model_configs(const string &model_configs)
{
    vector<int> call_id_list;
    ModelConfigsArgs args;
    args.set_model_configs(model_configs);
    for (auto i = 0u; i < _num_workers; i++)
    {
        int call_id = call_worker_func(i, function_ids::set_model_configs, &args);
        call_id_list.push_back(call_id);
    }
    string final_result;
    for (auto call_id : call_id_list)
    {
        string result = get_result(call_id);
        final_result += result;
    }
    return final_result;
}

void Worker::set_model_configs_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    ModelConfigsArgs args;
    args.ParseFromString(args_repr);
    string model_configs_str = args.model_configs();
    py::gil_scoped_acquire acquire;
    py::object model_configs = py::module::import("json").attr("loads")(model_configs_str);
    py::module::import("agentscope.manager").attr("ModelManager").attr("get_instance")().attr("load_model_configs")(model_configs);
    set_result(call_id, "");
}

pair<bool, string> Worker::call_get_agent_memory(const string &agent_id)
{
    int worker_id = get_worker_id_by_agent_id(agent_id);
    if (worker_id == -1)
    {
        return make_pair(false, "Try to get memory of a non-existent agent [" + agent_id + "].");
    }
    AgentArgs args;
    args.set_agent_id(agent_id);
    int call_id = call_worker_func(worker_id, function_ids::get_agent_memory, &args);
    string result_str = get_result(call_id);
    MsgReturn result;
    result.ParseFromString(result_str);
    return make_pair(result.ok(), result.message());
}

void Worker::get_agent_memory_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    AgentArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();
    py::gil_scoped_acquire acquire;
    shared_lock<shared_mutex> lock(_agent_pool_mutex);
    py::object agent = _agent_pool[agent_id];
    py::object memory = agent.attr("memory");
    MsgReturn result;
    if (memory.is_none())
    {
        // set_result(call_id, "FAgent [" + agent_id + "] has no memory.");
        result.set_ok(false);
        result.set_message("Agent [" + agent_id + "] has no memory.");
    }
    else
    {
        py::object memory_info = memory.attr("get_memory")();
        // py::object serialize_lib = py::module::import("agentscope.serialize");
        string memory_msg = _serialize(memory_info).cast<string>();
        result.set_ok(true);
        result.set_message(memory_msg);
        // set_result(call_id, "T" + py::module::import("json").attr("dumps")(memory_info).cast<string>());
    }
    set_result(call_id, result.SerializeAsString());
}

pair<bool, string> Worker::call_reply(const string &agent_id, const string &message)
{
    int worker_id = get_worker_id_by_agent_id(agent_id);
    if (worker_id == -1)
    {
        return make_pair(false, "Try to reply a non-existent agent [" + agent_id + "].");
    }
    logger("call_reply 1: agent_id = " + agent_id + " worker_id = " + to_string(worker_id));
    auto [task_id, callback_id] = get_task_id_and_callback_id();
    ReplyArgs args;
    args.set_agent_id(agent_id);
    args.set_message(message);
    args.set_task_id(task_id);
    args.set_callback_id(callback_id);
    logger("call_reply 2: agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " before call_worker_func");
    int call_id = call_worker_func(worker_id, function_ids::reply, &args);
    logger("call_reply 3: agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " call_id = " + to_string(call_id) + " wait result");
    string result = get_result(call_id);
    logger("call_reply 4: agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " call_id = " + to_string(call_id) + " result = " + result);
    return make_pair(true, result);
}

void Worker::reply_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    logger("reply_worker 1: call_id = " + to_string(call_id) + " args_repr = " + args_repr);
    ReplyArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();
    string message = args.message();
    int task_id = args.task_id();
    int callback_id = args.callback_id();
    logger("reply_worker 2: call_id = " + to_string(call_id) + " agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " message = " + message);

    py::gil_scoped_acquire acquire;
    shared_lock<shared_mutex> lock(_agent_pool_mutex);
    py::object agent = _agent_pool[agent_id];
    py::object message_lib = py::module::import("agentscope.message");
    // py::object serialize_lib = py::module::import("agentscope.serialize");
    py::object py_message = message.size() ? _deserialize(message) : py::none();

    string msg_str = to_string(task_id);
    logger("reply_worker 3: call_id = " + to_string(call_id) + " agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " msg_str = " + msg_str);
    set_result(call_id, msg_str);

    // working
    py::object PlaceholderMessage_class = message_lib.attr("PlaceholderMessage");
    if (py::isinstance(py_message, PlaceholderMessage_class))
    {
        py_message.attr("update_value")();
    }
    MsgReturn result;
    try
    {
        logger("reply_worker 3.1: call_id = " + to_string(call_id) + " agent_id = " + agent_id + " task_id = " + to_string(task_id) + " callback_id = " + to_string(callback_id) + " call reply");
        result.set_ok(true);
        py::object reply_msg = agent.attr("reply")(py_message);
        result.set_message(_serialize(reply_msg).cast<string>());
    }
    catch (const std::exception &e)
    {
        result.set_ok(false);
        result.set_message(e.what());
    }
    string reply_str = result.SerializeAsString();
    logger("reply_worker 4: call_id = " + to_string(call_id) + " agent_id=" + agent_id + ", task_id=" + to_string(task_id) + ", callback_id=" + to_string(callback_id) + " reply_str = " + reply_str);
    set_result(callback_id, reply_str);
}

pair<bool, string> Worker::call_observe(const string &agent_id, const string &message)
{
    int worker_id = get_worker_id_by_agent_id(agent_id);
    if (worker_id == -1)
    {
        return make_pair(false, "Try to observe a non-existent agent [" + agent_id + "].");
    }
    ObserveArgs args;
    args.set_agent_id(agent_id);
    args.set_message(message);
    int call_id = call_worker_func(worker_id, function_ids::observe, &args);
    string result = get_result(call_id);
    logger("call_observe 2: call_id = " + to_string(call_id) + " result = " + result);
    return make_pair(true, result);
}

void Worker::observe_worker(const int call_id)
{
    string args_repr = get_args_repr(call_id);
    ObserveArgs args;
    args.ParseFromString(args_repr);
    string agent_id = args.agent_id();
    string message = args.message();
    py::gil_scoped_acquire acquire;
    shared_lock<shared_mutex> lock(_agent_pool_mutex);
    py::object agent = _agent_pool[agent_id];
    py::object message_lib = py::module::import("agentscope.message");
    py::object PlaceholderMessage_class = message_lib.attr("PlaceholderMessage");
    // py::object serialize_lib = py::module::import("agentscope.serialize");
    logger("observe_worker 1: call_id = " + to_string(call_id) + " message = " + message);
    py::object py_messages = message.size() ? _deserialize(message) : py::list();
    // if (py::isinstance(py_messages, py::list()))
    // {
    //     py_messages.attr("update_value")();
    // }
    if (py::isinstance<py::list>(py_messages))
    {
        for (auto &py_message : py_messages)
        {
            if (py::isinstance(py_message, PlaceholderMessage_class))
            {
                py_message.attr("update_value")();
            }
        }
    }
    else
    {
        if (py::isinstance(py_messages, PlaceholderMessage_class))
        {
            py_messages.attr("update_value")();
        }
    }
    py::print("observe_worker: py_messages = ", py_messages);
    agent.attr("observe")(py_messages);
    set_result(call_id, "");
}

pair<bool, string> Worker::call_update_placeholder(const int task_id)
{
    auto [is_valid, result] = get_task_result(task_id);
    if (!is_valid)
    {
        if (result.empty())
        {
            return make_pair(false, "Task [" + to_string(task_id) + "] not exists.");
        }
        else
        {
            return make_pair(false, result);
        }
    }
    logger("call_update_placeholder 2: result = [" + result + "]");
    return make_pair(true, result);
}

string Worker::call_server_info()
{
    int worker_id = find_avail_worker_id();
    int call_id = call_worker_func(worker_id, function_ids::server_info, nullptr, false);
    string result = get_result(call_id);
    return result;
}

void Worker::server_info_worker(const int call_id)
{
    py::gil_scoped_acquire acquire;
    py::object process = py::module::import("psutil").attr("Process")(_main_worker_pid);
    double cpu_info = process.attr("cpu_percent")("interval"_a = 1).cast<double>();
    double mem_info = process.attr("memory_info")().attr("rss").cast<double>() / (1 << 20);
    py::dict result("pid"_a = _main_worker_pid, "id"_a = _server_id, "cpu"_a = cpu_info, "mem"_a = mem_info);
    string result_str = py::module::import("json").attr("dumps")(result).cast<string>();
    set_result(call_id, result_str);
}