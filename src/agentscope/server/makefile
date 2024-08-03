HOST_SYSTEM = $(shell uname | cut -f 1 -d_)
SYSTEM ?= $(HOST_SYSTEM)
CXX = g++
CPPFLAGS += `pkg-config --cflags protobuf grpc`
CXXFLAGS += -std=c++17 -fPIC `python3 -m pybind11 --includes`
ifeq ($(SYSTEM),Darwin)
LDFLAGS += -L/usr/local/lib `pkg-config --cflags --libs grpc++ grpc protobuf` -L/opt/anaconda3/lib \
		   -lpython3.12 \
           -pthread\
           -lgrpc++_reflection\
           -ldl
else
LDFLAGS += -L/usr/local/lib `pkg-config --cflags --libs grpc++ grpc protobuf`\
           -pthread\
           -Wl,--no-as-needed -lgrpc++_reflection -Wl,--as-needed\
           -ldl
endif
PROTOC = /opt/homebrew/Cellar/protobuf/27.1/bin/protoc # protoc
GRPC_CPP_PLUGIN = grpc_cpp_plugin
GRPC_CPP_PLUGIN_PATH ?= `which $(GRPC_CPP_PLUGIN)`

PROTOS_PATH = ../rpc

vpath %.proto $(PROTOS_PATH)

all: rpc_agent.grpc.pb.cc rpc_agent.pb.cc rpc_agent_servicer launch_server

rpc_agent_servicer: rpc_agent.pb.o rpc_agent.grpc.pb.o rpc_agent_servicer.o
	$(CXX) $^ $(CXXFLAGS) $(LDFLAGS) -o $@

launch_server:
	export DYLD_LIBRARY_PATH=/opt/anaconda3/lib:$DYLD_LIBRARY_PATH; export PYTHONPATH=/Users/chenyushuo/workspace/agentscope/src:$PYTHONPATH; ./rpc_agent_servicer

%.grpc.pb.cc: ../rpc/%.proto
	$(PROTOC) -I $(PROTOS_PATH) --grpc_out=. --plugin=protoc-gen-grpc=$(GRPC_CPP_PLUGIN_PATH) $<

%.pb.cc: ../rpc/%.proto
	$(PROTOC) -I $(PROTOS_PATH) --cpp_out=. $<

clean:
	rm -f *.o *.pb.cc *.pb.h rpc_agent_servicer
