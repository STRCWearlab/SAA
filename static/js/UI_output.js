// Colour palette by B. Wong - https://doi.org/10.1038/nmeth.1618

const color_palette = {
  "Black":            "rgb(  0,   0,   0)",
  "Gray":             "rgb(128, 128, 128)",
  "Orange":           "rgb(230, 159,   0)",
  "Sky Blue":         "rgb( 86, 180, 233)",
  "Bluish Green":     "rgb(  0, 158, 115)",
  "Yellow":           "rgb(240, 228,  66)",
  "Blue":             "rgb(  0, 114, 178)",
  "Vermillion":       "rgb(213,  94,   0)",
  "Reddish Purple":   "rgb(204, 121, 167)",
};

const color_list = ["Orange", "Sky Blue", "Vermillion", "Bluish Green", "Reddish Purple", "Blue", "Yellow"];

// ************************ //
//                          //
//      Display Stream      //
//                          //
// ************************ //

function getCanvasSample(event){
  const canvas = document.getElementById("signal_canvas");
  let rect = canvas.getBoundingClientRect();

  let x = event.clientX - rect.left;

  // Calculate sample
  let click_sample = Math.round( (globSettings.samples_per_screen-1) * x/canvas.width );
  click_sample = Math.max(click_sample,1);
  click_sample = Math.min(click_sample,globSettings.samples_per_screen-2);
  return Math.round(click_sample+globSettings.start_sample);
}

function getCanvasSampleAtClick(event){
  const canvas = document.getElementById("signal_canvas");
  let rect = canvas.getBoundingClientRect();

  let x = event.clientX - rect.left;
  
  // Calculate sample
  let click_sample = Math.round( (globSettings.samples_per_screen-1) * x/canvas.width );
  click_sample = Math.max(click_sample,1);
  click_sample = Math.min(click_sample,globSettings.samples_per_screen-2);
  var target_sample = Math.round(click_sample+globSettings.start_sample);

  // Check if there are annotation marker to snap to
  let x0 = x - globSettings.marker_snap_range;
  let x1 = x + globSettings.marker_snap_range;

  let start = Math.floor((globSettings.samples_per_screen-1) * x0/canvas.width + globSettings.start_sample);
  let end =  Math.ceil((globSettings.samples_per_screen-1) * x1/canvas.width + globSettings.start_sample);

  let min_dis = Infinity;

  const annos = globAnno.getRange(start, end);
  globLog.log('Mouse',"Click at",x,"("+target_sample+")","Annos in click range",x0,"("+start+")","to",x1,"("+end+")",":",annos);

  if (annos.length > 0)
  {
    for (const [sample, label] of annos.entries()){
      let dis = Math.abs(click_sample-sample)
      if (dis<min_dis)
      {
        min_dis = dis;
        target_sample = sample;
        globLog.log('Canvas',"Found closer annotation at",sample);
      }
    }
  }

  const preds = globPred.getRange(start, end);
  if (preds.length > 0)
  {
    // console.log("Found Samples:");
    for (const [sample, label] of preds.entries()){
      let dis = Math.abs(click_sample-sample)
      if (dis<min_dis)
      {
        min_dis = dis;
        target_sample = sample;
        globLog.log('Canvas',"Found closer prediction at",sample);
      }
    }
  }



  // console.log(event);
  // console.log(x,x/canvas.width);
  // console.log((globSettings.samples_per_screen) * x/canvas.width);

  return target_sample;
}

async function drawSample() {
  let promise = globSettings.get_signal_data();

  //console.log("Promise:",promise);
  globLog.log('Canvas',"Frame: "+globSettings.frame+" Sample: "+globSettings.sample+" Can move prev: "+globSettings.can_move_backwards()+" Can move next: "+globSettings.can_move_forwards());

  const canvas = document.getElementById("signal_canvas");
  const ctx = canvas.getContext("2d");

  const lineWidth = 1;
  const signalWidth = 1;
  const markerWidth = 2;
  const bgWidth = 0.25;

  const start_sample = globSettings.start_sample;
  const stop_sample = globSettings.stop_sample;
  const selectedSample = globAnno.selectedSample;
  const SPS = stop_sample - start_sample;

  globLog.log('Canvas',canvas);
  globLog.log('Canvas','Start:',start_sample,"Stop:",stop_sample,"Selected:",selectedSample);
  //console.log("Width:",canvas.width,"Height:",canvas.height);
  //console.log("CTX:",ctx);


  // Fill Background
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);


  
  // Background current frame
  let frame = globSettings.frame;
  
  let frame_sample_0 = Math.max(globSettings.get_start_sample(frame),start_sample);
  let frame_sample_1 = Math.min(globSettings.get_start_sample(frame+1),stop_sample);

  let frame_x0 = canvas.width * (frame_sample_0 - start_sample) / (SPS-1);
  let frame_x1 = canvas.width * (frame_sample_1 - start_sample) / (SPS-1);
  

  ctx.fillStyle = "#CCCCCC";
  ctx.fillRect(frame_x0, 0, frame_x1-frame_x0, canvas.height);

  // Horizontal Line
  ctx.beginPath();
  ctx.moveTo(0, canvas.height/2);
  ctx.lineTo(canvas.width, canvas.height/2);
  ctx.lineWidth = lineWidth;
  ctx.strokeStyle = 'black';
  ctx.stroke();

  // Grid
  const X = [...Array(SPS).keys()].map(i => i*canvas.width/(SPS-1));
  const grid_step = Math.max(1,parseInt(SPS/globSettings.max_bg_markers));
  ctx.beginPath();
  ctx.font = "8px Arial";
  ctx.fillStyle= "black";
  X.forEach(function (x, index) {
    if (index%grid_step == 0){
      let time_stamp = globSettings.get_time_stamp_str(start_sample+index);
      //globLog.log('Canvas',"Draw grid line at",x,"index:",index,"time stamp:",time_stamp,"sample:",start_sample+index);
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.fillText(time_stamp, x+2, 10);
    }
    
  });
  ctx.lineWidth = bgWidth;
  ctx.strokeStyle = 'black';
  ctx.stroke();
  
  // Next frame
  const startSamples = globSettings.get_start_samples_in_range(start_sample, stop_sample);
  ctx.beginPath();
  startSamples.forEach(function (sample, index) {
    let x = canvas.width*(sample - start_sample)/(SPS-1);
    globLog.log('Canvas',"Frame sample",sample,"x:",x);
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
  });
  ctx.lineWidth = lineWidth;
  ctx.strokeStyle = 'black';
  ctx.stroke();

  // Signal Data
  const data = await promise;

  if (data===null){
    globLog.log("Error","No data received! Promise:",promise);
  }
 
  var color_idx = 0;
  for (let name of Object.keys(data)){
    //console.log("Draw signal",name,"with color",color_list[color_idx],"(",color_palette[color_list[color_idx]],")");
    let Y = data[name].map(i => i * canvas.height);
    //console.log(Y);
    var idx = 1;

    ctx.beginPath();
    ctx.moveTo(X[0], Y[0]);
    while(idx < SPS){
      ctx.lineTo(X[idx], Y[idx]);
      idx += 1;
    }
    ctx.lineWidth = signalWidth;
    ctx.strokeStyle = color_palette[color_list[color_idx]];
    ctx.stroke();

    color_idx += 1;
  }

  // Original marker
  if (globAnno.originalSample !== null){
    let sample = globAnno.originalSample;
    let x = canvas.width * (sample - start_sample) / (SPS-1);
    globLog.log('Canvas',"Draw origin marker at Sample:",sample,"X:",x);
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.lineWidth = markerWidth;
    ctx.strokeStyle = color_palette["Gray"];
    ctx.stroke();
  }

  // Suggested marker
  const preds = globPred.getRange(start_sample, start_sample+SPS);
  ctx.beginPath();
  for (const [sample, label] of preds.entries()){
    let x = canvas.width * (sample - start_sample) / (SPS-1);
    globLog.log('Canvas',"Draw prediction marker at Sample:",sample,"X:",x,"Label:",label);
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
  }
  ctx.lineWidth = markerWidth;
  ctx.strokeStyle = color_palette["Orange"];
  ctx.stroke();


  // Selected marker
  if (selectedSample !== null){
    let x = canvas.width * (selectedSample - start_sample) / (SPS-1);
    
    globLog.log('Canvas',"Draw selected sample",selectedSample,"at X =",x);

    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.lineWidth = markerWidth*3;
    ctx.strokeStyle = color_palette["Gray"];
    ctx.shadowBlur = markerWidth*3;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.lineWidth = markerWidth*1.5;
    ctx.strokeStyle = color_palette["Blue"];
    ctx.stroke();
  }


  // Annotation marker
  const annos = globAnno.getRange(start_sample, start_sample+SPS);
  ctx.beginPath();
  for (const [sample, label] of annos.entries()){
    if (sample == globAnno.originalSample){
      continue;
    }
    let x = canvas.width * (sample - start_sample) / (SPS-1);
    globLog.log('Canvas',"Draw anno marker at Sample:",sample,"X:",x,"Label:",label);
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
  }
  ctx.lineWidth = markerWidth;
  ctx.strokeStyle = color_palette["Blue"];
  ctx.stroke();

}


async function drawFrame() {
  globLog.log('Filler');
  globLog.log('Video', "Set new frame",globSettings.frame);
  //globLog.log('Video',"setFrame Settings: ",globSettings);

  const elements = document.querySelectorAll(".video_frame");
  elements[0].src = get_video_url(globSettings.frame-1);
  elements[1].src = get_video_url(globSettings.frame);
  elements[2].src = get_video_url(globSettings.frame+1);
  // document.getElementById("text_frame_current").innerHTML = globSettings.frame;
}


function UpdateStream(){
  let startTime = new Date();

  globLog.log('Filler');
  //globLog.log('Playback',"UpdateStream Settings: ",globSettings);
  
  if (globSettings.isPlaying) {
    let newSample = globSettings.sample+globSettings.samples_per_tick

    if (newSample>=globSettings.last_sample){
      globSettings.stopPlay();
    }

    globSettings.setSample(newSample);

    let timeDiff = new Date() - startTime; //in ms
    let delay = globSettings.delay-timeDiff;
    if (delay < 0){
      globLog.log('Playback',"Warning: refresh rate too high, lagging",delay,"behind!")
      delay = 0;
    }
    //let delay = globSettings.delay;

    globLog.log('Playback',"UI Frame:",globSettings.frame,
              "UI Sample:",globSettings.sample,
              "Samples per Tick:",globSettings.samples_per_tick,
              "Total delay",globSettings.delay,
              "Remaining delay:",delay,
              "isPlaying:",globSettings.isPlaying,
            );
    
    setTimeout(()=>UpdateStream(),delay);
    //globLog.log('Playback',"Post log Test for Sample:",globSettings.sample);
  }
};

// ************************ //
//                          //
//        Annotation        //
//                          //
// ************************ //

function drawAnno(){
  const SPS = globSettings.stop_sample - globSettings.start_sample;
  // console.log(typeof globSettings.sample);
  // console.log(typeof globSettings['samples_per_frame']);
  // console.log(typeof samples_per_frame);
  // console.log(typeof (globSettings.sample+samples_per_frame));
  // console.log("Stop: "+Math.min(sample_number,(globSettings.sample+samples_per_frame))+" ("+(globSettings.sample+samples_per_frame)+"/"+sample_number+")");
  const annos = globAnno.getRange(globSettings.start_sample, globSettings.stop_sample-1, add_init=true, set_stop=true);

  const container = document.getElementById("box_annotations");
  container.innerHTML = '';   // clear previous annotations

  globLog.log('Canvas',"drawAnno between",globSettings.start_sample,"and",globSettings.stop_sample,annos);

  let last = null;
  for (const [sample, label] of annos.entries()){

    //console.log(sample, label, last);

    // Label annotations
    if (last !== null && last[1] !== '_none_'){
      let start_sample = Math.max(last[0],globSettings.start_sample);
      let start = (start_sample - globSettings.start_sample) / (SPS-1);

      let length = sample - start_sample;
      let width = length / (SPS-1);
      globLog.log('Canvas',"Draw anno box start sample",last[0],"(",start_sample,")",
                  "end sample:",sample,
                  "label:",last[1],
                  "length:",length,
                  "start: ",start,
                  "width: ",width);

      var box = document.createElement('div');
      box.style.position = 'absolute';
      //box.style.top = '100%';
      box.style.left = (100*start)+'%';
      box.style.width = (100*width)+'%';
      box.style.height = '100%';
      //box.style.color = 'black';
      box.style.background = 'lightblue'; // custom colour?
      box.style.padding = '0px';

      box.style.borderWidth = '1px';
      box.style.borderStyle = "solid";
      box.style.borderColor = "black";

      box.innerText = last[1];
      box.class = 'col text-center align-middle';

      box.setAttribute("start_sample", last[0])

      box.addEventListener("click", function(event){selectSampleEvent(parseInt(event.target.getAttribute("start_sample")),event);});

      container.appendChild(box);
    }

  // New last
  last = [sample, label];
  }
}