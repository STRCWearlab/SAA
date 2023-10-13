import argparse
from flask import Flask, jsonify, render_template, request, redirect, url_for, Response, send_file
from pathlib import Path
import warnings

from controller import Controller
from project import Project
from utils import get_default_args, serve_pil_image, SignedIntConverter

Path("static/uploads/pred").mkdir(parents=True, exist_ok=True)
Path("static/uploads/signal").mkdir(parents=True, exist_ok=True)
Path("static/uploads/project").mkdir(parents=True, exist_ok=True)
Path("static/uploads/video").mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.url_map.converters['signed_int'] = SignedIntConverter
zentrum = None

###########
# General #
###########

def data2JSON(data,print_resp=True):
    message = {
        'status': 200,
        'message': 'OK',
        'data': data
    }
    resp = jsonify(message)
    resp.status_code = 200
    if print_resp:
        print(resp)
    return resp


#########
# Video #
#########

@app.route('/video_frame/<signed_int:frame>')
def video_frame(frame):
    return Response(zentrum.project.get_frame_video(frame), mimetype='multipart/x-mixed-replace; boundary=frame')


##########
# Signal #
##########

@app.route('/signal_data/<signed_int:start>_<signed_int:stop>_<signed_int:samples>')
def signal_data(start, stop, samples):
    return data2JSON(zentrum.project.signal.get_data_window_json(start, stop, samples))


##############
# Annotation #
##############

@app.route('/submit_anno', methods=['POST'])
def submit_anno():
    data = request.get_json()
    print("submit anno:",data)

    target = data.get('target',None)
    if target == 'label':
        src = zentrum.project.label
    elif target == 'pred':
        src = zentrum.project.pred
    else:
        return f"Unknown target: {target} data: {data} request: {request}", 404

    type = data.get('type',None)
    if type == 'Add':
        status, msg = src.add_anno(int(data['sample']),data['label'])
    elif type == 'Del':
        status, msg = src.del_anno(int(data['sample']))
    else:
        return  f"Unknwon type '{type}' data: {data} request: {request}", 404
 
    return msg, 200 if status else 404


@app.route('/current_labels', methods=['GET'])
def current_labels():
    return data2JSON(zentrum.project.label.get_anno_dict())

@app.route('/current_prediction', methods=['GET'])
def current_prediction():
    return data2JSON(zentrum.project.pred.get_anno_dict())


##########
# Status #
##########

@app.route('/log_js', methods=['PUT'])
def log_js():
    zentrum.project.log_js(str(request.data.decode('UTF-8')))
    return 'Log written', 200


@app.route('/IO_settings', methods=['GET','POST'])
def IO_settings():
    if request.method == 'POST':
        data = request.get_json()
        print("settings/request data:",data)
        error = None
        type = data.get('type',None)
        if type is None:
            error = f"No type to post settings declared. data: {data} request: {request}"
        elif type == 'logSetting':
            zentrum.project.log_settings[data['setting']] = data['active']
        elif type == 'Setting':
            setting = data.get('setting',None)
            value = data.get('value',None)
            if setting is None or value is None:
                error = f"Recieved Setting {setting} with value={value}"
            elif setting == 'FPS': zentrum.project.video.fps = float(value)
            elif setting == 'sample_rate': zentrum.project.signal.sample_rate = float(value)
            elif setting == 'video_offset': zentrum.project.video.sample_offset = float(value)
            elif setting == 'buffer_rate': zentrum.project.buffer_rate = float(value)
            elif setting == 'play_speed': zentrum.project.play_speed = float(value)
            elif setting == 'max_play_speed': zentrum.project.max_play_speed = float(value)
            elif setting == 'refresh_rate': zentrum.project.refresh_rate = float(value)
            elif setting == 'signal_zoom': zentrum.project.signal_zoom = float(value)
            elif setting == 'zoom_factor': zentrum.project.zoom_factor = float(value)
            elif setting == 'sample_cur': zentrum.project.sample_cur = int(value)
            else:
                error = f"Could not find Setting {setting} with value={value}"
        elif type == 'finish_tool':
            zentrum.finish_tool()
            return 'Project closed', 200
        else:
            error = f"Unknwon type '{type}' to post settings declared. data: {data} request: {request}"
        
        if error is None:
            zentrum.project.save_settings()
            return 'Setting update successful', 200
        else:
            return error, 404
    
    elif request.method == 'GET':
        dict_obj = {'FPS':              zentrum.project.video.fps,
                    'sample_rate':      zentrum.project.signal.sample_rate,
                    'sample_number':    zentrum.project.signal.length,

                    'video_name':       zentrum.project.video.name,
                    'video_width':      zentrum.project.video.width,
                    'video_height':     zentrum.project.video.height,
                    'video_fps':        zentrum.project.video.fps,

                    'video_offset':     zentrum.project.video.sample_offset,
                    'frame_number':     zentrum.project.video.frame_count,
                    
                    'max_samples':      zentrum.project.max_samples,
                    'max_bg_markers':   zentrum.project.max_bg_markers,
                    'pred_clear_range': zentrum.project.pred_clear_range,
                    'marker_snap_range':zentrum.project.marker_snap_range,

                    'buffer_rate':      zentrum.project.buffer_rate,
                    'play_speed':       zentrum.project.play_speed,
                    'max_play_speed':   zentrum.project.max_play_speed,
                    'refresh_rate':     zentrum.project.refresh_rate,
                    'signal_zoom':      zentrum.project.signal_zoom,
                    'zoom_factor':      zentrum.project.zoom_factor,
                    
                    'log_settings':     zentrum.project.log_settings,
                    'project_name':     zentrum.project.project_name,
                    'modus':            zentrum.project.modus,
                    'cur_sample':       zentrum.project.sample_cur,
                    'target_seconds':   zentrum.project.target_seconds,
                    }
        return data2JSON(dict_obj)


#########
# Pages #
#########

@app.route("/settings")
def view_settings():
    return render_template("index.html", page="Settings", modus=zentrum.project.modus)

@app.route("/logging")
def view_logging():
    return render_template("index.html", page="Logging", modus=zentrum.project.modus)


##############
# Main Route #
##############

@app.route('/signup', methods=['GET'])
def signup():
    zentrum.phase = "signup"
    return render_template('signup.html')


@app.route('/start', methods=['GET', 'POST'])
def enter_name():
    if request.method == 'POST':
        project_name = request.form['project_name']
        if zentrum.project.set_project_name(project_name):
            return redirect(url_for('index'))

    return render_template('enter_name.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    print(zentrum)
    print("request:",request)
    print(request.form)
    if request.method == 'POST':

        if 'load_video' in request.form:
            return redirect(url_for('upload_video'))

        elif zentrum.phase == "tool":
            zentrum.finish_tool()
            return redirect(url_for('index'))
        
        elif zentrum.phase == "information_sheet":
            zentrum.phase = "consent_form"
            return redirect(url_for('index'))

        elif zentrum.phase == "consent_form":
            zentrum.phase = "signup"
            return redirect(url_for('index'))

        elif zentrum.phase == "signup":
            zentrum.finish_signup(request.form.to_dict())
            return redirect(url_for('index'))

        elif zentrum.phase == "intro_video":
            zentrum.phase = "intro_text"
            return redirect(url_for('index'))

        elif zentrum.phase == "intro_text":
            zentrum.run_tool()
            return redirect(url_for('index'))

        elif zentrum.phase == "nasa_tlx":
            zentrum.finish_tlx(request.form.to_dict())
            return redirect(url_for('index'))

        elif zentrum.phase == "questionnaire":
            zentrum.finish_questionnaire(request.form.to_dict())
            return redirect(url_for('index'))
        

    elif request.method == 'GET':

        if zentrum.phase == "tool":
            if zentrum.project.project_name == None:
                return redirect(url_for('enter_name'))
            else:
                return render_template('index.html', page="Tool", modus=zentrum.project.modus)
        
        elif zentrum.phase == "information_sheet":
            return render_template('info_sheet.html')

        elif zentrum.phase == "consent_form":
            return render_template('consent_form.html')

        elif zentrum.phase == "signup":
            return render_template('signup.html')

        elif zentrum.phase == "intro_video":
            return render_template('intro_video.html')

        elif zentrum.phase == "intro_text":
            return render_template('intro_text.html',scenario=zentrum.scenario,AI=zentrum.AI or zentrum.scenario=='0')

        elif zentrum.phase == "nasa_tlx":
            return render_template('nasa_tlx.html')

        elif zentrum.phase == "questionnaire":
            return render_template('questionnaire.html')

        elif zentrum.phase == "finish_study":
            return render_template('finish_study.html',id=zentrum.project_name)

if __name__ == '__main__':
    defaults_project = get_default_args(Project.__init__)

    parser = argparse.ArgumentParser(description='Set project settings.')
    parser.add_argument('--name',               type=str,   default=defaults_project['project_name'],       help="Name of the project file (required)")

    parser.add_argument('--video_name',         type=str,   default=defaults_project['video_name'],         help='Name/Path of the video file in the upload folder.')
    parser.add_argument('--video_fps',          type=float, default=defaults_project['video_fps'],          help='Frames per seconds of recording in the video. (Not necessarily same as video file)')
    parser.add_argument('--video_offset',       type=float, default=defaults_project['video_offset'],       help='Offset between video and signal.')
    parser.add_argument('--offset_path',        type=str,   default=defaults_project['offset_path'],        help='Path to the offset file.')

    parser.add_argument('--signal_name',        type=str,   default=defaults_project['signal_name'],        help='Name/Path of the signal file in the upload folder.')
    parser.add_argument('--sample_rate',        type=float, default=defaults_project['sample_rate'],        help='Sample rate (in Hz) of the sensor signal.')

    parser.add_argument('--pred_name',          type=str,   default=defaults_project['pred_name'],          help='Name/Path of the prediction file in the upload folder.')
    parser.add_argument('--label_name',         type=str,   default=defaults_project['label_name'],         help='Name/Path of the label file in the upload folder.')

    parser.add_argument('--max_samples',        type=int,   default=defaults_project['max_samples'],        help='How many samples are drawn on a signal screen.')
    parser.add_argument('--max_bg_markers',     type=int,   default=defaults_project['max_bg_markers'],     help='How many vertical sample indicators are displayed on a signal screen.')
    parser.add_argument('--pred_clear_range',   type=int,   default=defaults_project['pred_clear_range'],   help='Sample tolerance to remove predictions around placed annotations.')
    parser.add_argument('--marker_snap_range',  type=float, default=defaults_project['marker_snap_range'],  help='Range of pixel left and right of marker which register mouse clicks.')

    parser.add_argument('--buffer_rate',        type=float, default=defaults_project['buffer_rate'],        help='Ratio of sensor signal screen window stored in buffer.')
    parser.add_argument('--refresh_rate',       type=float, default=defaults_project['refresh_rate'],       help='Refreshs per second.')
    parser.add_argument('--play_speed',         type=float, default=defaults_project['play_speed'],         help='Initial playback speed in frames per second.')
    parser.add_argument('--max_play_speed',     type=float, default=defaults_project['max_play_speed'],     help='Maximum FPS for playback.')
    
    parser.add_argument('--initial_frame',      type=int,   default=None,                                   help='Select initial frame. (deprecated: use initial sample instead)')
    parser.add_argument('--initial_sample',     type=int,   default=defaults_project['sample_cur'],         help='Select initial sample.')
    parser.add_argument('--time_seconds',       type=int,   default=defaults_project['time_seconds'],       help='Set timer for the project.')
    
    parser.add_argument('--scenario_0',         type=str,   default='test',                                 help='Tutorial Scenario: ID for SHL folder or either \'test\' or \'test_shl\'.')
    parser.add_argument('--scenario_A',         type=str,   default='test',                                 help='Scenario A: ID for SHL folder or either \'test\' or \'test_shl\'.')
    parser.add_argument('--scenario_B',         type=str,   default='test',                                 help='Scenario B: ID for SHL folder or either \'test\' or \'test_shl\'.')

    parser.add_argument('--modus',              type=str,   default=defaults_project['modus'],              help='Select one of these modi: \'debug\', \'run\', \'hidden\' (hide settings), \'blocked\' (block access to settings)', choices=['debug', 'run', 'hidden', 'blocked'])
    
    parser.add_argument('--debug',              action="store_true",                                        help='Enter debug mode.')
    parser.add_argument('--clear',              action="store_true",                                        help='Clear current project settings + prediction history.')
    parser.add_argument('--hide_settings',      action="store_true",                                        help='Hide access to settings menu.')
    parser.add_argument('--restrict_labels',    action="store_true",                                        help='Prevent the user from entering new class labels.')
    parser.add_argument('--study',              action="store_true",                                        help='Set up user study.')
    parser.add_argument('--AI',                 action="store_true",                                        help='Activate AI support. For study set true to start with AI.')
    parser.add_argument('--absolute_paths',     action="store_true",                                        help='Paths are absolute')
    parser.add_argument('--close_button',       action="store_true",                                        help='Show tab to close the project')
    
    args = parser.parse_args()
    zentrum = Controller(args)

    app.run(debug=args.debug,host="0.0.0.0",use_reloader=False)
