import base64
import copy
import hashlib
import json
import os

from project import Project, get_project

class Controller:
    def __init__(self,args):

        self.args = args
        self.project_name = args.name

        if args.study:
            self.scenario = "0"
            self.AI = args.AI
            self.phase = "information_sheet"
            #self.phase = "intro_text"
        else:
            self.scenario = "T"
            self.project = get_project(args)
            self.phase = "tool"

    @property
    def path(self):
        return os.path.join("static/uploads/project", self.project_name)

    def run_tool(self):
        args_scenario = self.get_scenario_args()
        self.project = get_project(args_scenario)
        self.phase = "tool"

    def get_scenario_args(self):
        args_scenario = copy.deepcopy(self.args)
        args_scenario.name = self.project_name + "/" + self.scenario
        
        args_scenario.offset_path = None
        args_scenario.label_path = None

        if self.scenario == "0":
            args_scenario.AI = True
            args_scenario.close_button = True
            args_scenario.time_seconds = 601

            data = self.args.scenario_0

        else:
            args_scenario.AI = self.AI
            args_scenario.close_button = True

            if self.scenario == "A":
                data = self.args.scenario_A
            elif self.scenario == "B":
                data = self.args.scenario_B
            else:
                print("Unknown Scenario:",self.scenario)
                data = "test"

        if data == "test":
            args_scenario.absolute_paths = False
            args_scenario.video_name = "test_video.mp4"
            args_scenario.video_fps = 1.0
            args_scenario.video_offset = 12
            args_scenario.signal_name = "test_signal.txt"
            args_scenario.sample_rate = 20
            args_scenario.pred_clear_range = 5
        # SHL Data
        else:
            args_scenario.video_fps = 1/30
            args_scenario.sample_rate = 100
            args_scenario.pred_clear_range = 2000

            if data == "test_shl":
                args_scenario.absolute_paths = False
                args_scenario.video_name = "timelapse_test.mp4"
                args_scenario.video_offset = 10500
                args_scenario.signal_name = "Hips_Motion_Test.txt"
            else:
                args_scenario.absolute_paths = True
                args_scenario.video_name = f"/mnt/HDD/data/SHL_User1_v2/release/User1/{data}/timelapse.avi"
                args_scenario.offset_path = f"/mnt/HDD/data/SHL_User1_v2/release/User1/{data}/videooffset.txt"
                args_scenario.signal_name = f"/mnt/HDD/data/SHL_User1_v2/release/User1/{data}/Hips_Motion.txt"

            
        args_scenario.pred_name = f"pred_{data}.json"

        return args_scenario

    def save_JSON_file(self,name,data):
        # Serializing json
        json_object = json.dumps(data, indent=4)
        
        # Writing to file
        with open(os.path.join(self.path, name), "w") as outfile:
            outfile.write(json_object)

    def finish_tool(self):
        if self.scenario == "0":
            self.scenario = "A"
            self.phase = "intro_text"
            self.project = None
        else:
            self.phase = "nasa_tlx"

    def finish_signup(self,form):
        print("Finish signup:",form)

        email = form.pop('InputEmail')
        hasher = hashlib.md5(email.encode('utf-8'))
        hash_val = str(base64.urlsafe_b64encode(hasher.digest()[:10]))[2:16]
        print("Email:",email,"Identifier:",hash_val)

        # Save email and project name
        self.project_name = hash_val
        os.makedirs(self.path,exist_ok=True)

        self.save_JSON_file(hash_val+".json",{email: hash_val})

        # Save details
        self.save_JSON_file("signup.json",form)

        # Start next phase
        self.phase = "intro_video"

    def finish_tlx(self,form):
        print("Finish TLX:",form)

        if self.scenario == "A":
            self.save_JSON_file("TLX_A.json",form)
            self.scenario = "B"
            self.AI = not self.AI
            self.phase = "intro_text"
        else:
            self.save_JSON_file("TLX_B.json",form)
            self.phase = "questionnaire"

        self.project = None

    def finish_questionnaire(self,form):
        print("Finish questionnaire:",form)

        # Save questionnaire responses
        self.save_JSON_file("questionnaire.json",form)

        self.phase = "finish_study"