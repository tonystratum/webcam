from multiprocessing import Process, Queue
import socket
import struct
import sys

import net

if __name__ == "__main__":
    frame_buffer = Queue()

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
        receive_p = Process(target=net.receive_frames, args=(client_socket, frame_buffer, PAYLOAD_SIZE))
        receive_p.start()

        send_p = Process(target=net.send_frames, args=(destination_socket, frame_buffer))
        send_p.start()

    finally:
        client_socket.close()
        server_socket.close()
        destination_socket.close()
