import socket
import numpy as np
import hashlib
import cv2


addr = ("localhost", 10007)
width = 640
height = 480
buf = 4096
code = b'start'
num_of_chunks = width * height * 3 / buf


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(1)

    s, t = s.accept()  # wait for connection
    try:
        while True:
            chunks = []
            stop = b'start' + (b' ' * (buf - len(b'start')))
            s.sendto(stop, t)
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
            frame_clean = None
            try:
                frame = np.frombuffer(
                    byte_frame, dtype=np.uint8).reshape(height, width, 3)
                if hashlib.sha256(frame).digest() == frame_hash:
                    frame_clean = frame
                else:
                    print("WRONG HASH")
                    frame_clean = np.zeros((height, width, 3))
            except ValueError:
                print("DATA LOSS")
                frame_clean = np.zeros((height, width, 3))

            cv2.imshow('send', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        s.close()
