cmake_minimum_required(VERSION 3.20)

project(zt-client
	LANGUAGES C CXX
)

add_subdirectory(socket-cpp)

add_executable(zt-clientd
	main.cpp
	wireguard.c
)

target_link_libraries(zt-clientd PRIVATE socket)

install(TARGETS zt-clientd)
install(FILES zt-client.service DESTINATION /usr/lib/systemd/system)