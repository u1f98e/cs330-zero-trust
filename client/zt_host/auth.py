import datetime
import socket
from typing import Any, Callable, List

class AuthNode:
	addr: str
	port: int
	rank: int # Lower is better/faster

	def __init__(self, addr: str, port: int, rank: int = 999):
		self.addr = addr
		self.port = port
		self.rank = rank

	def connect(self) -> socket.socket:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((self.addr, self.port))
		return sock

class PeerAuthToken:
	jwt: str
	# JWT also includes the following fields, but we also receive it separately 
	# to avoid needing to decode it
	expiration: datetime = None

class ZTAuth:
	root_addr: str
	root_port: int
	nodes: List[AuthNode] # In order of rank
	system_cred: str # TODO

	def __init__(self, root_addr: str, root_port: int):
		self.root_addr = root_addr
		self.root_port = root_port
		self.refresh_cache_list()

	def refresh_cache_list(self):
		"""Fetch a list of auth nodes from the root node, 
		inserting them into self.caches in order of best to worst.	
		"""
		self.nodes = []

		root_node = AuthNode(self.root_addr, self.root_port)
		self.nodes.append(root_node)
		self.nodes.sort(key = AuthNode.rank)

	def on_best_node(self, func: Callable[[socket.socket], Any]):
		sock = None
		for node in self.nodes:
			try:
				sock = node.connect()
			except Exception as e:
				print(f"Failed to connect to auth node '{node.addr}', trying next.")

		if sock:
			result = func(sock)
			sock.close()
			return result
		else: 
			raise Exception("Unable to connect, all authentication nodes exhausted.")

	def load_credentials(self):
		self.system_cred = ""
		# TODO

	def request_connection_token(self, peer_addr: str, local_addr: str) -> PeerAuthToken:
		def request(sock: socket.socket) -> PeerAuthToken:
			# TODO
			return PeerAuthToken()	

		return self.on_best_node(request)

	def request_refresh_token(self, peer_addr: str) -> PeerAuthToken:
		# TODO if there ends up being a different implementation
		return self.request_connection_token(peer_addr)
