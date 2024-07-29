#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <utility>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <condition_variable>
#include <chrono>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/embed.h>

using std::pair;
using std::string;
using std::unordered_map;
using std::vector;

using std::condition_variable;
// using std::lock_guard;
using std::mutex;
using std::shared_lock;
using std::shared_mutex;
using std::thread;
using std::unique_lock;
using std::unique_ptr;
// using namespace std::chrono;

using namespace pybind11::literals;

namespace py = pybind11;

// g++ -O3 -Wall -shared -std=c++17 -L/opt/anaconda3/lib -fPIC -undefined dynamic_lookup $(python3 -m pybind11 --includes) -ldl cpp_agent_servicer.cc -o cpp_agent_servicer$(python3-config --extension-suffix)

class Task
{
private:
    int _task_id;
    mutex _task_mutex;
    condition_variable _task_cv;
    thread _task_executor;
    py::object _task_result;
    bool _task_finished;

public:
    Task(int task_id) : _task_id(task_id), _task_mutex(), _task_finished(false)
    {
    }

    int get_task_id()
    {
        return this->_task_id;
    }
    py::object get_result()
    {
        unique_lock<mutex> lock(_task_mutex);
        _task_cv.wait(lock, [this]()
                      { return this->_task_finished; });
        // py::print(_task_result);
        return _task_result;
    }
    void run(string agent_id, py::object &agent, py::object &task_msg)
    {
        assert(_task_finished == false);
        // py::scoped_interpreter guard{};
        // py::gil_scoped_release release;
        _task_executor = thread([this, agent_id, agent, task_msg]()
        {
            // std::cout << "run task 1: " << this->_task_id << std::endl;
            unique_lock<mutex> lock(_task_mutex);
            // std::cout << "run task 1.5: " << this->_task_id << std::endl;
            // py::gil_scoped_acquire acquire;
            // py::scoped_interpreter guard{};
            // std::cout << "run task 1.51: " << this->_task_id << std::endl;
            // py::print("???????????");
            // py::gil_scoped_release release;
            // std::cout << "run task 1.52: " << this->_task_id << std::endl;
            // auto test = py::module::import("json");
            // std::cout << "run task 1.55: " << this->_task_id << std::endl;
            auto agentscope = py::module::import("agentscope");
            // std::cout << "run task 1.6: " << this->_task_id << std::endl;
            auto message = agentscope.attr("message");
            // std::cout << "run task 1.7: " << this->_task_id << std::endl;
            auto PlaceholderMessage_class = message.attr("PlaceholderMessage");
            // auto PlaceholderMessage_class = py::module::import("agentscope").attr("message").attr("PlaceholderMessage");
            // std::cout << "run task 2: " << this->_task_id << std::endl;
            if (py::isinstance(task_msg, PlaceholderMessage_class))
            {
                task_msg.attr("update_value")();
            }
            // std::cout << "run task 3: " << this->_task_id << std::endl;
            try
            {
                _task_result = agent.attr("reply")(task_msg);
            }
            catch (const std::exception &e)
            {
                // std::cerr << e.what() << '\n';
                auto AgentError_class = py::module::import("agentscope").attr("server").attr("servicer").attr("_AgentError");
                _task_result = AgentError_class(agent_id, e.what());
            }
            // std::cout << "run task 4: " << this->_task_id << std::endl;
            this->_task_finished = true;
            this->_task_cv.notify_all();
        } );
        _task_executor.join();
    }
};

class AgentServicer
{
private:
    unordered_map<string, py::object> _agent_pool;
    unordered_map<string, unique_ptr<mutex>> _agent_pool_lock;
    shared_mutex _agent_pool_mutex;
    // int _task_id_counter;
    // mutex _task_id_counter_mutex;
    // unordered_map<int, unique_ptr<mutex>> _task_mutex;
    // unordered_map<int, unique_ptr<condition_variable>> _task_cv;
    // unordered_map<int, thread> _task_executors;
    // // unordered_map<int, pair<py::object, std::chrono::system_clock::time_point>> _task_results;
    // unordered_map<int, py::object> _task_results;
    vector<unique_ptr<Task>> _task_list;

public:
    int _max_pool_size;
    int _max_timeout_seconds;
    AgentServicer(
        int max_pool_size = 8192,
        int max_timeout_seconds = 1800)
    {
        this->_max_pool_size = max_pool_size;
        this->_max_timeout_seconds = max_timeout_seconds;
    }

    auto get_agent(string agent_id)
    {
        shared_lock<shared_mutex> lock(_agent_pool_mutex);
        return this->_agent_pool.find(agent_id);
    }

    bool agent_exists(string agent_id)
    {
        shared_lock<shared_mutex> lock(_agent_pool_mutex);
        return this->_agent_pool.find(agent_id) != this->_agent_pool.end();
    }

    // create a new agent on the server
    py::tuple create_agent(
        string agent_id,
        py::object agent_init_args,
        py::object agent_source_code)
    {
        // string agent_id = request->agent_id();
        // TODO: add lock
        {
            shared_lock<shared_mutex> lock(_agent_pool_mutex);
            if (this->_agent_pool.find(agent_id) != this->_agent_pool.end())
            {
                return py::make_tuple(false, "Agent with agent_id [{agent_id}] already exists");
            }
        }
        std::cout << "create_agent: " << agent_id << std::endl;
        py::tuple create_result = py::module::import("agentscope").attr("server").attr("servicer").attr("create_agent")(agent_id, agent_init_args, agent_source_code);
        // std::cout << "created! " << create_result.attr("__len__").cast<int>() << std::endl;
        std::cout << "created! " << std::endl;
        py::print(create_result);
        py::object agent = create_result[0];
        py::object error_msg = create_result[1];
        if (error_msg.is_none())
        {
            unique_lock<shared_mutex> lock(_agent_pool_mutex);
            this->_agent_pool[agent_id] = agent;
            auto new_mutex = std::make_unique<mutex>();
            this->_agent_pool_lock.insert(std::make_pair(agent_id, std::move(new_mutex)));
        }
        return py::make_tuple(error_msg.is_none(), error_msg);
    }
    // delete agent from the server
    py::tuple delete_agent(string agent_id)
    {
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            return py::make_tuple(false, "Try to delete a non-existent agent [{agent_id}].");
        }
        else
        {
            unique_lock<shared_mutex> lock(_agent_pool_mutex);
            if (py::hasattr(iter->second, "__del__"))
            {
                iter->second.attr("__del__")();
            }
            this->_agent_pool.erase(iter);
            auto mutex_iter = this->_agent_pool_lock.find(agent_id);
            this->_agent_pool_lock.erase(mutex_iter);
            return py::make_tuple(true, "");
        }
    }

    // clear all agent on the server
    py::tuple delete_all_agents()
    {
        unique_lock<shared_mutex> lock(_agent_pool_mutex);
        for (auto iter : this->_agent_pool)
        {
            if (py::hasattr(iter.second, "__del__"))
            {
                iter.second.attr("__del__")();
            }
        }
        this->_agent_pool.clear();
        this->_agent_pool_lock.clear();
        return py::make_tuple(true, "");
    }

    // clone an agent with specific agent_id
    py::tuple clone_agent(string agent_id)
    {
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            return py::make_tuple(false, "Try to clone a non-existent agent [{agent_id}].");
        }
        else
        {
            unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
            py::object clone_agent = iter->second.attr("__class__")(
                *(iter->second.attr("_init_settings")["args"]),
                **(iter->second.attr("_init_settings")["kwargs"]));
            agent_lock.unlock();
            unique_lock<shared_mutex> lock(_agent_pool_mutex);
            string clone_agent_id = clone_agent.attr("agent_id").cast<string>();
            this->_agent_pool[clone_agent_id] = clone_agent;
            this->_agent_pool_lock.insert(std::make_pair(clone_agent_id, std::make_unique<mutex>()));
            return py::make_tuple(true, clone_agent_id);
        }
    }

    // get id of all agents on the server as a list
    vector<string> get_agent_list()
    {
        vector<string> agent_list;
        {
            shared_lock<shared_mutex> lock(_agent_pool_mutex);
            for (auto iter : _agent_pool)
            {
                unique_lock<mutex> agent_lock(*_agent_pool_lock[iter.first]);
                agent_list.push_back(iter.second.attr("__str__")().cast<string>());
            }
        }
        return agent_list;
    }

    // get memory of a specific agent
    py::tuple get_agent_memory(string agent_id)
    {
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            return py::make_tuple(false, "Try to get memory of a non-existent agent [{agent_id}].");
        }
        else
        {
            unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
            py::object memory = iter->second.attr("memory");
            if (memory.is_none())
            {
                return py::make_tuple(false, "Agent [{agent_id}] has no memory.");
            }
            else
            {
                return py::make_tuple(true, memory.attr("get_memory")());
            }
        }
    }

    // update value of PlaceholderMessage
    py::object update_placeholder(int task_id)
    {
        py::print("update_placeholder in cpp");
        if (task_id >= this->_task_list.size())
        {
            return py::none();
        }
        return this->_task_list[task_id]->get_result();
    }

    py::tuple _reply(string agent_id, py::object message)
    {
        std::cout << "reply 1: " << agent_id << std::endl;
        py::print(message);
        auto iter = this->get_agent(agent_id);
        auto agent = iter->second;
        std::cout << "reply 2: " << agent_id << std::endl;
        unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
        int task_id = _task_list.size();
        _task_list.emplace_back(std::make_unique<Task>(task_id));
        std::cout << "reply 3: " << agent_id << std::endl;
        _task_list[task_id]->run(agent_id, agent, message);
        std::cout << "reply 4: " << agent_id << std::endl;
        return py::make_tuple(agent, task_id);
    }

    void _observe(string agent_id, py::object messages)
    {
        auto iter = this->get_agent(agent_id);
        auto agent = iter->second;
        unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
        agent.attr("observe")(messages);
    }
};

PYBIND11_MODULE(cpp_agent_servicer, m)
{
    m.doc() = "cpp_agent_servicer";
    py::class_<AgentServicer>(m, "CPPAgentServicer")
        .def(py::init<int, int>())
        .def("agent_exists", &AgentServicer::agent_exists)
        .def("create_agent", &AgentServicer::create_agent)
        .def("delete_agent", &AgentServicer::delete_agent)
        .def("delete_all_agents", &AgentServicer::delete_all_agents)
        .def("clone_agent", &AgentServicer::clone_agent)
        .def("get_agent_list", &AgentServicer::get_agent_list)
        .def("get_agent_memory", &AgentServicer::get_agent_memory)
        .def("update_placeholder", &AgentServicer::update_placeholder)
        .def("_reply", &AgentServicer::_reply)
        .def("_observe", &AgentServicer::_observe);
}