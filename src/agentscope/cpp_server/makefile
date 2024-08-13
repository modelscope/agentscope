CXX = g++
CPPFLAGS += `pkg-config --cflags protobuf grpc`
CXXFLAGS += -std=c++17 -O3 -fPIC `python3 -m pybind11 --includes`
PY_LIB_PATH = `python3-config --prefix`/lib
LDFLAGS += -L/usr/local/lib `pkg-config --cflags --libs grpc++ grpc protobuf` -L$(PY_LIB_PATH) \
		   -lpython3.12 \
           -pthread\
           -lgrpc++_reflection\
           -ldl
PROTOC = protoc
GRPC_CPP_PLUGIN = grpc_cpp_plugin
GRPC_CPP_PLUGIN_PATH ?= `which $(GRPC_CPP_PLUGIN)`

PROTOS_PATH = ../rpc

vpath %.proto $(PROTOS_PATH)

all: install launch_server

install: rpc_agent.grpc.pb.cc rpc_agent.pb.cc worker_args.pb.cc rpc_agent_servicer

rpc_agent_servicer: rpc_agent.pb.o rpc_agent.grpc.pb.o worker_args.pb.o worker.o rpc_agent_servicer.o
	$(CXX) $^ $(CXXFLAGS) $(LDFLAGS) -o $@

worker.o: worker.cc worker.h
	$(CXX) -c $< $(CXXFLAGS) $(LDFLAGS) -o $@

launch_server:
	cd ../../../; DYLD_LIBRARY_PATH=$(PY_LIB_PATH):$$DYLD_LIBRARY_PATH OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES ./src/agentscope/cpp_server/rpc_agent_servicer $(INIT_SETTINGS_STR) $(HOST) $(PORT) $(SERVER_ID) $(CUSTOM_AGENT_CLASSES) $(STUDIO_URL) $(MAX_TASKS) $(TIMEOUT_SECONDS) $(NUM_WORKERS)

%.grpc.pb.cc: $(PROTOS_PATH)/%.proto
	$(PROTOC) -I $(PROTOS_PATH) --grpc_out=. --plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN_PATH) $<

%.pb.cc: $(PROTOS_PATH)/%.proto
	$(PROTOC) -I $(PROTOS_PATH) --cpp_out=. $<

clean:
	rm -f *.o *.so *.pb.cc *.pb.h rpc_agent_servicer
