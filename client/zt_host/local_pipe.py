import os

class NamedPipe:
	path: str
	mode: str
	fd = None

	def __init__(self, path: str, mode: str):
		self.path = path
		self.mode = mode

	def __enter__(self):
		self.open()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.fd.close()

	def open(self):
		try:
			os.mkfifo(self.path)
		except FileExistsError as e:
			pass
		except OSError as e:
			raise Exception(f"Named pipe creation failed: {e}") from e

		self.fd = open(self.path, self.mode)

	def close(self):
		self.fd.close()
		os.remove(self.path)

	def readline(self, max_line_size = 2048) -> str:
		line = self.fd.readline(max_line_size)

		# Reopen pipe if connection closes early
		if not line:
			self.fd.close()
			self.open()
			
		return line

	def write(self, buf):
		self.fd.write(buf)

	def flush(self):
		self.fd.flush()	
