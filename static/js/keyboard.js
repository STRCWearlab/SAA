document.addEventListener('keydown', (event) => {

  // Normal tool screen
  if (!$("#modal_annotation").hasClass('show')) {

    // Backwards hotkey
    if (event.code == "ArrowLeft") {
      globLog.log('Hotkey',event.code);
      globSettings.movePrev();
    }

    // Toogle play hotkey
    else if (event.code == "Space") {
      // remove focus to prevent strange interactions
      document.activeElement.blur()

      globLog.log('Hotkey',event.code);
      globSettings.togglePlay("Space");
    }

    // Forwards hotkey
    else if (event.code == "ArrowRight") {
      globLog.log('Hotkey',event.code);
      globSettings.moveNext();
    }

    // Skip current prediction
    if (event.code == "Escape"){
      globLog.log('Hotkey',event.code);
      globSettings.cancel_move(del_pred=false);
    }

    // Remove current prediction
    if (event.code == "Delete"){
      globLog.log('Hotkey',event.code);
      globSettings.cancel_move(del_pred=true);
    }
  }

  // Annotation screen active
  else if ($("#modal_annotation").hasClass('show')) {

    // Confirm annotation selection
    if (event.code == "Enter") {
      globLog.log('Hotkey',event.code);
      if (document.activeElement.id == "anno_select"){
        selectAnno($('#anno_select option:selected').val());
      }
      else if (document.activeElement.id == "text_new_anno"){
        selectAnno($('#text_new_anno').val());
      }
    }

    // Remove current annotation
    if (event.code == "Delete"){
      globLog.log('Hotkey',event.code);
      deleteAnno();
    }

  }

}, false);