import subprocess
from typing import Self, List, Tuple

class DeviceConfig:
	listen_port: int = None
	private_key: str = None

class Peer:
	name: str
	public_key: str
	allowed_ips: List[str]
	endpoint_ip: str

class WireguardDevice:
	_name: str

	def create(interface_name: str) -> Self:
		subprocess.run(["wg-quick", "up", interface_name])
		return WireguardDevice(interface_name)

	def __init__(interface_name):
		name = interface_name

	def add_peer(self, peer: Peer):
		params = []
		params += ["public-key", peer.public_key]
		params += ["allowed-ips", peer.allowed_ips]
		params += ["endpoint", peer.endpoint_ip]
		subprocess.run(["wg", "set", self._name, "peer"] + params)

	def remove_peer(self, public_key: str):
		subprocess.run(["wg", "set", self._name, "peer", public_key, "remove"])

	def set_config(self, config: DeviceConfig):
		params = []
		if config.listen_port != None:
			params += ["listen-port", config.listen_port]
		if config.private_key:
			params += ["private-key", config.private_key]

		subprocess.run(["wg", "set", self._name] + params)

	def close(self):
		subprocess.run(["wg-quick", "down", self.name])
