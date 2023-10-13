import json
import matplotlib.pyplot as plt
import numpy as np
import os

from utils import downsample, fig_to_img, read_csv_file

NAMES_X = ["Time","Acc X","Acc Y","Acc Z",
           "Gyroscope X","Gyroscope Y","Gyroscope Z",
           "Magnetometer X","Magnetometer Y","Magnetometer Z",
           "Orientation W","Orientation X","Orientation Y","Orientation Z",
           "Gravity X","Gravity Y","Gravity Z",
           "Linear acceleration X","Linear acceleration Y","Linear acceleration Z",
           "Pressure","Altitude","Temperature"]


class Signal:
    def __init__(self,
                    path:str,
                    channels:list = ['Acc X', 'Acc Y', 'Acc Z'],
                    video_offset:int = 0,             # In samples
                    video_frames:int = None,          # Number of video frames
                    sample_rate:float = 100.,
                    normalize:bool = True,
                    flip:bool = True,
                    drop_gravity_channel:str = None,  # Rather normalise than drop gravity
                    ):
        self.path = path
        self.name = path.split('/')[-1]
        self.channels = set(channels)
        self.sample_rate = sample_rate

        self.video_offset = video_offset
        self.video_frames = video_frames

        self.signal_df = None
        self.signal = None

        if self.path is not None:

            self.signal_df = read_csv_file(self.path,names=NAMES_X)

            if self.signal_df is None:
                return

            self.signal = self.signal_df.copy()

            # Select channels
            self.signal = self.signal[channels]

            # Remove gravity
            if drop_gravity_channel is not None and drop_gravity_channel in self.signal.columns:
                self.signal[drop_gravity_channel] = self.signal[drop_gravity_channel].sub(9.81)

            if normalize:
                # Center at 0
                self.signal = self.signal - self.signal.mean()

                # Limit scale to -1/1
                self.signal = self.signal / self.signal.abs().max()

                if flip:
                    # Flip the signal and scale between 0.1 and 0.9 for display
                    self.signal = (1.1 - self.signal) * 0.45

            # Fill NaN values
            self.signal.fillna(0,inplace=True)

            # Convert to numpy
            self.signal = self.signal.to_numpy()

        # ADD DEFAULT HANDLING

        self.ylim = (np.min(self.signal), np.max(self.signal))

    @property
    def length(self):
        return self.signal.shape[0] if self.signal is not None else 0

    def __len__(self):
        return self.length

    @property
    def last_sample(self):
        ''' Returns the last sample to start a signal frame '''
        return self.length - self.samples_per_frame

    def update(self,**kwargs):
        ''' Use to update samples_per_frame and video_offset '''
        self.__dict__.update(kwargs)

    def get_data_window_json(self, start:int, stop:int, samples:int=None):
        win = self.get_data_window(start,stop)
        # Perform downsampling if required
        if samples is not None and samples < (stop-start):
            print(f"Downsampling from {stop-start} to { samples}")
            print(f"Before: {win.shape}")
            win = downsample(signal=win, length=samples)
            print(f" After: {win.shape}")
        dic = {chl_name: json.dumps(win[:,i].tolist()) for i,chl_name in enumerate(self.channels)}
        return dic

    def get_data_window(self, start:int, stop:int):
        return self.signal[start:stop]

    def get_start_sample(self,frame:int=1):
        return int(self.video_offset+self.samples_per_frame*(frame-2))