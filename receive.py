import socket
import numpy as np
import hashlib


addr = ("localhost", 10000)
buf = 512
width = 640
height = 480
code = b'start'
num_of_chunks = width * height * 3 / buf


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(1)

    s, _ = s.accept()  # wait for connection
    try:
        while True:
            chunks = []
            start = False
            frame_hash = None
            while len(chunks) < num_of_chunks:
                chunk, _ = s.recvfrom(buf)
                if start:
                    chunks.append(chunk)
                elif chunk.startswith(code):
                    frame_hash = chunk[-32:]
                    start = True

            byte_frame = b''.join(chunks)
            frame = np.frombuffer(
                byte_frame, dtype=np.uint8).reshape(height, width, 3)
            if hashlib.sha256(frame).digest() == frame_hash:
                # print(frame_hash, "OK")
                print("OK", frame.shape)
            else:
                print("NOT OK", frame.shape)

    finally:
        s.close()
