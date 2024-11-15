cmake_minimum_required(VERSION 3.20)

project(zt-client
	LANGUAGES C CXX
)

set(CMAKE_CXX_STANDARD 17)

# Verify system dependencies
find_package(OpenSSL)

# Get dependencies
include(FetchContent)
fetchcontent_declare(nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json
    GIT_TAG 9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03
	OVERRIDE_FIND_PACKAGE
)
fetchcontent_makeavailable(nlohmann_json)

fetchcontent_declare(jwt-cpp 
    GIT_REPOSITORY https://github.com/Thalhammer/jwt-cpp.git
    GIT_TAG 08bcf77a687fb06e34138e9e9fa12a4ecbe12332 # v0.7.0 release
)
set(JWT_BUILD_EXAMPLES OFF)
fetchcontent_makeavailable(jwt-cpp)

fetchcontent_declare(socket-cpp
    GIT_REPOSITORY https://github.com/embeddedmz/socket-cpp
    GIT_TAG dafb82265f22fe7c02e1f4e39b60560901b9f8bd
)
fetchcontent_makeavailable(socket-cpp)

add_executable(zt-clientd
	main.cpp
	listen.cpp
	msg.cpp
	wireguard.c
)
target_link_libraries(zt-clientd PRIVATE 
	socket
	jwt-cpp::jwt-cpp
	nlohmann_json::nlohmann_json
)

install(TARGETS zt-clientd)
install(FILES zt-client.service DESTINATION /usr/lib/systemd/system)

GET_DIRECTORY_PROPERTY(output INCLUDE_DIRECTORIES)
MESSAGE(WARNING ${output})