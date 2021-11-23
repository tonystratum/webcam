from multiprocessing import Process, Queue
import numpy
import socket
import struct
import sys

import net
import numpy
import os

import pathlib
from pycoral.utils import edgetpu
from pycoral.utils import dataset
from pycoral.adapters import common
from pycoral.adapters import detect
from PIL import Image

from infer import draw_bounding_box_on_image


def transpose(receive_buffer: Queue, send_buffer: Queue):
    while True:
        if not receive_buffer.empty():
            frame = receive_buffer.get()
            tframe = numpy.transpose(frame, (1, 0, 2))
            send_buffer.put(tframe)


def detect(receive_buffer: Queue, send_buffer: Queue, model_file, label_file):
    # Initialize the TF interpreter
    # (locks the tpu => bound to the process)
    interpreter = edgetpu.make_interpreter(model_file)
    interpreter.allocate_tensors()

    # Read the labels
    labels = dataset.read_label_file(label_file)

    while True:
        if not receive_buffer.empty():
            frame = receive_buffer.get()

            # Resize the image
            size = common.input_size(interpreter)
            image = Image.fromarray(frame).convert('RGB')
            image_inference = image.copy().resize(size, Image.ANTIALIAS)

            # Run an inference
            common.set_input(interpreter, image_inference)
            interpreter.invoke()
            objects = detect.get_objects(interpreter)

            # Form the result
            for obj in objects:
                width, height = image.size
                scale_x, scale_y = width / size[0], height / size[1]

                bbox = obj.bbox.scale(scale_x, scale_y)
                x0, y0 = int(bbox.xmin), int(bbox.ymin)
                x1, y1 = int(bbox.xmax), int(bbox.ymax)

                draw_bounding_box_on_image(image, y0, x0, y1, x1,
                                           display_str_list=[labels.get(obj.id, obj.id)],
                                           use_normalized_coordinates=False
                                           )

            send_buffer.put(numpy.array(image))


if __name__ == "__main__":
    # Specify the TensorFlow model, labels, and image
    script_dir = pathlib.Path(__file__).parent.absolute()
    model_file = os.path.join(script_dir, 'tf2_ssd_mobilenet_v2_coco17_ptq_edgetpu.tflite')
    label_file = os.path.join(script_dir, 'coco_labels.txt')
    image_file = os.path.join(script_dir, 'people.png')

    receive_buffer, send_buffer = Queue(), Queue()

    # client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_ip = 'localhost'
    client_port = int(sys.argv[1])
    print(f'client: {(client_ip, client_port)}')
    client_socket.connect((client_ip, client_port))
    PAYLOAD_SIZE = struct.calcsize("Q")

    # server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_port = int(sys.argv[2])
    server_ip = 'localhost'
    socket_address = (server_ip, server_port)
    print(f'server: {socket_address}')
    server_socket.bind(socket_address)
    server_socket.listen(5)
    destination_socket, addr = server_socket.accept()

    print("handshake ok")
    try:
        receive_p = Process(target=net.receive_frames, args=(client_socket, receive_buffer, PAYLOAD_SIZE))
        receive_p.start()

        # detect_p = Process(target=detect, args=(receive_buffer, send_buffer, model_file, label_file))
        # detect_p.start()

        transpose_p = Process(target=transpose, args=(receive_buffer, send_buffer))
        transpose_p.start()

        send_p = Process(target=net.send_frames, args=(destination_socket, send_buffer))
        send_p.start()

    finally:
        client_socket.close()
        server_socket.close()
        destination_socket.close()
