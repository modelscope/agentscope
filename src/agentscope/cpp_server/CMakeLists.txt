find_package(Python3 COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG REQUIRED)

source_group(TREE ${CMAKE_CURRENT_SOURCE_DIR} FILES ${SOURCES})

pybind11_add_module(cpp_server worker.cc rpc_agent_servicer.cc)

target_include_directories(cpp_server
    PRIVATE
    ${Python3_INCLUDE_DIRS}
    ${pybind11_INCLUDE_DIRS}
)

target_link_libraries(cpp_server
    PRIVATE
    rpc
)


install(TARGETS cpp_server DESTINATION ${CMAKE_SOURCE_DIR}/src/agentscope/cpp_server)