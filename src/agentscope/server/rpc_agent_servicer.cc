#include <iostream>
#include <fstream>
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

#include <grpc/grpc.h>
#include <grpcpp/security/server_credentials.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>

#include "rpc_agent.grpc.pb.h"

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

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerReader;
using grpc::ServerReaderWriter;
using grpc::ServerWriter;
using grpc::Status;

using google::protobuf::Empty;

// using rpc_agent::AgentStatus;
// using rpc_agent::ByteMsg;
// using rpc_agent::CreateAgentRequest;
// using rpc_agent::GeneralResponse;
// using rpc_agent::RpcAgent;
// using rpc_agent::RpcMsg;
// using rpc_agent::StringMsg;
// using rpc_agent::UpdatePlaceholderRequest;

namespace py = pybind11;

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
            py::scoped_interpreter guard{};
            // std::cout << "run task 1.51: " << this->_task_id << std::endl;
            // py::print("???????????");
            py::gil_scoped_release release;
            // std::cout << "run task 1.52: " << this->_task_id << std::endl;
            // auto test = py::module::import("json");
            // std::cout << "run task 1.55: " << this->_task_id << std::endl;
            // auto agentscope = py::module::import("agentscope");
            // // std::cout << "run task 1.6: " << this->_task_id << std::endl;
            // auto message = agentscope.attr("message");
            // // std::cout << "run task 1.7: " << this->_task_id << std::endl;
            // auto PlaceholderMessage_class = message.attr("PlaceholderMessage");
            auto PlaceholderMessage_class = py::module::import("agentscope").attr("message").attr("PlaceholderMessage");
            // std::cout << "run task 2: " << this->_task_id << std::endl;
            if (py::isinstance(task_msg, PlaceholderMessage_class))
            {
                task_msg.attr("update_value")();
            }
            // std::cout << "run task 3: " << this->_task_id << std::endl;
            try
            {
                _task_result = agent.attr("reply")(task_msg).attr("serialize")();
            }
            catch (const std::exception &e)
            {
                // std::cerr << e.what() << '\n';
                auto AgentError_class = py::module::import("agentscope").attr("server").attr("servicer").attr("_AgentError");
                _task_result = AgentError_class(agent_id, e.what()).attr("err_msg");
            }
            // std::cout << "run task 4: " << this->_task_id << std::endl;
            this->_task_finished = true;
            this->_task_cv.notify_all(); });
        _task_executor.join();
    }
};

class RpcAgentServiceImpl final : public RpcAgent::Service
{
private:
    unordered_map<string, py::object> _agent_pool;
    unordered_map<string, unique_ptr<mutex>> _agent_pool_lock;
    shared_mutex _agent_pool_mutex;
    vector<unique_ptr<Task>> _task_list;
    py::object _model_configs;
    // py::scoped_interpreter guard{};

public:
    string _host;
    int _port;
    string _server_id;
    string _studio_url;
    int _max_pool_size;
    int _max_timeout_seconds;
    RpcAgentServiceImpl(
        string host = "localhost",
        int port = 10086,
        string server_id = "",
        string studio_url = "",
        int max_pool_size = 8192,
        int max_timeout_seconds = 1800) : _model_configs(py::none()), _host(host), _port(port), _server_id(server_id), _studio_url(studio_url), _max_pool_size(max_pool_size), _max_timeout_seconds(max_timeout_seconds)
    {
        // this->_host = host;
        // this->_port = port;
        // this->_server_id = server_id;
        // this->_studio_url = studio_url;
        // this->_max_pool_size = max_pool_size;
        // this->_max_timeout_seconds = max_timeout_seconds;
        // TODO: Add studio url to studio server;
    }

    // ~RpcAgentServiceImpl()
    // {
    // }

    // check server is alive
    Status is_alive(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        response->set_ok(true);
        return Status::OK;
    }

    // stop the server
    Status stop(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        // TODO: Add stop event;
        return Status::OK;
    }

    auto get_agent(string agent_id)
    {
        shared_lock<shared_mutex> lock(_agent_pool_mutex);
        return this->_agent_pool.find(agent_id);
    }

    py::tuple _create_agent(string agent_id, string agent_init_args, string agent_source_code)
    {
        // py::scoped_interpreter guard{};
        // py::gil_scoped_acquire acquire;
        if (!this->_model_configs.is_none())
        {
            py::module::import("agentscope").attr("models").attr("read_model_configs")(this->_model_configs);
        }
        py::tuple res = py::module::import("agentscope").attr("server").attr("servicer").attr("create_agent")(agent_id, py::bytes(agent_init_args), py::bytes(agent_source_code));
        py::print(res[0]);
        py::print(res[1]);
        // py::gil_scoped_release release;
        return res;
    }

    // create a new agent on the server
    Status create_agent(
        ServerContext *context,
        const CreateAgentRequest *request,
        GeneralResponse *response) override
    {
        string agent_id = request->agent_id();
        std::cout << "Create agent: " << agent_id << std::endl;
        {
            shared_lock<shared_mutex> lock(_agent_pool_mutex);
            if (this->_agent_pool.find(agent_id) != this->_agent_pool.end())
            {
                response->set_ok(false);
                response->set_message("Agent with agent_id [" + agent_id + "] already exists.");
                return Status::OK;
            }
        }
        string agent_init_args = request->agent_init_args();
        string agent_source_code = request->agent_source_code();
        // py::tuple create_result = _create_agent(agent_id, agent_init_args, agent_source_code);
        // py::tuple create_result = [&]()
        // {
        //     py::scoped_interpreter guard{};
        //     // py::gil_scoped_release release;
        //     if (!this->_model_configs.is_none())
        //     {
        //         py::module::import("agentscope").attr("models").attr("read_model_configs")(this->_model_configs);
        //     }
        //     py::tuple res = py::module::import("agentscope").attr("server").attr("servicer").attr("create_agent")(agent_id, py::bytes(agent_init_args), py::bytes(agent_source_code));
        //     py::print(res[0]);
        //     py::print(res[1]);
        //     return res;
        // }();
        py::scoped_interpreter guard{};
        // // py::gil_scoped_release release;
        if (!this->_model_configs.is_none())
        {
            py::module::import("agentscope").attr("models").attr("read_model_configs")(this->_model_configs);
        }
        std::cout << "Create agent 13: " << std::endl;
        try{
            std::cout << "Create agent 1: " << std::endl;
            auto t = py::module::import("agentscope");
            py::print(t);
        }
        catch(const std::exception &e)
        {
            std::cerr << e.what() << '\n';
        }
        py::tuple create_result = py::module::import("agentscope").attr("server").attr("servicer").attr("create_agent")(agent_id, py::bytes(agent_init_args), py::bytes(agent_source_code));
        py::object agent = create_result[0];
        py::object error_msg = create_result[1];
        if (error_msg.is_none())
        {
            unique_lock<shared_mutex> lock(_agent_pool_mutex);
            this->_agent_pool[agent_id] = agent;
            auto new_mutex = std::make_unique<mutex>();
            this->_agent_pool_lock.insert(std::make_pair(agent_id, std::move(new_mutex)));
            response->set_ok(true);
            // response->set_message("");
            // std::cout << "Create agent 14: " << std::endl;
        }
        else
        {
            response->set_ok(false);
            response->set_message(error_msg.cast<string>());
        }
        // std::cout << "Create agent 15: " << std::endl;
        // response->set_ok(true);
        return Status::OK;
    }
    // delete agent from the server
    Status delete_agent(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            // return py::make_tuple(false, "Try to delete a non-existent agent [{agent_id}].");
            response->set_ok(false);
            response->set_message("Try to delete a non-existent agent [" + agent_id + "].");
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
            // return py::make_tuple(true, "");
            response->set_ok(true);
        }
        return Status::OK;
    }

    // clear all agent on the server
    Status delete_all_agents(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        unique_lock<shared_mutex> lock(_agent_pool_mutex);
        py::scoped_interpreter guard{};
        for (auto iter : this->_agent_pool)
        {
            if (py::hasattr(iter.second, "__del__"))
            {
                iter.second.attr("__del__")();
            }
        }
        this->_agent_pool.clear();
        this->_agent_pool_lock.clear();
        return Status::OK;
    }

    // clone an agent with specific agent_id
    Status clone_agent(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        py::scoped_interpreter guard{};
        std::cout << "Clone agent: " << agent_id << std::endl;
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            // return py::make_tuple(false, "Try to clone a non-existent agent [{agent_id}].");
            response->set_ok(false);
            response->set_message("Try to clone a non-existent agent [" + agent_id + "].");
        }
        else
        {
            unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
            std::cout << "Clone agent 2: " << agent_id << std::endl;
            // try{
            //     py::object clone_agent = py::module::import("agentscope").attr("server").attr("servicer").attr("clone_agent")(iter->second);
            //     // py::object t = cl();
            //     // py::print(t);
            // }catch (const std::exception& e) {
            //     std::cerr << "Exception: " << e.what() << "\n";
            // }
            std::cout << "Clone agent 3: " << agent_id << std::endl;
            py::print(iter->second.attr("_init_settings")["args"]);
            py::print(iter->second.attr("_init_settings")["kwargs"]);
            auto cl = iter->second.attr("__class__");
            py::print(cl);
            auto t1 = py::module::import("agentscope");
            py::print(t1);
            try{
                auto t1 = py::module::import("agentscope");
                py::print(t1);
                auto func = py::module::import("agentscope").attr("server").attr("servicer").attr("clone_agent");
                py::print(func);
                py::object clone_agent = func(iter->second);
                // py::object t = cl();
                // py::print(t);
            }catch (const std::exception& e) {
                std::cerr << "Exception: " << e.what() << "\n";
            }
            py::object clone_agent = py::module::import("agentscope").attr("server").attr("servicer").attr("clone_agent")(iter->second);

            // // py::object sys = py::module::import("sys"); // 导入sys模块
            // // py::object version = sys.attr("version_info"); // 获取sys模块的version_info属性
            // // std::cout << "Python 版本信息: ";
            
            // // // 打印版本号
            // // for (auto v : py::cast<py::tuple>(version)) {
            // //     std::cout << v.cast<int>() << ".";
            // // }
            // // std::cout << std::endl;
            // py::exec(R"(
            //     print('super' in globals())
            //     print(super)
            // )");
            // try{
            //     py::object t = cl();
            //     py::print(t);
            // }catch (const std::exception& e) {
            //     std::cerr << "Exception: " << e.what() << "\n";
            // }
            // std::cout << "Clone agent 3.1: " << agent_id << std::endl;
            // py::object clone_agent = iter->second.attr("__class__")(
            //     *(iter->second.attr("_init_settings")["args"]),
            //     **(iter->second.attr("_init_settings")["kwargs"]));
            std::cout << "Clone agent 3.2: " << agent_id << std::endl;
            agent_lock.unlock();
            unique_lock<shared_mutex> lock(_agent_pool_mutex);
            std::cout << "Clone agent 3.3: " << agent_id << std::endl;
            string clone_agent_id = clone_agent.attr("agent_id").cast<string>();
            std::cout << "Clone agent 3.5: " << agent_id << std::endl;
            this->_agent_pool[clone_agent_id] = clone_agent;
            this->_agent_pool_lock.insert(std::make_pair(clone_agent_id, std::make_unique<mutex>()));
            std::cout << "Clone agent 4: " << agent_id << std::endl;
            // return py::make_tuple(true, clone_agent_id);
            response->set_ok(true);
            response->set_message(clone_agent_id);
        }
        // catch (const std::exception& e) {
        //     std::cerr << "Exception: " << e.what() << "\n";
        // }
        std::cout << "Clone agent 5: " << agent_id << std::endl;
        return Status::OK;
    }

    // get id of all agents on the server as a list
    Status get_agent_list(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        py::scoped_interpreter guard{};
        // py::gil_scoped_release release;
        vector<string> agent_list;
        {
            shared_lock<shared_mutex> lock(_agent_pool_mutex);
            for (auto iter : _agent_pool)
            {
                unique_lock<mutex> agent_lock(*_agent_pool_lock[iter.first]);
                agent_list.push_back(iter.second.attr("__str__")().cast<string>());
            }
        }
        // string msg = py::module::import("agentscope").attr("server").attr("servicer").attr("get_agents_info")(agent_list).cast<string>();
        string msg = py::module::import("json").attr("dumps")(agent_list).cast<string>();
        response->set_ok(true);
        response->set_message(msg);
        return Status::OK;
    }

    // get the resource utilization information of the server
    Status get_server_info(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        return Status::OK;
    }

    // update the model configs in the server
    Status set_model_configs(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        py::scoped_interpreter guard{};
        _model_configs = py::module::import("json").attr("loads")(request->value());
        return Status::OK;
    }

    // get memory of a specific agent
    Status get_agent_memory(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        auto iter = this->get_agent(agent_id);
        if (iter == this->_agent_pool.end())
        {
            // return py::make_tuple(false, "Try to get memory of a non-existent agent [{agent_id}].");
            response->set_ok(false);
            response->set_message("Try to get memory of a non-existent agent [" + agent_id + "].");
        }
        else
        {
            unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
            py::scoped_interpreter guard{};
            py::object memory = iter->second.attr("memory");
            if (memory.is_none())
            {
                // return py::make_tuple(false, "Agent [{agent_id}] has no memory.");
                response->set_ok(false);
                response->set_message("Agent [" + agent_id + "] has no memory.");
            }
            else
            {
                // return py::make_tuple(true, memory.attr("get_memory")());
                response->set_ok(true);
                py::object memory_info = memory.attr("get_memory")();
                response->set_message(py::module::import("json").attr("dumps")(memory_info).cast<string>());
            }
        }
        return Status::OK;
    }

    // call funcs of agent running on the server
    Status call_agent_func(
        ServerContext *context,
        const RpcMsg *request,
        GeneralResponse *response) override
    {
        auto agent_id = request->agent_id();
        auto target_func = request->target_func();
        auto agent = this->get_agent(agent_id);
        if (agent == this->_agent_pool.end())
        {
            // // return py::make_tuple(false, "Try to call a non-existent agent [{agent_id}].");
            // response->set_ok(false);
            // response->set_message("Try to call a non-existent agent [" + agent_id + "].");
            // context->TryCancel();
            return Status(grpc::StatusCode::INVALID_ARGUMENT, "Agent [" + agent_id + "] not exists.");
        }
        else
        {
            if (target_func == "_reply")
            {
                return this->_reply(request, response);
            }
            else if (target_func == "_observe")
            {
                return this->_observe(request, response);
            }
            else
            {
                return Status(grpc::StatusCode::INVALID_ARGUMENT, "Unsupported method " + target_func + ".");
            }
        }
        return Status::OK;
    }

    Status _reply(const RpcMsg *request, GeneralResponse *response) // string agent_id, py::object message)
    {
        string agent_id = request->agent_id();
        py::scoped_interpreter guard{};
        py::object message = request->value().size() ? py::module::import("agentscope").attr("message").attr("deserialize")(request->value()) : py::none();
        // py::object message = [&]()
        // {
        //     py::scoped_interpreter guard{};
        //     return request->value().size() ? py::module::import("agentscope").attr("message").attr("deserialize")(request->value()) : py::none();
        // }();
        // std::cout << "reply 1: " << agent_id << std::endl;
        // py::print(message);
        auto iter = this->get_agent(agent_id);
        auto agent = iter->second;
        // std::cout << "reply 2: " << agent_id << std::endl;
        unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
        int task_id = _task_list.size();
        _task_list.emplace_back(std::make_unique<Task>(task_id));
        // std::cout << "reply 3: " << agent_id << std::endl;
        _task_list[task_id]->run(agent_id, agent, message);
        // std::cout << "reply 4: " << agent_id << std::endl;
        // return py::make_tuple(agent, task_id);
        response->set_ok(true);
        // response->set_message(py::module::import("json").attr("dumps")(task_id).cast<string>());
        {
            // py::scoped_interpreter guard{};
            response->set_message(py::module::import("agentscope").attr("message").attr("Msg")(agent.attr("name")(), py::none(), task_id).attr("serialize")().cast<string>());
        }
        return Status::OK;
    }

    Status _observe(const RpcMsg *request, GeneralResponse *response) // string agent_id, py::object messages)
    {
        string agent_id = request->agent_id();
        py::object messages = [&]()
        {
            py::scoped_interpreter guard{};
            py::list messages = py::module::import("agentscope").attr("message").attr("deserialize")(request->value());
            py::object PlaceholderMessage_class = py::module::import("agentscope").attr("message").attr("PlaceholderMessage");
            for (auto message : messages)
            {
                if (py::isinstance(message, PlaceholderMessage_class))
                {
                    message.attr("update_value")();
                }
            }
            return messages;
        }();
        // py::scoped_interpreter guard{};
        // py::gil_scoped_release release;
        auto iter = this->get_agent(agent_id);
        auto agent = iter->second;
        unique_lock<mutex> agent_lock(*_agent_pool_lock[agent_id]);
        {
            py::scoped_interpreter guard{};
            agent.attr("observe")(messages);
        }
        response->set_ok(true);
        return Status::OK;
    }

    // update value of PlaceholderMessage
    Status update_placeholder(
        ServerContext *context,
        const UpdatePlaceholderRequest *request,
        GeneralResponse *response) override
    {
        auto task_id = request->task_id();
        if (task_id >= this->_task_list.size())
        {
            // return py::none();
            response->set_ok(false);
            response->set_message("Task [" + std::to_string(task_id) + "] not exists.");
            return Status::OK;
        }
        // return this->_task_list[task_id]->get_result();
        response->set_ok(true);
        response->set_message(this->_task_list[task_id]->get_result().cast<string>());
        return Status::OK;
    }

    // file transfer
    Status download_file(
        ServerContext *context,
        const StringMsg *request,
        ServerWriter<ByteMsg> *writer) override
    {
        std::string filepath = request->value();
        if (!std::filesystem::exists(filepath))
        {
            return Status(grpc::StatusCode::NOT_FOUND, string("File ") + filepath + " not found");
        }

        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open())
        {
            return Status(grpc::StatusCode::INTERNAL, "Failed to open the file");
        }

        char buffer[1024 * 1024]; // 1MB buffer
        while (file.read(buffer, sizeof(buffer)))
        {
            ByteMsg piece;
            piece.set_data(std::string(buffer, file.gcount()));
            if (!writer->Write(piece))
            {
                // 如果发送失败（例如，客户端断开连接）
                return Status(grpc::StatusCode::ABORTED, "Failed to send data to client");
            }
        }

        // 发送完成，检查是否成功
        if (file.eof())
        {
            return Status::OK;
        }
        else if (file.fail())
        {
            return Status(grpc::StatusCode::INTERNAL, "Error occurred while reading the file");
        }

        return Status::OK;
    }
};

void RunServer()
{
    std::string server_address("0.0.0.0:50051");
    // py::scoped_interpreter guard{};
    RpcAgentServiceImpl service;

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;
    server->Wait();
}

int main(int argc, char **argv)
{
    RunServer();
    return 0;
}
