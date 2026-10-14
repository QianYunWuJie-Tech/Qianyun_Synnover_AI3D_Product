cmake_minimum_required(VERSION 3.18)
project(ai3d_example LANGUAGES CXX)

# 本文件随包位于 Examples/CMakeLists.txt，预编译 SDK 位于同级 ../sdk。
list(PREPEND CMAKE_PREFIX_PATH "${CMAKE_CURRENT_LIST_DIR}/../sdk")
find_package(SynnoverAI3D CONFIG REQUIRED)
add_executable(first-frame main.cpp)
target_compile_features(first-frame PRIVATE cxx_std_17)
target_link_libraries(first-frame PRIVATE Synnover::AI3D)
if(MSVC)
  target_compile_options(first-frame PRIVATE /utf-8)
endif()
if(WIN32)
  # 将运行所需 DLL 复制到程序旁边，无需手工设置 PATH。
  file(GLOB SDK_DLLS "${CMAKE_CURRENT_LIST_DIR}/../sdk/bin/*.dll")
  foreach(SDK_DLL IN LISTS SDK_DLLS)
    add_custom_command(TARGET first-frame POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different "${SDK_DLL}" "$<TARGET_FILE_DIR:first-frame>")
  endforeach()
else()
  set_target_properties(first-frame PROPERTIES BUILD_RPATH "${CMAKE_CURRENT_LIST_DIR}/../sdk/lib")
endif()
