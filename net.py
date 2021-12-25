import pickle
import socket
import struct
from multiprocessing import Queue

import cv2


def send_frames(sock: socket.socket, frame_buffer: Queue):
    while True:
        if sock:
            frame = frame_buffer.get()
            a = pickle.dumps(
                cv2.imencode(".jpg", frame, (1, 50))[1]
            )
            message = struct.pack("Q", len(a)) + a
            sock.sendall(message)


def receive_frames(sock: socket.socket, frame_buffer: Queue, payload_size: int):
    data = b""
    while True:
        if sock:
            while len(data) < payload_size:
                packet = sock.recv(4 * 1024)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += sock.recv(4 * 1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame_jpeg = pickle.loads(frame_data)
            frame = cv2.imdecode(frame_jpeg, 1)
            frame_buffer.put(frame)
