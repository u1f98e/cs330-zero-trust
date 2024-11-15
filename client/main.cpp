#include <cstdio>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

extern "C" {
#include "wireguard.h"
}
#include "wg_types.h"
#include "listen.h"

std::vector<std::string> get_device_names() {
	// wg_list_device_names hands back an array of
	// names seperated by \0 and terminated by \0\0
	char* names = wg_list_device_names();
	std::vector<std::string> name_vec;
	while(true) {
		std::string name(names);
		if(name.empty()) {
			break;
		}
		names += name.size();
		name_vec.push_back(name);
	}

	return name_vec;
}

int main(int argc, char* argv[]) {
	if(argc > 1) {
		if(std::string(argv[1]) == "list") {
			auto names = get_device_names();
			for(auto const& name : names) {
				std::cout << name << '\n';
			}
			return 0;
		}
	}

	auto tunnel = WgDevice::create_device("wgTest0");

	// Start listening for peer connection requests on another thread
	std::thread peer_listen_thread(listen_for_peers);
}
