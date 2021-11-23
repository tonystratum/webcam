import pickle
import socket
import struct
import zstd
from multiprocessing import Queue


def send_frames(sock: socket.socket, frame_buffer: Queue):
    while True:
        if sock:
            frame = frame_buffer.get()
            a = pickle.dumps(frame)
            a_zst = zstd.ZSTD_compress(a, 19)
            print(len(a_zst) / len(a))
            message = struct.pack("Q", len(a_zst)) + a_zst
            sock.sendall(message)


def receive_frames(sock: socket.socket, frame_buffer: Queue, payload_size: int):
    data = b""
    while True:
        if sock:
            while len(data) < payload_size:
                packet = sock.recv(8 * 1024)
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += sock.recv(8 * 1024)
            frame_zst = data[:msg_size]
            data = data[msg_size:]
            frame_data = zstd.ZSTD_uncompress(frame_zst)
            frame = pickle.loads(frame_data)
            frame_buffer.put(frame)
