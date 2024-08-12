#include <iostream>
#include <string>
#include <utility>
#include <csignal>

#include <grpc/grpc.h>
#include <grpcpp/security/server_credentials.h>
#include <grpcpp/server.h>
#include <grpcpp/server_builder.h>
#include <grpcpp/server_context.h>

#include "rpc_agent.grpc.pb.h"
#include "worker.h"

using std::pair;
using std::string;

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::ServerReader;
using grpc::ServerReaderWriter;
using grpc::ServerWriter;
using grpc::Status;

using google::protobuf::Empty;

Worker *worker = nullptr;

class RpcAgentServiceImpl final : public RpcAgent::Service
{
private:
    Worker *_worker;

public:
    RpcAgentServiceImpl(Worker *worker) : _worker(worker)
    {
    }

    ~RpcAgentServiceImpl()
    {
    }

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
        response->set_ok(true);
        return Status::OK;
    }

    // create a new agent on the server
    Status create_agent(
        ServerContext *context,
        const CreateAgentRequest *request,
        GeneralResponse *response) override
    {
        const string &agent_id = request->agent_id();
        const string &agent_init_args = request->agent_init_args();
        const string &agent_source_code = request->agent_source_code();
        const string &result = _worker->call_create_agent(agent_id, agent_init_args, agent_source_code);
        response->set_ok(result.empty());
        response->set_message(result);
        return Status::OK;
    }
    // delete agent from the server
    Status delete_agent(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        const string &result = _worker->call_delete_agent(agent_id);
        response->set_ok(result.size() == 0);
        response->set_message(result);
        return Status::OK;
    }

    // clear all agent on the server
    Status delete_all_agents(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        const string &result = _worker->call_delete_all_agents();
        response->set_ok(result.size() == 0);
        response->set_message(result);
        return Status::OK;
    }

    // clone an agent with specific agent_id
    Status clone_agent(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        auto [is_ok, result] = _worker->call_clone_agent(agent_id);
        response->set_ok(is_ok);
        response->set_message(result);
        return Status::OK;
    }

    // get id of all agents on the server as a list
    Status get_agent_list(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        const string &result = _worker->call_get_agent_list();
        response->set_ok(true);
        response->set_message(result);
        return Status::OK;
    }

    // get the resource utilization information of the server
    Status get_server_info(
        ServerContext *context,
        const Empty *request,
        GeneralResponse *response) override
    {
        const string &result = _worker->call_server_info();
        response->set_ok(true);
        response->set_message(result);
        return Status::OK;
    }

    // update the model configs in the server
    Status set_model_configs(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        const string &model_configs = request->value();
        std::cout << "set_model_configs: " << model_configs << std::endl;
        const string &result = _worker->call_set_model_configs(model_configs);
        response->set_ok(result.size() == 0);
        response->set_message(result);
        return Status::OK;
    }

    // get memory of a specific agent
    Status get_agent_memory(
        ServerContext *context,
        const StringMsg *request,
        GeneralResponse *response) override
    {
        string agent_id = request->value();
        auto [is_ok, result] = _worker->call_get_agent_memory(agent_id);
        response->set_ok(is_ok);
        response->set_message(result);
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
        auto message = request->value();
        pair<bool, string> result;
        if (target_func == "_reply")
        {
            result = _worker->call_reply(agent_id, message);
        }
        else if (target_func == "_observe")
        {
            result = _worker->call_observe(agent_id, message);
        }
        else
        {
            return Status(grpc::StatusCode::INVALID_ARGUMENT, "Unsupported method " + target_func + ".");
        }
        if (result.first)
        {
            response->set_ok(true);
            response->set_message(result.second);
        }
        else
        {
            return Status(grpc::StatusCode::INVALID_ARGUMENT, result.second);
        }
        return Status::OK;
    }

    // update value of PlaceholderMessage
    Status update_placeholder(
        ServerContext *context,
        const UpdatePlaceholderRequest *request,
        GeneralResponse *response) override
    {
        auto task_id = request->task_id();
        auto [is_ok, result] = _worker->call_update_placeholder(task_id);
        // bool is_ok = true;
        // string result = "{\"__type\": \"Msg\", \"id\": \"000b39a7472142339197cd3acaddf81b\", \"timestamp\": \"2024-08-12 00:58:51\", \"name\": \"File\", \"content\": \"Image\", \"role\": \"assistant\", \"url\": \"/Users/chenyushuo/workspace/agentscope/tests/data/image.png\", \"metadata\": null, \"_colored_name\": \"\\u001b[92mFile\\u001b[0m\"}";
        // string result = "{\"__type\": \"Msg\", \"name\": \"\", \"content\": \"\", \"url\": \"\"}";
        _worker->logger("rpc server update_placeholder 1: task_id = " + std::to_string(task_id) + " is_ok = " + std::to_string(is_ok) + " result = [" + result + "]");
        response->set_ok(is_ok);
        response->set_message(result);
        _worker->logger("rpc server update_placeholder 2: is_ok = " + std::to_string(is_ok) + " result = [" + result + "], result.size() = " + std::to_string(result.size()));
        return Status::OK;
    }

    // file transfer
    Status download_file(
        ServerContext *context,
        const StringMsg *request,
        ServerWriter<ByteMsg> *writer) override
    {
        _worker->logger("download_file: start!");
        std::string filepath = request->value();
        _worker->logger("download_file: filepath = " + filepath);
        if (!std::filesystem::exists(filepath))
        {
            return Status(grpc::StatusCode::NOT_FOUND, string("File ") + filepath + " not found");
        }

        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open())
        {
            return Status(grpc::StatusCode::NOT_FOUND, "Failed to open the file");
        }

        auto buffer = std::make_unique<char[]>(1024 * 1024);
        auto read_size = sizeof(char) * 1024 * 1024;
        _worker->logger("downloading sizeof(buffer) = " + std::to_string(sizeof(buffer)) + " read_size = " + std::to_string(read_size));
        while (true)
        {
            file.read(buffer.get(), read_size);
            if (!file && !file.eof())
            {
                file.close();
                return Status(grpc::StatusCode::INTERNAL, "Error occurred while reading the file");
            }
            ByteMsg piece;
            string data = std::string(buffer.get(), file.gcount());
            _worker->logger("download_file: read_size = " + std::to_string(read_size) + " file.gcount() = " + std::to_string(file.gcount()) + " data.size() = " + std::to_string(data.size()));
            piece.set_data(data);
            if (!writer->Write(piece))
            {
                file.close();
                return Status(grpc::StatusCode::ABORTED, "Failed to send data to client");
            }
            if (file.eof())
            {
                file.close();
                return Status::OK;
            }
        }
    }
};

void RunServer(const string &server_address)
{
    RpcAgentServiceImpl service(worker);

    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);

    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;
    server->Wait();
}

void signal_handler(int signum)
{
    if (worker != nullptr)
    {
        delete worker;
    }
    exit(0);
}

int main(int argc, char **argv)
{
    if (argc < 9)
    {
        std::cerr << "Usage: " << argv[0] << " <init_settings_str> <host> <port> <server_id> <custom_agent_classes_str> <studio_url> <max_tasks> <timeout_seconds> [<num_workers>] [<launcher_pid>]" << std::endl;
        return 1;
    }
    struct sigaction act;
    act.sa_handler = signal_handler;
    sigemptyset(&act.sa_mask);
    act.sa_flags = 0;
    sigaction(SIGINT, &act, NULL);
    sigaction(SIGKILL, &act, NULL);

    string init_settings_str = argv[1];
    string host = argv[2];
    string port = argv[3];
    std::string server_address(host + ":" + port);
    string server_id = argv[4];
    string custom_agent_classes_str = argv[5];
    string studio_url = argv[6];
    int max_tasks = std::atoi(argv[7]);
    int timeout_seconds = std::atoi(argv[8]);
    int num_workers = argc >= 10 ? std::atoi(argv[9]) : 2;
    int launcher_pid = argc >= 11 ? std::atoi(argv[10]) : 0;
    worker = new Worker(init_settings_str, host, port, server_id, custom_agent_classes_str, studio_url, max_tasks, timeout_seconds, num_workers, launcher_pid);
    RunServer(server_address);
    delete worker;
    return 0;
}
