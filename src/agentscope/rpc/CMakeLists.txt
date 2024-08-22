find_package(protobuf CONFIG REQUIRED)
find_package(gRPC CONFIG REQUIRED)


set(PROTO_FILES
    rpc_agent.proto
    worker_args.proto
)

add_library(rpc ${PROTO_FILES})
target_link_libraries(rpc
    PUBLIC
    protobuf::libprotobuf
    gRPC::grpc
    gRPC::grpc++
)
target_include_directories(rpc PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

get_target_property(grpc_cpp_plugin_location gRPC::grpc_cpp_plugin LOCATION)
protobuf_generate(TARGET rpc LANGUAGE cpp)
protobuf_generate(TARGET rpc LANGUAGE grpc GENERATE_EXTENSIONS .grpc.pb.h .grpc.pb.cc PLUGIN "protoc-gen-grpc=${grpc_cpp_plugin_location}")