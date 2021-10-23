from multiprocessing import Process, Queue
import socket
import cv2
import pickle
import struct

import sys


def buffer_frames(capture: cv2.VideoCapture, frame_buffer: Queue):
    while capture.isOpened():
        frame_buffer.put(capture.read())


def send_frames(sock: socket.socket, frame_buffer: Queue):
    while True:
        if sock:
            img, frame = frame_buffer.get()

            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            sock.sendall(message)


def receive_processed_frames(sock: socket.socket, frame_buffer: Queue, PAYLOAD_SIZE: int):
    data = b""
    while True:
        if sock:
            while len(data) < PAYLOAD_SIZE:
                packet = sock.recv(4 * 1024)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:PAYLOAD_SIZE]
            data = data[PAYLOAD_SIZE:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += sock.recv(4 * 1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)
            frame_buffer.put(frame)


if __name__ == "__main__":
    capture = cv2.VideoCapture(0)

    send_buffer, receive_buffer = Queue(), Queue()

    # server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = 'localhost'
    server_port = int(sys.argv[1])
    server_socket_address = (server_ip, server_port)
    print(f'server: {server_socket_address}')
    server_socket.bind(server_socket_address)
    server_socket.listen(5)
    destination_socket, addr = server_socket.accept()

    cap_p = Process(target=buffer_frames, args=(capture, send_buffer))
    cap_p.start()

    send_p = Process(target=send_frames, args=(destination_socket, send_buffer))
    send_p.start()

    # connect to coral as a client
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_ip = 'localhost'
    recv_port = int(sys.argv[2])
    print(f'client: {(recv_ip, recv_port)}')
    recv_socket.connect((recv_ip, recv_port))
    PAYLOAD_SIZE = struct.calcsize("Q")

    receive_p = Process(target=receive_processed_frames, args=(recv_socket, receive_buffer, PAYLOAD_SIZE))
    receive_p.start()

    while True:
        if not receive_buffer.empty():
            frame = receive_buffer.get()
            cv2.imshow('Receiving...', frame)
            key = cv2.waitKey(10)
            if key == 13:
                recv_socket.close()
