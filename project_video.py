import cv2
import numpy as np
import os

# generate frame by frame from video
def gen_frames(video):
    while True:
        success, frame = video.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield frame

class Video:
    def __init__(self,
                    path:str,
                    fps:int,
                    sample_offset:int=0,
                    offset_path:str=None):
        """_summary_

        Args:
            name (str, optional):           Name of the video file in the static folder. Defaults to None.
            fps (int, optional):            Actual FPS of the video (NOT the video file). Defaults to 0.
            sample_offset (int, optional):  Number of signal samples before the video starts. Defaults to 0.
        """
        self.path = path
        self.name = path.split('/')[-1]
        self.fps = fps
        self.sample_offset = sample_offset

        if offset_path is not None:
            self.sample_offset = self.get_offset_from_file(offset_path)        
        

        self.set_video()

    def set_video(self):
        self.video = None
        if self.path is not None:
            self.video = cv2.VideoCapture(self.path)
        else:
            print("ERROR: can't open video",self.path)

        if self.video is None:
            self.active = False
            self.width = 1024
            self.height = 768
            self.frame_count = 0
            self.lst_frames = []

        else:
            self.active = True
            self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
            self.lst_frames = list(gen_frames(self.video))

        array = np.empty((self.height,self.width,4), dtype=np.uint8)
        array.fill(255)
        ret, frame = cv2.imencode('.jpg', array)
        self.clear_frame = frame.tobytes()

    def get_offset_from_file(self,offset_path):
        with open(offset_path) as f:
            line = f.readline()
            self.sample_offset = float(line.split()[1])



    def get_idx_frame(self,idx):
        if idx < 0 or idx >= len(self.lst_frames):
            return self.clear_frame
        else:
            return self.lst_frames[idx]

    def get_frame(self,frame):
        return (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + self.get_idx_frame(frame-1) + b'\r\n')

    def __len__(self):
        return len(self.lst_frames)
