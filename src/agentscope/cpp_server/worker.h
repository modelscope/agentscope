#ifndef WORKER_H
#define WORKER_H

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <utility>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <deque>
#include <queue>
#include <condition_variable>
#include <semaphore.h>
#include <sys/ipc.h>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/embed.h>

#include "worker_args.pb.h"

using std::deque;
using std::queue;
using std::make_pair;
using std::pair;
using std::string;
using std::unordered_map;
using std::vector;

using std::condition_variable;
using std::condition_variable_any;
using std::mutex;
using std::shared_lock;
using std::shared_mutex;
using std::thread;
using std::unique_lock;
using std::unique_ptr;

namespace py = pybind11;

using google::protobuf::Message;

class Task
{
public:
    int _task_id;
    mutex _task_mutex;
    condition_variable_any _task_cv;
    string _task_result;
    bool _task_finished;

    Task(const int task_id);
    int task_id();
    string get_result();
};

class Worker
{
private:
    const string _host;
    const string _port;
    const string _server_id;
    const int _main_worker_pid;
    const unsigned int _num_workers;
    int _worker_id;
    vector<pid_t> _worker_pids;

    const int _sem_num_per_sem_id;
    const unsigned int _call_shm_size;
    const unsigned int _max_call_id;
    const unsigned int _small_obj_size;
    const unsigned int _small_obj_shm_size;

    const string _call_worker_shm_name;
    const string _func_args_shm_prefix;
    const string _func_result_shm_prefix;
    const string _worker_avail_sem_prefix;
    const string _func_ready_sem_prefix;
    const string _small_obj_pool_shm_name;

    vector<int> _call_sem_ids;
    int _call_worker_shm_fd;
    char *_call_worker_shm;
    vector<pair<sem_t *, sem_t *>> _worker_semaphores;
    int _small_obj_pool_shm_fd;
    void *_small_obj_pool_shm;
    mutex _call_id_mutex;
    condition_variable _call_id_cv;
    queue<int> _call_id_pool;

    const bool _use_logger;
    mutex _logger_mutex;

    unordered_map<string, int> _agent_id_map; // map agent id to worker id
    shared_mutex _agent_id_map_mutex;
    unordered_map<string, py::object> _agent_pool;
    shared_mutex _agent_pool_mutex;

    deque<pair<long long, std::unique_ptr<Task>>> _tasks;
    int _num_tasks;
    shared_mutex _tasks_head_mutex;
    mutex _tasks_tail_mutex;
    const unsigned int _max_tasks;
    const unsigned int _max_timeout_seconds;

    // common used functions
    py::object _serialize, _deserialize;

    enum function_ids
    {
        create_agent = 0,
        delete_agent = 1,
        delete_all_agents = 2,
        clone_agent = 3,
        get_agent_list = 4,
        set_model_configs = 5,
        get_agent_memory = 6,
        reply = 7,
        observe = 8,
        server_info = 9,
    };

    int find_avail_worker_id();
    int get_call_id();
    string get_content(const string &prefix, const int call_id);
    void set_content(const string &prefix, const int call_id, const string &content);
    string get_args_repr(const int call_id);
    void set_args_repr(const int call_id, const string &args_repr);
    string get_result(const int call_id);
    void set_result(const int call_id, const string &result);
    int get_worker_id_by_agent_id(const string &agent_id);

    static const unsigned int _default_max_call_id = 10000;
    static unsigned int calc_max_call_id()
    {
        char *max_call_id = getenv("AGENTSCOPE_MAX_CALL_ID");
        if (max_call_id != nullptr)
        {
            try {
                return std::stoi(max_call_id);
            } catch (const std::invalid_argument&) {
                return _default_max_call_id;
            } catch (const std::out_of_range&) {
                return _default_max_call_id;
            }
        }
        else
        {
            return _default_max_call_id;
        }
    }
    static bool calc_use_logger()
    {
        char *use_logger = getenv("AGENTSCOPE_USE_CPP_LOGGER");
        if (use_logger != nullptr && std::string(use_logger) == "True")
        {
            return true;
        }
        else
        {
            return false;
        }
    }

    inline long long get_current_timestamp()
    {
        auto now = std::chrono::system_clock::now();
        auto duration = now.time_since_epoch();
        return std::chrono::duration_cast<std::chrono::seconds>(duration).count();
    }
    inline bool is_timeout(const long long timestamp)
    {
        return get_current_timestamp() - timestamp > _max_timeout_seconds;
    }
    pair<int, int> get_task_id_and_callback_id();
    pair<bool, string> get_task_result(const int task_id);
    int call_worker_func(const int worker_id, const function_ids func_id, const Message *args, const bool need_wait = true);

    void create_agent_worker(const int call_id);
    void delete_agent_worker(const int call_id);
    void delete_all_agents_worker(const int call_id);
    void clone_agent_worker(const int call_id);
    void get_agent_list_worker(const int call_id);
    void set_model_configs_worker(const int call_id);
    void get_agent_memory_worker(const int call_id);
    void reply_worker(const int call_id);
    void observe_worker(const int call_id);
    void server_info_worker(const int call_id);

public:
    Worker(
        const string &host,
        const string &port,
        const string &server_id,
        const string &studio_url,
        const unsigned int max_tasks,
        const unsigned int max_timeout_seconds,
        const unsigned int num_workers);
    ~Worker();

    void logger(const string &msg)
    {
        if (_use_logger)
        {
            unique_lock<std::mutex> lock(_logger_mutex);
            std::cout << "pid = " << getpid() << " tid = " << std::this_thread::get_id() << " " << msg << std::endl;
        }
    }

    string call_create_agent(const string &agent_id, const string &agent_init_args, const string &agent_source_code);
    string call_delete_agent(const string &agent_id);
    string call_delete_all_agents();
    pair<bool, string> call_clone_agent(const string &agent_id);
    string call_get_agent_list();
    string call_set_model_configs(const string &model_configs);
    pair<bool, string> call_get_agent_memory(const string &agent_id);
    pair<bool, string> call_reply(const string &agent_id, const string &message);
    pair<bool, string> call_observe(const string &agent_id, const string &message);
    pair<bool, string> call_update_placeholder(const int task_id);
    string call_server_info();
};

#endif
