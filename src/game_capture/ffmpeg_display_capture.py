import cv2

from threading import Thread


class ThreadedCamera(object):
    def __init__(self, source=0):

        self.capture = cv2.VideoCapture(source)

        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

        self.status = False
        self.frame = None

    def update(self):
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()

    def grab_frame(self):
        if self.status:
            return self.frame
        return None


if __name__ == "__main__":
    """
    docker run -p 1935:1935 --name nginx-rtmp tiangolo/nginx-rtmp

    """
    stream_link = "rtmp://127.0.0.1/live/test"

    streamer = ThreadedCamera(stream_link)

    while streamer.capture.isOpened():
        frame = streamer.grab_frame()
        if frame is not None:
            cv2.imshow("OpenCV capture", frame)
        cv2.waitKey(1)
