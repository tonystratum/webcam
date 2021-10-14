import socket
import numpy as np


addr = ("192.168.0.108", 10000)
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
            while len(chunks) < num_of_chunks:
                chunk, _ = s.recvfrom(buf)
                if start:
                    chunks.append(chunk)
                elif chunk.startswith(code):
                    start = True

            byte_frame = b''.join(chunks)
            if len(byte_frame) != height * width * 3:
                frame = np.zeros((height, width, 3))
                print("zeros")
            else:
                frame = np.frombuffer(
                    byte_frame, dtype=np.uint8).reshape(height, width, 3)
                print(frame.shape)

    finally:
        s.close()
