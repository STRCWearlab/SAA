function refreshButtons(){

  // Toggle play button
  img = document.getElementById("img_btn_toggle_play");
  if (globSettings.isPlaying){img.src = url_btn_img_pause;}
  else {img.src = url_btn_img_play;}

  // Cancel move button
  btn = document.getElementById("img_btn_cancel");
  if (globSettings.speed_ctrl.move !== null){
    btn.disabled = false;
    btn.src = url_btn_img_cancel;
    //btn.style.display = '';
  }
  else {
    btn.disabled = true;
    btn.src = "";
    //btn.style.display = 'none';
  }

  document.getElementById("btn_prev").disabled = !globSettings.can_move_backwards();
  document.getElementById("btn_toggle_play").disabled = !globSettings.can_move_forwards();
  document.getElementById("btn_next").disabled = !globSettings.can_move_forwards();
  
  let el;
  el = document.getElementById("btn_jmp_start")
  if (el !== null){
    el.disabled = !globSettings.can_move_backwards();
  }
  
  el = document.getElementById("btn_jmp_end")
  if (el !== null){
    el.disabled = !globSettings.can_move_forwards();
  }
  
  document.getElementById("zoom_in").disabled = !globSettings.can_zoom_in;
  document.getElementById("zoom_out").disabled = !globSettings.can_zoom_out;
}

function openCloseDialog(){
  $("#modal_close").modal("show");
}

function closeAnno(){
  $("#modal_annotation").modal("hide");
}

function selectAnno(label){
  if (globAnno.originalSample !== null && globAnno.originalSample != globAnno.selectedSample){
    globAnno.del(globAnno.originalSample);
  }
  globAnno.add(globAnno.selectedSample,label);
  closeAnno();
}

function deleteAnno(){
  globAnno.del(globAnno.selectedSample);
  globAnno.selectedSample = null;
  closeAnno();
}

function selectSampleEvent(sample,event){
  globSettings.stopPlay();
  globAnno.selectedSample = sample;
  globSettings.redrawSample();
  $("#modal_annotation").modal("show");
}

function mouseDown(e){
  if (e.button > 2){
    return;
  }
  else if (globAnno.selectedSample !== null && e.button == 1){
    globAnno.selectedSample = null;
    globAnno.originalSample = null;
  }
  else{
    globSettings.stopPlay();
    let sample = getCanvasSampleAtClick(e);
    if (globAnno.getAnno(sample) !== null){
      globAnno.originalSample = sample;
    }
    globAnno.selectedSample = sample;
  }
  globSettings.redrawSample();
}

function mouseMove(e){
  if (globAnno.selectedSample !== null){
    let sample = getCanvasSample(e);
    globAnno.selectedSample = sample;
    globSettings.redrawSample();
  }
}

function mouseUp(e){
  if (e.button == 0){
    let sample = getCanvasSampleAtClick(e);
    globAnno.selectedSample = sample;
    if( globAnno.originalSample===null || globAnno.originalSample == sample ){
      $("#modal_annotation").modal("show");
    }
    else {
      globAnno.add(sample, globAnno.getAnno(globAnno.originalSample));
      globAnno.del(globAnno.originalSample);
      globAnno.selectedSample = null;
      globAnno.originalSample = null;
    }
  }
  // else if (e.button == 1){
  //   globAnno.selectedSample = null;
  //   globAnno.originalSample = null;
  // }
  else if (e.button == 2){
    let sample = getCanvasSampleAtClick(e);
    globAnno.del(sample);
    globPred.del(sample);
    globAnno.selectedSample = null;
    globAnno.originalSample = null;

  }
  globSettings.redrawSample();
}