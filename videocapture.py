import cv2
from threading import Thread

class ThreadedCamera(object):
    def __init__(self, source = 0):

        self.capture = cv2.VideoCapture(source)

        self.thread = Thread(target = self.update, args = ())
        self.thread.daemon = True
        self.thread.start()

        self.status = False
        self.frame  = None

    def update(self):
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()

    def grab_frame(self):
        if self.status:
            return self.frame
        return None  

if __name__ == '__main__':
    stream_link = "rtmp://127.0.0.1/live/test"
    
    """
    https://gist.github.com/jeasonstudio/914981b346746309828ae31ecda9264c
    
    $ ffmpeg -f avfoundation -list_devices true -i ""
    ...
    [AVFoundation indev @ 0x128905a20] AVFoundation video devices:
    [AVFoundation indev @ 0x128905a20] [0] FaceTime HD Camera
    [AVFoundation indev @ 0x128905a20] [1] Capture screen 0
    [AVFoundation indev @ 0x128905a20] AVFoundation audio devices:
    [AVFoundation indev @ 0x128905a20] [0] MacBook Pro Microphone
    
    speed=0.9x
    $ ffmpeg \
        -f avfoundation \
        -re -i "1" \
        -vcodec h264 \
        -preset ultrafast \
        -acodec aac \
        -ar 44100 \
        -ac 1 \
        -f flv "rtmp://127.0.0.1/live/test"
        
    $ ffmpeg \
        -f avfoundation \
        -video_size 1920x1080 \
        -framerate 30 \
        -re -i "1" \
        -ac 1 \
        -vcodec libx264 -maxrate 2000k \
        -bufsize 2000k -acodec libmp3lame -ar 44100 -b:a 128k \
        -f flv "rtmp://127.0.0.1/live/test"
        
        
    $ sudo nice -n -20 ffmpeg -fflags nobuffer -threads 1 -f avfoundation -thread_queue_size 512 -i "1" -framerate 60 -b:a 256K -c:a aac_at -f flv "rtmp://127.0.0.1/live/test"
    frame= 6654 fps= 30 q=31.0 Lsize=  193437kB time=00:03:42.03 bitrate=7136.9kbits/s speed=   1x
    """
    
    
    threaded_streamer = True
    if threaded_streamer:
        streamer = ThreadedCamera(stream_link)

        while streamer.capture.isOpened():
            frame = streamer.grab_frame()
            if frame is not None:
                cv2.imshow("OpenCV capture", frame)
            cv2.waitKey(1) 
            
    else:
        capture = cv2.VideoCapture(stream_link, cv2.CAP_DSHOW)
        
        capture.cap