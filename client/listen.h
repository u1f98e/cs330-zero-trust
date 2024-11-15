#pragma once

#include "Socket/Socket.h"
#include "TCPServer.h"
#include <string>

void listen_for_peers();
void handle_peer(CTCPServer& server, ASocket::Socket peer_socket);