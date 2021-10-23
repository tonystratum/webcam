from multiprocessing import Process, Queue
import numpy
import socket
import struct
import sys

import net


def transpose(receive_buffer: Queue, send_buffer: Queue):
    while True:
        if not receive_buffer.empty():
            frame = receive_buffer.get()
            tframe = numpy.transpose(frame, (1, 0, 2))
            send_buffer.put(tframe)


if __name__ == "__main__":
    receive_buffer, send_buffer = Queue(), Queue()

    # client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_ip = 'localhost'
    client_port = int(sys.argv[1])
    print(f'client: {(client_ip, client_port)}')
    client_socket.connect((client_ip, client_port))
    PAYLOAD_SIZE = struct.calcsize("Q")

    # server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_port = int(sys.argv[2])
    server_ip = 'localhost'
    socket_address = (server_ip, server_port)
    print(f'server: {socket_address}')
    server_socket.bind(socket_address)
    server_socket.listen(5)
    destination_socket, addr = server_socket.accept()

    print("handshake ok")
    try:
        receive_p = Process(target=net.receive_frames, args=(client_socket, receive_buffer, PAYLOAD_SIZE))
        receive_p.start()

        transpose_p = Process(target=transpose, args=(receive_buffer, send_buffer))
        transpose_p.start()

        send_p = Process(target=net.send_frames, args=(destination_socket, send_buffer))
        send_p.start()

    finally:
        client_socket.close()
        server_socket.close()
        destination_socket.close()
