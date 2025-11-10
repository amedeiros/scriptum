cmake_minimum_required(VERSION 3.10)
project(scriptum_runtime)

set(CMAKE_CXX_STANDARD 17)

# Add the runtime library
add_library(scriptum_runtime SHARED array_runtime.cpp)
