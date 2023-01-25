import av
import cv2
import numpy as np

if __name__ == "__main__":
    x11grab = av.open(
        ":0.0",
        format="x11grab",
        options={
            "video_size": "2560x1440",
            "framerate": "30",
            "c:v": "libx264",
            "preset": "ultrafast",
            "tune": "zerolatency",
        },
    )
    generator = x11grab.demux(x11grab.streams.video[0])
    for packet in generator:
        frame = np.asarray(packet.decode()[0].to_image())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow("OpenCV capture", frame)
        cv2.waitKey(1)
    print("Done")
