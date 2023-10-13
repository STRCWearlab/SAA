import json
import os
from datetime import datetime, timedelta

from project_signal import Signal
from project_video import Video
from project_annotation import Annotation

default_logger = {
    'AI': True,
    'Anno': True,
    'Buffer': True,
    'Canvas': True,
    'GET': True,
    'Hotkey': True,
    'Input': True,
    'Mouse': True,
    'Playback': True,
    'POST': True,
    'Settings': True,
    'Setup': True,
    'Speed': True,
    'Timer': True,
    'Video': True,
}

def get_project(args):
    return Project( project_name=args.name,

                    video_name=args.video_name,
                    video_fps=args.video_fps,
                    video_offset=args.video_offset,
                    offset_path=args.offset_path,

                    signal_name=args.signal_name,
                    sample_rate=args.sample_rate,

                    pred_name=args.pred_name,
                    label_name=args.label_name,

                    max_samples=args.max_samples,
                    max_bg_markers=args.max_bg_markers,
                    pred_clear_range=args.pred_clear_range,
                    marker_snap_range=args.marker_snap_range,

                    buffer_rate=args.buffer_rate,
                    refresh_rate=args.refresh_rate,
                    play_speed=args.play_speed,
                    max_play_speed=args.max_play_speed,
                    sample_cur=args.initial_sample,
                    time_seconds=args.time_seconds,

                    modus={
                        'debug':args.debug,
                        'clear':args.clear,
                        'hide_settings':args.hide_settings,
                        'restrict_labels':args.restrict_labels,
                        'study':args.study,
                        'AI':args.AI,
                        'absolute_paths':args.absolute_paths,
                        'close_button':args.close_button,
                        },
                )

class Project:
    def __init__(   self,

                    project_name:str        = None,

                    video_name:str          = None,
                    video_fps:float         = 1.,
                    video_offset:float      = 0,
                    offset_path:str         = None,

                    signal_name:str         = None,
                    sample_cur:int          = 0,
                    sample_rate:float       = 1.,

                    pred_name:str           = None,
                    label_name:str          = None,

                    max_samples:int         = 200,
                    max_bg_markers:int      = 25,
                    pred_clear_range:int    = 100,
                    marker_snap_range:float = 5,

                    buffer_rate:float       = 20.,
                    refresh_rate:float      = 24.,  # Refreshs per second
                    play_speed:float        = 1,    # Frames to display per second
                    max_play_speed:float    = 5.,   # Max fps to display
                    signal_zoom:float       = 1.,
                    zoom_factor:float       = 1.5,

                    log_settings:dict       = default_logger,
                    modus:dict              = None,
                    time_seconds:int        = 0,
                ):    
        self.arguments = locals()
        del self.arguments['self']
        self.params = list(self.arguments)
        del self.arguments['project_name']
 
        self.clear = modus['clear']

        self.project_name = None
        if project_name != None:
            self.set_project_name(project_name)

        
        
    def set_project_name(self,project_name:str):
        if project_name == None or project_name == '':
            return False

        self.project_name = project_name

        # Project folder
        self.path = os.path.join("static/uploads/project", project_name)
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)

        # Load Settings
        self.path_settings = os.path.join(self.path,'settings.json')
        if not self.clear and os.path.exists(self.path_settings):
            with open(self.path_settings) as f:
                data = json.load(f)
                self.__dict__.update(data)
                print("Loaded Settings from file.")

            # check any new settings
            new = {k:v for k,v in self.arguments.items() if k not in self.__dict__}
            if len(new) > 0:
                print("New Settings:",new)
                self.__dict__.update(new)
        else:
            self.__dict__.update(self.arguments)
            print("Loaded Settings from arguments.")


        # Log paths
        self.path_log_js = os.path.join(self.path,'log_js.txt')
        self.path_log_py = os.path.join(self.path,'log_js.txt')

        # Prediction
        if self.pred_name is not None:
            self.path_prediction = os.path.join("static/uploads/pred", self.pred_name)
        else:
            self.path_prediction = None

        self.buffer_rate = max(1.0,self.buffer_rate)


        self.video = None
        self.signal = None

        self.set_video()
        self.set_signal()
        self.set_label()
        self.set_pred()

        if self.time_seconds == 0:
            self.target_seconds = 0
        else:
            self.target_seconds = (datetime.now() + timedelta(seconds=self.time_seconds)).timestamp()

        self.save_settings()

        print("Created Project",project_name)
        print("Passed Settings:",self.get_pass_settings())

        return True

    #########################
    #                       #
    #         Paths         #
    #                       #
    #########################

    @property
    def video_path(self):
        if self.video_name is None:
            return None
        if self.modus['absolute_paths']:
            return self.video_name
        else:
            return os.path.join('static/uploads/video/',self.video_name)
        
    @property
    def signal_path(self):
        if self.signal_name is None:
            return None
        if self.modus['absolute_paths']:
            return self.signal_name
        else:
            return os.path.join('static/uploads/signal/',self.signal_name)
        
    @property
    def label_path(self):
        if self.label_name is None:
            return None
        if self.modus['absolute_paths']:
            return self.label_name
        else:
            return os.path.join('static/uploads/label/',self.label_name)

    #########################
    #                       #
    #        Settings       #
    #                       #
    #########################
    
    def get_pass_settings(self):
        return {k:self.__dict__[k] for k in self.params}

    def save_settings(self):
        # Serializing json
        json_object = json.dumps(self.get_pass_settings(), indent=4)
        
        # Writing to file
        with open(self.path_settings, "w") as outfile:
            outfile.write(json_object)
            print("Saved Settings to file.")


    #########################
    #                       #
    #        Logging        #
    #                       #
    #########################

    def log_js(self,txt):
        with open(self.path_log_js, "a+") as file:
            file.write(txt+'\n')


    #########################
    #                       #
    #     Signal Handling   #
    #                       #
    #########################

    def set_signal(self):
        self.signal = Signal(path=self.signal_path, sample_rate=self.sample_rate)
        self.update_signal()

    def update_signal(self):
        if self.video is not None and self.signal is not None:
            self.signal.update( samples_per_frame = self.signal.sample_rate/self.video.fps,
                                video_offset = self.video.sample_offset)


    #########################
    #                       #
    #     Video Handling    #
    #                       #
    #########################

    def set_video(self, initial_frame=1):
        self.video = Video(path=self.video_path, fps=self.video_fps, sample_offset=self.video_offset, offset_path=self.offset_path)
        self.set_frame_current(initial_frame)
        self.update_signal()

    def set_frame_current(self,frame:int):
        self.frame_current = max(1,min(self.video.frame_count,frame))

    def get_frame_video(self,frame:int):
        return self.video.get_frame(frame)


    #########################
    #                       #
    #     Label Handling    #
    #                       #
    #########################

    def set_label(self):
        self.label = Annotation(type_="Anno",path_=os.path.join(self.path,'anno.json'),SHL_label_file=self.label_path)

    def set_pred(self):
        self.pred = Annotation(type_="Pred",path_=os.path.join(self.path,'pred.json'),points=self.get_prediction_file())

    def verify_labels(self):
        ''' Checks the integrity of the current annotation '''
        return False

    #########################
    #                       #
    #      Predictions      #
    #                       #
    #########################

    def get_prediction_file(self):
        data = {}
        if self.path_prediction is not None and os.path.exists(self.path_prediction):
            with open(self.path_prediction) as f:
                data = json.load(f)
        else:
            print(f"No prediction file at {self.path_prediction}")
        return data