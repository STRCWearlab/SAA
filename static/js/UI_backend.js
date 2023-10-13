// ************************ //
//                          //
//         Settings         //
//                          //
// ************************ //

class Settings {

  #_buffer;

  // ###############
  // #   Tracker   #
  // ###############
  #_FPS;
  #_sample_rate;
  #_sample_number;
  #_video_offset;
  #_frame_number;

  #_sample = null;
  #_frame = null;
  #_first_sample;
  #_last_sample;
  #_start_samples;

  #_is_drawing = false;

  constructor(
    modus,
    project_name = 'unnamed',
    FPS = 0.0, 
    sample_rate = 1.0, 
    sample_number = 0, 
    sample_cur = null,

    video_name = "",
    video_width = 0,
    video_height = 0,
    video_fps = 0.0,

    video_offset = 0, 
    frame_number = 0, 
    
    max_samples = 100,
    max_bg_markers = 100,
    pred_clear_range = 100,
    marker_snap_range = 10,

    buffer_rate = 5.0, 
    play_speed = 1.0,
    max_play_speed = 30.0,
    refresh_rate = 1.0, 
    signal_zoom = 1.0,
    zoom_factor = 1.5,
    target_seconds = 0,
    
    ){

    this.isPlaying = false;
    this.project_name = project_name;
    this.modus = modus;

    // #################
    // #   Constants   #
    // #################

    // Actual frames per second of the video (NOT of the video file)
    this.#_FPS = FPS;

    // Sampling Rate of the sensor signal in Hz
    this.#_sample_rate = sample_rate;

    // Number of samples in the signal
    this.#_sample_number = sample_number;

    // Number of samples after which the video starts
    this.#_video_offset = video_offset;

    // Number of frames in the video
    this.#_frame_number = frame_number;

    // Current sample
    if (sample_cur === null) {
      this.#_sample = this.video_offset + this.samples_per_frame/2;
    }
    else {
      this.#_sample = sample_cur;
    }
    

    // Calculate first and last samples
    this.calc_samples();

    // General Video information
    this.video_name = video_name;
    this.video_width = video_width;
    this.video_height = video_height;
    this.video_fps = video_fps;


    // ###################
    // #   UI Settings   #
    // ###################

    // Number of samples drawn on a signal screen
    this.max_samples = max_samples;

    // Number of vertical sample indicators displayed on a signal screen
    this.max_bg_markers = max_bg_markers;

    // Sample tolerance to remove predictions around placed annotations
    this.pred_clear_range = pred_clear_range;

    // Range of pixel left and right of annotation marker which register mouse clicks
    this.marker_snap_range = marker_snap_range;


    // ################
    // #   Settings   #
    // ################

    // Ratio of the current displayed signal length stored in buffer (Should be at least 2.0)
    this.buffer_rate = buffer_rate;

    // Playspeed control element
    this.speed_ctrl = new PlaySpeed(play_speed,0.05,max_play_speed);

    this.sample_ctrl = new BasicSlider({minval:0,maxval:sample_number});

    // Refreshs of the display in seconds (relevant for smooth signal moving)
    this.refresh_rate = refresh_rate;

    // Ratio of frame signal window to screen signal window 
    // 0.5 - 2 frame signal window are displayed at once (zoom out)
    // 1.0 - the length of the signal for one frame window will be displayed
    // 2.0 - half of the frame signal will be displayed (zoom in)
    this.signal_zoom = signal_zoom;

    // Factor to change zoom
    this.zoom_factor = zoom_factor;

    // Set timer if required
    if (target_seconds > 0){
      this.timer = new Timer(target_seconds);
    }
    else {
      globLog.log('Timer',"No timer set.");
      this.timer = null;
    }

    // ###################
    // #   Signal Data   #
    // ###################
    
    this.set_buffer();


    // #####################
    // #   AI Assistance   #
    // #####################

    this.AI_ctrl = new AI_CTRL(this.delay,false);

  }


  // ###############
  // #   Getters   #
  // ###############

  get FPS(){return this.#_FPS;}
  get sample_rate(){return this.#_sample_rate;}
  get sample_number(){return this.#_sample_number;}
  get video_offset(){return this.#_video_offset;}
  get frame_number(){return this.#_frame_number;}

  get sample(){return this.#_sample;}
  get sample_cur(){return this.sample;}
  get frame(){return this.#_frame;}
  get first_sample(){return this.#_first_sample;}
  get last_sample(){return this.#_last_sample;}

  // First sample displayed
  get start_sample(){return Math.round(this.sample-.5*this.samples_per_screen);}

  // Last sample displayed
  get stop_sample(){return Math.round(this.sample+.5*this.samples_per_screen);}

  // How many signal samples cover the length of one frame
  get samples_per_frame(){
    return this.sample_rate / this.FPS;
  }

  // How many signal samples are represented at once
  get samples_per_screen(){
    return this.samples_per_frame / this.signal_zoom;
  }

  // // How many signal samples are left or right of the marker
  // get half_samples_per_screen(){
  //   return Math.round(1/2 * this.samples_per_frame / this.signal_zoom);
  // }

  // How many signal samples are actually plotted
  get samples_displayed(){
    return Math.min(this.samples_per_screen, this.max_samples);
  }

  // How many samples the signal moves at each refresh
  get samples_per_tick(){
    return this.samples_per_frame * this.play_speed / this.refresh_rate;
  }

  // Length of the delay before refreshing the display in ms
  get delay(){
    return 1000 / this.refresh_rate;
  }

  // Returns true while keyboard hotkeys are active
  get hotkeys_active(){
    return globAnno.selectedSample === null;
  }

  // ###############
  // #   Setters   #
  // ###############

  set FPS(val){this.#_FPS=Math.max(0,val);this.calc_samples();}
  set sample_rate(val){if (val!=0){this.#_sample_rate=val;this.calc_samples();}}
  set sample_number(val){this.#_sample_number=val;this.calc_samples();}
  set video_offset(val){this.#_video_offset=val;this.calc_samples();}
  set frame_number(val){this.#_frame_number=val;this.calc_samples();}
  
  set sample_cur(val){this.#_sample=val;}
  
  setSetting(setting,value){
    globLog.log("Settings","Set",setting,"to",value);
    this[setting] = value;
    POST_setting(setting,this[setting]);
  }


  // ####################
  // #    Playback     #
  // ####################

  async startPlay(){
    globLog.log('Playback',"Start Play!");
    this.isPlaying = true;
    this.AI_ctrl.resume();
    setTimeout(()=>UpdateStream(this.sample),this.delay);
    refreshButtons();
  }
  
  stopPlay(){
    globLog.log('Playback',"Stop Play!");
    this.isPlaying = false;
    this.AI_ctrl.pause();
    this.sync_sample();
    refreshButtons();
  }
  
  togglePlay(msg){
    globLog.log('Playback',"Toggle Play!");
    if (this.isPlaying){this.stopPlay();}
    else if (this.can_move_forwards()){this.startPlay();}
  }

  cancel_move(del_pred=false){
    this.speed_ctrl.cancel_move(del_pred);
  }

  get play_speed(){return this.speed_ctrl.value;}
  set play_speed(val){this.speed_ctrl.value = val;}

  get play_speed_pos(){return this.speed_ctrl.position;}
  set play_speed_pos(pos){this.speed_ctrl.position = pos;}

  get max_play_speed(){return this.speed_ctrl.max_play_speed;}
 
  // ###############
  // #    Zoom     #
  // ###############

  get can_zoom_in(){
    return true;
  }

  get can_zoom_out(){
    return true;
  }

  zoom_out(){if (this.can_zoom_out) { this.zoom_to(this.signal_zoom / this.zoom_factor); }}
  zoom_in(){if (this.can_zoom_in) { this.zoom_to(this.signal_zoom * this.zoom_factor); }}

  async zoom_to(zoom_lvl){
    this.setSetting("signal_zoom",zoom_lvl);
    await this.set_buffer();
    this.redrawSample();
  }

  // ##################
  // #  Calculations  #
  // ##################

  get_start_samples_in_range(start, stop){
    return this.#_start_samples.filter(sample => sample>start && sample<stop);
  }

  // Get the starting sample for a frame
  get_start_sample(frame=null){
    if (frame===null){frame = this.frame;}
    return parseInt(this.video_offset + this.samples_per_frame * (frame-2));
  }

  // Get the Frame for a given sample
  get_frame(sample){
    return parseInt(2 + (sample - this.video_offset) / this.samples_per_frame);
  }

  get_time_stamp_str(sample){
    let text = '';
    let sec_num = Math.round(sample / this.sample_rate);
    let negative = (sec_num < 0);
    if (negative) {sec_num = -sec_num;text=text+'-';}

    let hh = Math.floor(sec_num / 3600);
    let mm = Math.floor((sec_num - (hh * 3600)) / 60);
    let ss = sec_num - (hh * 3600) - (mm * 60);

    if (hh < 10) {hh = "0"+hh;}
    if (mm < 10) {mm = "0"+mm;}
    if (ss < 10) {ss = "0"+ss;}
     
    if (hh>0){text = text+hh+':'}
    text = text + mm+':'+ss;
    return text;
  }

  // ###############
  // #  Functions  #
  // ###############


  can_move_backwards(){return this.sample > this.first_sample;}
  can_move_forwards(){return this.sample < this.last_sample;}

  moveFirst(){this.setSample(this.first_sample);}
  movePrev(){ if(this.can_move_backwards()) this.setFrame(this.frame-1);}
  moveNext(){ if(this.can_move_forwards()) this.setFrame(this.frame+1);}
  moveLast(){this.setSample(this.last_sample);}

  // Sync the current sample with the backend
  async sync_sample(){POST_setting("sample_cur",this.sample_cur);}

  async set_buffer(){
    //globLog.log("Settings","Set Buffer start =",this.start_sample);
    this.#_buffer = new Buffer(this.samples_per_screen * this.buffer_rate, this.sample_number);
    if (this.#_sample!=null){
      await this.#_buffer.setStart(this.start_sample);
    }
  }

  calc_samples(){
    // Calculate the first sample of each frame
    this.#_start_samples = SortedSet();

    let frame_idx = 1;
    while(frame_idx <= this.frame_number){
      this.#_start_samples.push(this.get_start_sample(frame_idx));
      frame_idx += 1;
    }

    // Calculate first and last samples for jump buttons
    this.#_first_sample = Math.min(0,this.get_start_sample(1));
    this.#_last_sample = Math.max(this.sample_number-this.samples_per_frame,this.get_start_sample(this.frame_number));
  }

  async get_signal_data(){
    //globLog.log('Buffer',"Start:",this.sample,"Stop:",this.sample+this.samples_per_screen,"Samples:",this.samples_per_screen)
    let data = await this.#_buffer.get_data(this.start_sample, this.stop_sample);
    //let data = await this.#_buffer.get_data(this.sample-this.half_samples_per_screen, this.sample+this.half_samples_per_screen);
    return data;
    //return GET_SignalData(this.sample,this.sample+this.samples_per_screen);
  }

  setSample(sample=null,prevent_reload=true){
    if (sample === null){ sample = this.sample;}
    if (this.sample == sample && prevent_reload){return;}
    this.setDisplay(sample, this.get_frame(sample));
  }

  setFrame(frame){
    if (this.frame == frame){return;}
    this.setDisplay(this.get_start_sample(frame), frame);
  }

  setDisplay(sample,frame){
    let is_new_frame = this.frame != frame;

    this.#_sample = sample;
    this.#_frame = frame;
 
    refreshButtons();
    if(is_new_frame){
      drawFrame();
      this.sync_sample();
    }
    this.redrawSample();
    document.getElementById("slider_sample").value = this.sample_ctrl.get_position(this.sample);
  }

  async redrawSample(){
    if (this.#_is_drawing){
      globLog.log('Canvas',"Can't draw sample",this.sample,"since canvas is locked.");
      return false;
    }
    else {
      this.#_is_drawing = true;
      await Promise.allSettled([drawSample(), drawAnno()]);
      this.#_is_drawing = false;
    }
  }

  // Close the tool
  async close_tool(){
    // Prepare backend
    await POST_finish_tool();

    // Refresh page for new content
    location.reload();
  }
}

// ************************ //
//                          //
//      AI Controller       //
//                          //
// ************************ //

class AI_CTRL {
  #running_ = false;

  // last max sample to be checked
  #last_sample = null;

  constructor(delay,running=false){
    this.delay = Math.min(200,delay);
    this.#running_ = running;
    globLog.log('AI',"Task controller delay =",delay);
  }

  resume(){
    globLog.log('AI',"Task controller is running.")
    this.#running_ = true;
    setTimeout(()=>this.step(),0);
  }

  pause(){
    globLog.log('AI',"Task controller stopped.")
    this.#running_ = false;
  }

  get isRunning(){return this.#running_;}

  step(){
    if (!this.isRunning){return;}

    let SPS = globSettings.samples_per_screen;
    let start = Math.max(globSettings.start_sample,this.#last_sample+1);
    let stop = globSettings.stop_sample;

    let s0 = start ;
    let s1 = stop +1;

    
    const [sample, label] = globPred.getFirstInRange(s0,s1);
    globLog.log('AI',"Check preds in range",s0,"-",s1,":",sample,label);

    if (sample !== null){
      
      // Arguments?
      const target_speed = 0.1;
      const constant_time = 1.5;

      const constant_samples = target_speed * constant_time * globSettings.samples_per_frame;
      const target_sample = sample - 0.5 * constant_samples;

      let start_sample = globSettings.sample;

      globLog.log('AI',"Slow down around sample",sample,"to indicate label",label);
      setTimeout(()=>globSettings.speed_ctrl.slow_around(sample,start_sample,target_sample,target_speed,constant_samples),0);   
      console.log("return check");
    }

    this.#last_sample = stop;
    setTimeout(()=>this.step(),this.delay);
  }
}

// ************************ //
//                          //
//          Setup           //
//                          //
// ************************ //

var globSettings = null;
var globLog = null;
var globAnno = null;
var globPred = null;
async function Setup(page="Tool"){
  let _settings = await GET_Settings();
  globLog = new Logger(_settings['log_settings'],_settings['log_path']);
  globLog.log("Setup","Page \""+page+"\" - Loaded Settings:",_settings);
  globSettings = new Settings(
      modus             = _settings['modus'],
      project_name      = _settings['project_name'],

      FPS               = _settings['FPS'], 
      sample_rate       = _settings['sample_rate'], 
      sample_number     = _settings['sample_number'], 
      sample_cur        = _settings['cur_sample'],

      video_name        = _settings['video_name'],
      video_width       = _settings['video_width'],
      video_height      = _settings['video_height'],
      video_fps         = _settings['video_fps'],

      video_offset      = _settings['video_offset'], 
      frame_number      = _settings['frame_number'],

      max_samples       = _settings['max_samples'],
      max_bg_markers    = _settings['max_bg_markers'],
      pred_clear_range  = _settings['pred_clear_range'],
      //pred_threshold  = _settings['pred_threshold'],
      marker_snap_range = _settings['marker_snap_range'],

      buffer_rate       = _settings['buffer_rate'],
      play_speed        = _settings['play_speed'],
      max_play_speed    = _settings['max_play_speed'], 
      refresh_rate      = _settings['refresh_rate'], 
      signal_zoom       = _settings['signal_zoom'],
      zoom_factor       = _settings['zoom_factor'],
      target_seconds    = _settings['target_seconds'],
    );

  if (page=="Tool"){
    let promise_anno = GET_Annotation();

    // Set up AI assistance
    if (globSettings.modus['AI']){
      let _predObj = await GET_Prediction();
      globLog.log('AI',"Support activated");
      globPred = new Predictions(_predObj);
    }
    else {
      globLog.log('AI',"Support not activated");
      globPred = new Predictions();
    }
    
    // Set up existing annotation afterwards remove superflous predictions
    let _annoObj = await promise_anno;
    globAnno = new Annotation(_annoObj,globSettings.sample_number);
    
    await setUI();
    globSettings.setSample(_settings['cur_sample'],prevent_reload=false);
  }
  
  if (page=="Settings")
  {
    setSettingUI();
  }

  if (page=="Logging"){
    setLogSel();
  }

}


// ************************ //
//                          //
//           GET            //
//                          //
// ************************ //

// Get JSON data from Backend
async function GET_JSON(url){
  if (globLog !== null){globLog.log("GET",url);}
  const res = await fetch(url);
  const json = await res.json();
  return await json.data;
}

async function GET_Annotation(){
  return GET_JSON(url_current_labels);
}

async function GET_Prediction(){
  return GET_JSON(url_current_prediction);
}

async function GET_Settings(){
  return GET_JSON(url_play_settings);
}

async function GET_StartSample(frame){
  return GET_JSON(get_start_signal_url(frame));
}

async function GET_SignalData(start,stop,samples){
  let data = await GET_JSON(get_signal_data_url(start,stop,samples));
  var dict = new Object();
  for (const [key, value] of Object.entries(data)) {
    dict[key] = JSON.parse(value);
  }
  return dict;
}


// ************************ //
//                          //
//           POST           //
//                          //
// ************************ //

async function POST_JSON(url, data){
  globLog.log("POST",url,data);
  return fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
}

async function POST_log(txt){
  return fetch(url_logging, {
    method: 'PUT',
    headers: {'Content-Type': 'text/plain'},
    body: txt
  });
}

async function POST_finish_tool(){
  let data = {'type': 'finish_tool'};
  return POST_JSON(url_play_settings, data);
}

async function POST_logSetting(setting,active){
  let data = {'type': 'logSetting', 'setting': setting, 'active': active};
  return POST_JSON(url_play_settings, data);
}

async function POST_setting(setting,value){
  let data = {'type': 'Setting', 'setting': setting, 'value': value};
  return POST_JSON(url_play_settings, data);
}

async function POST_addAnno(sample,label){
  let data = {'target': 'label', 'type': 'Add', 'sample': sample, 'label': label};
  return POST_JSON(url_submit_anno, data);
}

async function POST_delAnno(sample){
  let data = {'target': 'label', 'type': 'Del', 'sample': sample};
  return POST_JSON(url_submit_anno, data);
}

async function POST_addPred(sample,label){
  let data = {'target': 'pred', 'type': 'Add', 'sample': sample, 'label': label};
  return POST_JSON(url_submit_anno, data);
}

async function POST_delPred(sample){
  let data = {'target': 'pred', 'type': 'Del', 'sample': sample};
  return POST_JSON(url_submit_anno, data);
}