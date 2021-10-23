from multiprocessing import Process, Queue

import socket
import pickle
import struct

from time import time
import sys


def receive_frames(sock: socket.socket, frame_buffer: Queue, PAYLOAD_SIZE: int):
    data = b""
    while True:
        while len(data) < PAYLOAD_SIZE:
            packet = client_socket.recv(4 * 1024)
            if not packet:
                break
            data += packet
        packed_msg_size = data[:PAYLOAD_SIZE]
        data = data[PAYLOAD_SIZE:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        frame_buffer.put(frame)


if __name__ == "__main__":
    frame_buffer = Queue()

    # client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = 'localhost'
    client_port = int(sys.argv[1])
    print(f'client: {(host_ip, client_port)}')
    client_socket.connect((host_ip, client_port))
    PAYLOAD_SIZE = struct.calcsize("Q")

    recv_p = Process(target=receive_frames, args=(client_socket, frame_buffer, PAYLOAD_SIZE))
    recv_p.start()

    # server socket
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_port = int(sys.argv[2])
    server_ip = 'localhost'
    socket_address = (server_ip, server_port)
    print(f'server: {socket_address}')
    server_socket.bind(socket_address)
    server_socket.listen(5)

    send_socket,addr = server_socket.accept()
    while True:
        if send_socket:
            if not frame_buffer.empty():
                frame = frame_buffer.get().T
                a = pickle.dumps(frame)
                message = struct.pack("Q",len(a))+a
                send_socket.sendall(message)

