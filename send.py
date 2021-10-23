import cv2
from multiprocessing import Process, Queue
import socket
import struct
import sys
import time

import net


def buffer_frames(capture: cv2.VideoCapture, frame_buffer: Queue):
    while capture.isOpened():
        frame_buffer.put(capture.read()[1])


if __name__ == "__main__":
    webcam = cv2.VideoCapture(0)

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

    # connect to coral as a client
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_ip = 'localhost'
    recv_port = int(sys.argv[2])
    print(f'client: {(recv_ip, recv_port)}')
    time.sleep(1)
    recv_socket.connect((recv_ip, recv_port))
    PAYLOAD_SIZE = struct.calcsize("Q")

    print("handshake ok")
    try:
        cap_p = Process(target=buffer_frames, args=(webcam, send_buffer))
        cap_p.start()

        send_p = Process(target=net.send_frames, args=(destination_socket, send_buffer))
        send_p.start()

        receive_p = Process(target=net.receive_frames, args=(recv_socket, receive_buffer, PAYLOAD_SIZE))
        receive_p.start()

        while True:
            if not receive_buffer.empty():
                frame = receive_buffer.get()
                cv2.imshow('Receiving...', frame)
                key = cv2.waitKey(10)
                if key == 13:
                    recv_socket.close()

    finally:
        server_socket.close()
        destination_socket.close()
        recv_socket.close()
