from time import sleep
from select import select
from threading import Thread
from traceback import print_exc
from struct import pack, unpack, error as struct_error
from socket import socket, SHUT_RDWR, error as socket_error


SOCK_ERROR = b'\x01'
SOCK_TIMEOUT = b'\x00'


class Socket(object):
    """
    Creates an easy to use abstracted standard for transporting and reconstructing messages over TCP.
    """

    def __init__(self, sock=None, timeout: int=60, debug: bool=False):
        """
        sock: Existing socket to use if supplied.

        timeout: Time to wait (in seconds) for certain socket operations before stopping. I.e. connecting, reading data.
        
        debug: If set to true, the stack trace will be printed to console upon errors for debugging.
        """

        self.timeout = timeout
        self.debug = debug
        self.__sock = sock

    def __str__(self) -> str:
        return f"gruv_socks.Socket(timeout={self.timeout}, debug={self.debug})"
    
    def __add__(self, x: bytes) -> bool:
        return self.write(x)

    def connect(self, host: str, port: int) -> bool:
        """
        Attempts to establish a connection to a given host. Returns bool dictating status.

        host: Hostname/Address of host to connect to.

        port: Port on the given host to connect to.
        """

        if self.__sock is not None:
            print(f"[ERROR] (Socket.connect) could not connect, reason: socket already connected")
            return False

        try:
            self.__sock = socket()
            self.__sock.settimeout(self.timeout)
            self.__sock.connect((host, port))

            return True
        except Exception as err:
            if self.debug: print_exc()
            print(f"[SOCKET ERROR] (Socket.connect) could not connect, reason: {err}")
            return False

    def read(self, timeout_override: int=0) -> tuple[bool, bytes]:
        """
        Attempts to read data from the socket object.

        Returns a tuple containing a boolean dictating success status, and then the received data in byte string.
        If the status is False, then either gruv_socks.SOCK_ERROR, or gruv_socks.SOCK_TIMEOUT will be returned as the data.

        timeout_override: If not 0, then overrides the set timeout for this singular read call.
        """        
        fragments = []  # mutable types are faster to process than immutable types such as byte strings
        data_length = 0
        message_length = 0
        timeout = timeout_override if timeout_override != 0 else self.timeout

        if self.__sock is None:
            print("[ERROR] (Socket.read) could not receive data, reason: socket is not connected")
            return (False, SOCK_TIMEOUT)

        try:
            # use timeout override (if set) only upon first read
            if len(select([self.__sock], [], [], timeout)[0]) == 0:
                return (False, b'\x00')

            message_length = unpack(">I", self.__sock.recv(4))[0]

            while data_length < message_length:
                # creating and getting length of buffer is faster than indexing and calling len on fragments
                buffer = self.__sock.recv(message_length-data_length)
                data_length += len(buffer)
                fragments.append(buffer)

        except struct_error as err:
            if self.debug: print_exc()
            print(f"[STRUCT ERROR] (Socket.read) could not receive data, reason: {err}")
            return (False, SOCK_ERROR)

        except socket_error as err:
            if self.debug: print_exc()
            print(f"[SOCKET ERROR] (Socket.read) could not receive data, reason: {err}")
            return (False, SOCK_ERROR)

        except Exception as err:
            if self.debug: print_exc()
            print(f"[ERROR] (Socket.read) could not receive data, reason: {err}")
            return (False, SOCK_ERROR)

        return (True, b''.join(fragments))
    
    def write(self, data: bytes or str) -> bool:
        """
        Attempts to write data to socket object, sending it to the connected host. Returns boolean dictating status.

        data: Data to send to connected host.
        """

        if self.__sock is None:
            print("[ERROR] (Socket.write) could not send data, reason: socket is not connected")
            return False

        if isinstance(data, str):
            data = data.encode()

        sent = 0
        length = len(data)

        try:
            data = pack(">I", length) + data

            while sent < length:
                sent += self.__sock.send(data[sent:])

            return True

        except struct_error as err:
            if self.debug: print_exc()
            print(f"[STRUCT ERROR] (Socket.write) could not send data, reason: {err}")

            return False

        except socket_error as err:
            if self.debug: print_exc()
            print(f"[SOCKET ERROR] (Socket.write) could not send data, reason: {err}")

            return False

        except Exception as err:
            if self.debug: print_exc()
            print(f"[ERROR] (Socket.write) could not send data, reason: {err}")

            return False


    def disconnect(self):
        """
        Properly disconnects the socket object by shutting down READ/WRITE channels, and then closing the socket.
        """
        if self.__sock is None: return

        try: self.__sock.shutdown(SHUT_RDWR)
        except Exception: pass
        finally:
            try: self.__sock.close()
            except Exception: pass
            finally: self.__sock = None
    
    def __del__(self):
        """
        Socket destructor, ensures the socket object properly closes before being destroyed.
        """

        self.disconnect()


class ServerBase:
    """
    Quasi-framework for creating a server using the Socket object.
    """
    def __init__(self, debug: bool=False):
        """
        Initializes the ServerBase object.

        debug: Decides if stack trace information is printed to console or not.
        """

        self.debug = debug
        self.running = False
        self.__listener = None
    
    def __listen(self, callback):
        """
        Listens for incoming connections and hands them off to the callback function supplied.
        """

        while self.running:
            try:
                if select([self.__listener], [], [], 0.1)[0] == []: continue
                sock, addr = self.__listener.accept()

                t = Thread(target=callback, args=(addr, Socket(sock, debug=self.debug)))
                t.setDaemon(True)
                t.start()
            
            except KeyboardInterrupt:
                self.running = False

            except Exception as err:
                if self.debug: print_exc()
                if self.running: print(f"[ERROR] (ServerBase.__listen): {err}")
    
    def start(self, callback, port: int, address: str="0.0.0.0", blocking: bool = False):
        """
        Makes the server listen with the given configuration.

        The callback function is supplied 2 arguments. The first is a tuple of the remote IP, and the remote port.
        The second argument is the Socket object of the remote connection.

        callback: Callback function to trigger upon new connections. 
        callback( (host: str, port: int), Socket )

        port: Port to listen on.

        address: Address to listen on.

        blocking: Boolean dictating wether or not this function should block, or spawn a thread to listen.
        """

        if self.__listener is not None:
            raise Exception("server is already listening")

        self.__listener = socket()
        self.__listener.bind((address, port))
        self.__listener.listen()
        self.running = True

        if blocking:
            self.__listen(callback)
        else:
            t = Thread(target=self.__listen, args=(callback,))
            t.setDaemon(True)
            t.start()

    def stop(self):
        """
        Stops the server by shutting down the listening socket and triggering the background thread to stop.
        """
        self.running = False

        sleep(0.2)

        try: self.__listener.shutdown(SHUT_RDWR)
        except Exception: pass
        finally:
            try: self.__listener.close()
            except Exception: pass

        self.__listener = None


    def __del__(self):
        """
        Ensures the listening socket is properly closed, and the listening thread exits gracefully.
        """
        if self.running is True:
            self.stop()


def echo_callback(addr: tuple[str, int], sock: Socket):
    data = sock.read()[1]
    sock.write(data)
    sock.disconnect()


def server_test():
    conn = Socket(debug=True)
    serv = ServerBase(debug=True)

    serv.start(echo_callback, 5551, address="127.0.0.1")
    conn.connect("127.0.0.1", 5551)
    conn.write(b"If you see this message, that means gruv_socks is working!")
    print(conn.read()[1].decode())

    conn.disconnect()
    serv.stop()


if __name__ == "__main__":
    server_test()
