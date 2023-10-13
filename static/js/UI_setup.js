async function setButtons(){

  if (document.getElementById("btn_jmp_start") !== null){
    document.getElementById("img_btn_jmp_start").src = url_btn_img_start;
  }

  document.getElementById("img_btn_prev").src = url_btn_img_prev;
  document.getElementById("img_btn_next").src = url_btn_img_next;
  
  if (document.getElementById("btn_jmp_end") !== null){
    document.getElementById("img_btn_jmp_end").src = url_btn_img_end;
  }

  document.getElementById("img_btn_zoom_in").src = url_btn_img_zoom_in;
  document.getElementById("img_btn_zoom_out").src = url_btn_img_zoom_out;
  
}
  
async function setText(){
  // document.getElementById("text_video_width").innerHTML = globSettings.video_width;
  // document.getElementById("text_video_height").innerHTML = globSettings.video_height;
  // document.getElementById("text_frame_count").innerHTML = globSettings.frame_number;
  // document.getElementById("text_video_fps").innerHTML = globSettings.FPS;
  
  document.getElementById("text_page_header").innerHTML = globSettings.project_name;
  
  if (globSettings.timer !== null){
    globSettings.timer.step();
  }
}
  
async function setCanvas(){
  const div = document.getElementById("canvas_div");
  const canvas = document.getElementById("signal_canvas");
  let width = div.clientWidth;
  let height = 100;

  // console.log(div);
  // console.log(div.clientWidth);
  // console.log(div.clientHeight);

  canvas.width  = width;
  canvas.height = height; 
  canvas.style.width  = width+'px';
  canvas.style.height = height+'px';

  // canvas.addEventListener("click", function(event){
  //   let sample = getCanvasSampleAtClick(event);

  //   selectSampleEvent(sample,event);
  // });

  canvas.addEventListener("mousedown", mouseDown);
  canvas.addEventListener("mousemove", mouseMove);
  canvas.addEventListener("mouseup", mouseUp);

  canvas.addEventListener('contextmenu', function(event) {
    event.preventDefault();
    globLog.log('Mouse','Prevent context menu');

    return false;
  }, false);

  $("#modal_annotation").on('hidden.bs.modal', function(e) {
    globAnno.selectedSample = null;
    globAnno.originalSample = null;
    globSettings.redrawSample();
    let el = document.getElementById("text_new_anno");
    if ( el !== null) { el.value = "";}
  });

  $("#modal_annotation").on('shown.bs.modal', function(e) {
    console.log(globPred.predictionMap)
    let sel_box = document.getElementById("anno_select");
    const sample_cur = globAnno.selectedSample;
    let pred_label = "No Label";
    let pred_src = "no available information";
    if (globAnno.originalSample !== null){
      pred_label = globAnno.getAnno(globAnno.originalSample);
      pred_src = "original sample "+globAnno.originalSample;
    }
    else {
      let label = globAnno.getAnno(sample_cur);
      if ( label !== null){
        pred_label = label;
        pred_src = "existing annotation";
      }
      else if (globPred.length > 0) {
        pred_label = globPred.get_prediction_at(sample_cur);
        pred_src = "closest prediction";
      }
      else {
        let [last_sample, last_label] = globAnno.getLastAnno();
        if (last_label !== null){
          pred_label = last_label;
          pred_src = "last annotation at sample "+last_sample;
        }
      }
    }

    sel_box.value = pred_label;
    globLog.log('AI',"Suggest label",pred_label,"for sample",sample_cur,"based on",pred_src);
    
    // Set focus to selection box
    sel_box.focus();
  });
  
}
   
async function setSlider(){
  const playspeed_slider = document.getElementById("slider_playspeed");
  playspeed_slider.value = globSettings.play_speed_pos;
  playspeed_slider.addEventListener('input', function () {
    globLog.log('Input',"Set playspeed slider to pos",playspeed_slider.value);
    globSettings.play_speed_pos = playspeed_slider.value;
  }, false);
  globLog.log('Setup',"Speed Slider:",playspeed_slider);

  const sample_slider = document.getElementById("slider_sample");
  sample_slider.value = globSettings.sample_ctrl.get_position(globSettings.sample);
  sample_slider.addEventListener('input', function () {
    globLog.log('Input',"Set sample slider to pos",sample_slider.value);
    globSettings.setSample(sample=globSettings.sample_ctrl.get_value(sample_slider.value));
  }, false);
  globLog.log('Setup',"Sample Slider:",sample_slider);
}

async function setInput(){
  const playspeed_input = document.getElementById("input_playspeed");
  playspeed_input.min = globSettings.speed_ctrl.min_play_speed;
  playspeed_input.value = globSettings.speed_ctrl.value;
  playspeed_input.max = globSettings.speed_ctrl.max_play_speed;

  playspeed_input.addEventListener('change', function () {
    globLog.log('Input',"Set playspeed value to sample",playspeed_input.value);
    globSettings.speed_ctrl.set_playspeed_manual(playspeed_input.value);
  }, false);
  globLog.log('Setup',"Speed Input:",playspeed_input);
}

async function setUI(){
  await Promise.allSettled([setCanvas(),setButtons(),setSlider(),setText(),setInput()]);
}

async function setLogSel(){
  const log_settings = globLog.logSettings;
  const form = document.getElementById("logBoxes");
  form.innerHTML = '';
  var counter = 1;
  console.log(log_settings);
  for (const [setting, active] of Object.entries(log_settings)){
    var row = document.createElement('div');
    row.classList.add('row');
    row.classList.add('justify-content-center');
    row.classList.add('mt-2');

    var checkbox = document.createElement('input');
    checkbox.type = "checkbox";
    //checkbox.name = "name";
    checkbox.value = setting;
    checkbox.id = "box"+counter;
    checkbox.checked = active;
    checkbox.classList.add('checkbox_larger');
    checkbox.onchange = function(){globLog.setSetting(this.value,this.checked)};

    var col1 = document.createElement('div');
    col1.classList.add('col-6');
    //col1.classList.add('text-end');
    col1.appendChild(checkbox);
    

    // creating label for checkbox
    var label = document.createElement('h5');
    label.classList.add("checkbox_label");
    label.htmlFor = "box"+counter;
    label.appendChild(document.createTextNode(setting+":"));

    var col2 = document.createElement('div');
    col2.classList.add('col-6');
    col2.classList.add('text-end');
    col2.appendChild(label);

    row.appendChild(col2);
    row.appendChild(col1);

    form.appendChild(row);

    counter += 1;
  }
}

async function setSettingUI(){

  const inputs = document.getElementById("SettingsDiv").getElementsByTagName('input');
  for (const input of inputs){
    globLog.log("Setup","Set",input.id,"("+input.name+") to",globSettings[input.name]);
    input.value = globSettings[input.name];
    input.onchange = function(){globSettings.setSetting(this.name,this.value)};
  }

  const outputs = document.getElementsByClassName("fill_in");
  for (const output of outputs){
    let name = output.id.substring(8);
    globLog.log("Setup","Set",output.id,"("+name+") to",globSettings[name]);
    output.textContent = globSettings[name];
  }

}