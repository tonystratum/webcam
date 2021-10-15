import socket
import hashlib
import cv2 as cv


addr = ("localhost", 10000)
buf = 512
width = 640
height = 480
cap = cv.VideoCapture(0)
cap.set(3, width)
cap.set(4, height)
code = 'start'
code = ('start' + (buf - len(code) - 32) * ' ').encode('utf-8')


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                s.sendto(code + hashlib.sha256(frame).digest(), addr)
                data = frame.tobytes()
                for i in range(0, len(data), buf):
                    s.sendto(data[i:i+buf], addr)
                # cv.imshow('send', frame)
                # if cv.waitKey(1) & 0xFF == ord('q'):
                    # break
            else:
                break
    finally:
        s.close()
    # s.close()
    # cap.release()
    # cv.destroyAllWindows()
