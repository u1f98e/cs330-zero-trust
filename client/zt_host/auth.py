import datetime
import socket
from typing import Any, Callable, List, Tuple

import jwt

AUTH_PUBLIC_KEY=b"""
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0ntFvw4YEisJ67WyOJWY
smEPmLjCDqg+OhlUAvMy4DcB+fYM9/EvCupWpx2MTGFf4St88nrEW9pfGDqI4zuM
rCaKda7bchY8DpCUK13ONuuQv0noeXQgMqlIL+Xp15GMOOqjaRsQ+NHio3zX3hLP
P7+IuawESEhnT4aq9CGYIDYqUbKpyIZL3RmQp6vP/ZFOrE8ccSnsa2shembY/UZX
TmsZae4+bPKYH7K9XhvAibO1S9T4z0o661r7BwtbbzsldZhsZUBn5mXIoi4eGl7R
GaqYG7W0M320K5OC9BNP22aBpNUq0CyOh3uOfSpulyQp1g+XP9iHTqwEtMM5lRFq
gwIDAQAB
-----END PUBLIC KEY-----"""

# TODO: Remove when authentication works
FAKE_AUTH_PRIVATE_KEY=b"""-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDSe0W/DhgSKwnr
tbI4lZiyYQ+YuMIOqD46GVQC8zLgNwH59gz38S8K6lanHYxMYV/hK3zyesRb2l8Y
OojjO4ysJop1rttyFjwOkJQrXc4265C/Seh5dCAyqUgv5enXkYw46qNpGxD40eKj
fNfeEs8/v4i5rARISGdPhqr0IZggNipRsqnIhkvdGZCnq8/9kU6sTxxxKexrayF6
Ztj9RldOaxlp7j5s8pgfsr1eG8CJs7VL1PjPSjrrWvsHC1tvOyV1mGxlQGfmZcii
Lh4aXtEZqpgbtbQzfbQrk4L0E0/bZoGk1SrQLI6He459Km6XJCnWD5c/2IdOrAS0
wzmVEWqDAgMBAAECggEAKtB+gH2Kce+lRfggt5fehrJtrMAwYTDh74mFaFA2Ehu+
YC0nuCusSQkf9UBycHsCONhSwzQryw9hdpk5jRdo5v+z/HpEEzHop4HLUgLz1oIW
YILVMhdoEUYT9AJNjdcCcfVwpgmmayaudlkHxBmJZMs+MZ6HBHkN4sRe8+f9fNeJ
VhbaYwbxyrffAU/cPQml3hUEryBKwmVQmGGPZXbAtrt03yVVRrWK7H97AG7qzTbl
NNggC9OxLksTHFx73+UPfkYZNS+j67AKtrZK/tzk9+O49M9nsd+/cxDAt83ddjEF
Re5Zln1eXDl8h48Bctzg6CSiDNtCjcnH+XM2TuxFOQKBgQDpa0YFPP8V4ZHWzoKE
80EUYtxE4nI5R41jH9tg325rwSfax+eLufRpZ2y7axeGiVscz/QANiqFYt3efiSi
UHjYdIMM+rlxGbOZ2djPapENKsBqioHonsRLvDfnIUo9hTsUbos7v6TIbV7TKnKS
VP9sU/NZOuZRa7k+g9GL2ruHLQKBgQDm1/EAm7XSJpcwowKqIyVAnCjgCuf6rbnG
nfITuI/iiT7zYfDMUM9BrDmmd1RH5u04uMQrC9mKNe22U3w8aAB5TMp9VFmpSd0/
iFj2LOpwcPJXppaCkH2y0C1j7k/V8OHA66Ik5QkcgXe402iqY8gRu9gujRx4HjQW
4RfIYSnGbwKBgDMcCBLxjjEuWQ6d3TpbQS7DjtOOedBM+Ipx2UlW4wi5HI7tIqgX
qYrC2K4Y/ue4f7jJV/YL5jeatFYZbNAVqsBKkr9uztgS9p6DctPH08b8S3GIrnVO
/lBPADadtXHPEGai5d3JUr2IJTE7pCaiceM4ZpptKS0+1yr3FhT3agRpAoGAGFX5
jUPdFiuFUtZMiJ0t5zLPSFc9/3pjFGJAS/3wBUTMwyG3HgMC5nx+k2MPGoloxssL
uzIDnAN1bPw+I6wfKKqEylOjJCqqTXFVV5aCnJn7omvogBk1dy1lK5zLA9XiJtFw
hY0zubKYaX64EQZ16BCyiK3Nq4gbm7HdLP25RrcCgYAaWTEb/siTK3GPSLsQEqZt
Ak6aWiwGEp8HIekXVUlIOPg5eoqcFvY69GG9uYTLSnpLc9ALcdHIRt7qTQhm8z+F
4T/hOKgiffwA/Q4dUMLGdBpaJhxia1QirnVVjL6Zo1Zfo/LZgg2pJcJhPy6qeIEi
2jPBBvgMt6E5m87ZPAksXQ==
-----END PRIVATE KEY-----"""

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

	def __init__(self, root_addr: Tuple[str, int]):
		self.root_addr, self.root_port = root_addr
		self.refresh_cache_list()

	def refresh_cache_list(self):
		"""Fetch a list of auth nodes from the root node, 
		inserting them into self.caches in order of best to worst.	
		"""
		self.nodes = []

		root_node = AuthNode(self.root_addr, self.root_port)
		self.nodes.append(root_node)
		self.nodes.sort(key = lambda node: node.rank)

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
		# TODO Load credentials from system to be used with the auth server

	# TODO: Delete me
	def create_fake_request_jwt(local_addr, pub_key):
		claims = { 
			"pub": pub_key,
			"addr": local_addr,
			"ips": f"{local_addr}/32", # Semicolon seperated list of CIDR ranges
			"exp": int(datetime.datetime.fromisoformat("2030-01-01").timestamp())
		}

		token = PeerAuthToken()
		token.jwt = jwt.encode(claims, key=FAKE_AUTH_PRIVATE_KEY, algorithm='RS256')
		token.expiration = claims['exp']
		return token

	def request_connection_token(self, peer_addr: str, local_addr: str, pub_key) -> PeerAuthToken:
		def request(sock: socket.socket) -> PeerAuthToken:
			# TODO: This is a fake token for now, this should
			# instead send a request to the auth node with `sock` to get
			# a token
			return ZTAuth.create_fake_request_jwt(local_addr, pub_key)

		return self.on_best_node(request)

	def request_refresh_token(self, peer_addr: str, local_addr: str) -> PeerAuthToken:
		# TODO if there ends up being a different implementation
		return self.request_connection_token(peer_addr, local_addr)
