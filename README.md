# Simple Webcam Streaming

OpenCV and TCP

Test with Python 3.7.3, OpenCV 4.1.0

I understand this is not the best way to do video streaming but it works for me.

There are still some issues:

1. a flicker at second frame ???
2. flickering when draging the frame window for the first time???
3. not tolerable to data lost (should generate packet loss to simulate the test)

## coral todo:
1. queue received frames to separate thread
2. inference on separate thread
3. send back the inference from separate thread

## host todo:
1. wait response from coral on a separate thread
