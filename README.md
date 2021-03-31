# gruv-socks

This script provides a simple to use base server class and a Socket object that abstracts away the needed work to transport and recieve messages over TCP.

NOTE: The method used to reconstruct fragments does not work with protocols such as HTTP. This is designed to be used with simple self designed protocols.

## Installation
`pip install gruv_socks`

## Usage
Simple examples to show you how the library can be used.

### Test Install

```py
from gruv_socks.gruv_socks import server_test

print(server_test())
b"If you see this message, that means gruv_socks is working!"
```

### Create Echo Server
This script will create a server that listens for data from clients, sends it back, then closes the connection. It will continue to run until stopped with `Ctrl+C` due to the `blocking=True` parameter in line 14. The deconstructor of the Socket object ensures it is properly closed, so you do not need to explicitly call it unless needed.

```py
from gruv_socks.gruv_socks import ServerBase, SOCK_ERROR, SOCK_TIMEOUT

def callback(addr, sock):
	status, data = sock.read()  # receive read status, and received data

	# exit if read failed
	if status is False and data == SOCK_ERROR:
		print("client error")
		return
	elif status is False and data == SOCK_TIMEOUT:
		print("client timeout")
		return

	sock.write(data)  # send data back to client
	print(f"{addr[0]} said: {data.decode()}")

def main():
	server = ServerBase()
	server.start(callback, 5551, blocking=True)

if __name__ == "__main__":
	main()
```

### Create Echo Client
This script will connect to the server running from the above script, send the text "Hello world!" disconnect, and then exit.

```py
from gruv_socks.gruv_socks import Socket

def main():
	sock = Socket()
	
	sock.connect("localhost", 5551)
	sock.write("Hello world!")
	# NOTE: Socket + str/bytes [sock + "foo"] is valid shorthand for sock.write()

	print(sock.read()[1])

	sock.disconnect()

if __name__ == "__main__":
	main()
```


## Items Provided
A breakdown of the provided functions, objects, and variables.

### Variable: SOCK_ERROR
Use to determine if a socket encountered an error.

### Variable: SOCK_TIMEOUT
Use to determine if a socket encountered a time out.

### Function: echo_callback(addr: tuple[str, int], sock: Socket)
Simple callback function to create an echo server with the ServerBase object.

### Function: server_test()
Direct call function to test the BaseServer and Socket objects locally on the machine running it to ensure the library is working.

### Object: Socket

#### Socket.timeout: int
Timeout (in seconds) to use for socket operations.

#### Socket.debug: bool
Decides if stack trace information is printed to console or not.

#### Socket.__sock: socket.socket
Holds the underlying socket object that communication is preformed with.

#### Socket.\_\_init__(self, sock=None, timeout: int=60, debug: bool=False)
sock: Existing socket to use if supplied.

timeout: Time to wait (in seconds) for certain socket operations before stopping. I.e. connecting, reading data.
        
debug: If set to true, the stack trace will be printed to console upon errors for debugging.

#### Socket.\_\_str__(self) -> str
```py
def __str__(self) -> str:
    return f"gruv_socks.Socket(timeout={self.timeout}, debug={self.debug})"
```

#### Socket.\_\_add__(self, x: bytes) -> bool
Shorthand for Socket.write()

```py
def __add__(self, x: bytes) -> bool:
    return self.write(x)
```

Usage

```py
from gruv_socks.gruv_socks import Socket

sock = Socket()
sock.connect("localhost", 5551)
sock + b"Hello world!"
```

#### Socket.connect(self, host: str, port: int) -> bool
Attempts to establish a connection to a given host. Returns bool dictating status.

host: Hostname/Address of host to connect to.

port: Port on the given host to connect to.

#### Socket.read(self, timeout_override: int=0) -> tuple[bool, bytes]
Attempts to read data from the socket object.

Returns a tuple containing a boolean dictating success status, and then the received data in byte string.
If the status is False, then either gruv_socks.SOCK_ERROR, or gruv_socks.SOCK_TIMEOUT will be returned as the data.

timeout_override: If not 0, then overrides the set timeout for this singular read call.

#### Socket.write(self, data: bytes or str) -> bool
Attempts to write data to socket object, sending it to the connected host. Returns boolean dictating status.

data: Data to send to connected host.

#### Socket.disconnect(self)
Properly disconnects the socket object by shutting down READ/WRITE channels, and then closing the socket.

#### Socket.\_\_del__(self)
Socket destructor, ensures the socket object properly closes before being destroyed.

### Object:ServerBase

#### ServerBase.\_\_init__(self, debug: bool=False)
Initializes the ServerBase object.

debug: Decides if stack trace information is printed to console or not.

#### ServerBase.\_\_listen(self, callback)
Listens for incoming connections and hands them off to the callback function supplied.

#### ServerBase.start(self, callback, port: int, address: str="0.0.0.0", blocking: bool = False)
Makes the server listen with the given configuration.

The callback function is supplied 2 arguments. The first is a tuple of the remote IP, and the remote port.
The second argument is the Socket object of the remote connection.

callback: Callback function to trigger upon new connections. 
callback( (host: str, port: int), Socket )

port: Port to listen on.

address: Address to listen on.

blocking: Boolean dictating wether or not this function should block, or spawn a thread to listen.

#### ServerBase.stop(self)
Stops the server by shutting down the listening socket and triggering the background thread to stop.

#### ServerBase.\_\_del__(self)
Ensures the listening socket is properly closed, and the listening thread exits gracefully.