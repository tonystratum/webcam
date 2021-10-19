import concurrent.futures
import queue
import socket
import hashlib
import threading
import time

import cv2 as cv

addr = ("10.110.2.245", 10007)
width = 640
height = 480
fps = 60
buf = 4096
code = 'start'
code = ('start' + (buf - len(code) - 32) * ' ').encode('utf-8')


def buffer_frames(cap, buffer):
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # chunks = [code + hashlib.sha256(frame).digest()]
            data = frame.tobytes()
            # for i in range(0, len(data), buf):
            #     chunks.append(data[i:i + buf])
            buffer.put_nowait(code + hashlib.sha256(frame).digest() + data)
        else:
            break


def listen_for_start(sock: socket.socket, start_event: threading.Event, sent_event: threading.Event):
    while True:
        # print(f"waiting start... {time.time()}")
        start, _ = sock.recvfrom(buf)
        if start.startswith(b'start'):
            start_event.set()
            # print(f"got start {time.time()}")


def send(s: socket.socket, start_event: threading.Event, sent_event: threading.Event, frame_buffer: queue.Queue):
    while True:
        # print(f"waiting... {time.time()}")
        start_event.wait()
        # print(f"received start {time.time()}")
        chunks = None
        if not frame_buffer.empty():
            chunks = frame_buffer.get_nowait()
        else:
            continue

        if chunks is not None:
            # s.sendto(chunks.pop(0), addr)
            # for chunk in chunks:
            #     s.sendto(chunk, addr)
            s.sendall(chunks)
        start_event.clear()
        # print(f"sent {time.time()}")


if __name__ == '__main__':
    cap = cv.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    cap.set(5, fps)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)

    frame_buffer = queue.Queue()
    start_event = threading.Event()
    sent_event = threading.Event()
    sent_event.set()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            executor.submit(listen_for_start, s, start_event, sent_event)
            executor.submit(buffer_frames, cap, frame_buffer)
            # time.sleep(1)
            executor.submit(send, s, start_event, sent_event, frame_buffer)

    finally:
        s.close()
