#include "listen.h"
#include "msg.h"
#include "socket-cpp/Socket/Socket.h"
#include "socket-cpp/Socket/TCPServer.h"
#include <thread>

#define PEER_LISTEN_PORT "9090"

void log_connection(std::string const& msg) {
	std::cout << msg << std::endl;
}

void listen_for_peers() {
	CTCPServer peer_server(log_connection, PEER_LISTEN_PORT);

	while(true) {
		ASocket::Socket peer_socket;
		peer_server.Listen(peer_socket);

		std::thread peer_thread(
			[&peer_server, peer_socket]() { 
				handle_peer(peer_server, peer_socket); 
			}
		);
		peer_thread.detach();
	}
}

void handle_peer(CTCPServer& server, ASocket::Socket peer_socket) {
	std::vector<char> buf;
	buf.resize(PeerRequest::MAX_SIZE);
	server.Receive(peer_socket, buf.data(), buf.size());

	PeerRequest request = PeerRequest::deserialize(buf);

	
}
