import queue
import socket
import hashlib
import threading

import cv2 as cv

addr = ("localhost", 10001)
width = 640
height = 480
fps = 60
buf = 4096
code = 'start'
code = ('start' + (buf - len(code) - 32) * ' ').encode('utf-8')


def buffer_frames(cap, buffer, lock):
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            chunks = [code + hashlib.sha256(frame).digest()]
            data = frame.tobytes()
            for i in range(0, len(data), buf):
                chunks.append(data[i:i + buf])
            with lock:
                buffer.put_nowait(chunks)
        else:
            break


if __name__ == '__main__':
    cap = cv.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    cap.set(5, fps)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)

    frame_buffer = queue.Queue()
    lock = threading.Lock()
    buffer_thread = threading.Thread(target=buffer_frames, args=(cap, frame_buffer, lock))
    buffer_thread.start()

    send_next = True

    try:
        while True:
            if send_next:
                chunks = None
                with lock:
                    if not frame_buffer.empty():
                        chunks = frame_buffer.get_nowait()
                    else:
                        continue

                if chunks is not None:
                    s.sendto(chunks.pop(0), addr)
                    for chunk in chunks:
                        s.sendto(chunk, addr)
                    send_next = False

                stop, _ = s.recvfrom(buf)
                if stop.startswith(b'stop'):
                    send_next = True
                    # print("allow next")
    finally:
        s.close()
