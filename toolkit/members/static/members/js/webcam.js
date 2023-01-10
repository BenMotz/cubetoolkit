"use strict";
var setupPage = function() {
    /* 'Derived' from:
     * https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Taking_still_photos
     */
    var streaming        = false;
    var video            = document.getElementById('video');
    var canvas           = document.getElementById('canvas');
    var photo            = document.getElementById('photo');
    var originalPhotoSrc = photo.getAttribute('src');
    var captureButton    = document.getElementById('capturebutton');
    var enableCaptureButton = document.getElementById('enablecapturebutton');
    var width = 320;
    var height = 0;

  if (window.self !== window.top) {
    // If our document is in a frame we won't be able to request permission
    // for camera access.
    console.error("In a frame, cannot use the camera");
    return;
  }

  if (navigator.mediaDevices !== undefined) {
    enablecapturebutton.style.display = 'initial';
  } else {
    console.log("WebRTC not supported");
    return;
  }

  // Fill the photo with an indication that none has been
  // captured.

  function clearphoto() {
    photo.setAttribute("src", originalPhotoSrc);
  }

  // Capture a photo by fetching the current contents of the video
  // and drawing it into a canvas, then converting that to a PNG
  // format data URL. By drawing it on an offscreen canvas and then
  // drawing that to the screen, we can change its size and/or apply
  // other changes before drawing it.

  function takePicture() {
    const context = canvas.getContext("2d");
    if (width && height) {
      canvas.width = width;
      canvas.height = height;
      context.drawImage(video, 0, 0, width, height);

      const data = canvas.toDataURL("image/png");
      photo.setAttribute("src", data);
      document.getElementById('id_vol-image_data').value = data;
    } else {
      clearphoto();
    }
  }

  function startCapture() {
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then((stream) => {
        video.srcObject = stream;
        video.play();
      })
      .catch((err) => {
        console.error(`An error occurred: ${err}`);
      });

    video.addEventListener(
      "canplay",
      (ev) => {
        if (!streaming) {
          height = video.videoHeight / (video.videoWidth / width);

          // Firefox currently has a bug where the height can't be read from
          // the video, so we will make assumptions if this happens.

          if (isNaN(height)) {
            height = width / (4 / 3);
          }

          video.setAttribute("width", width);
          video.setAttribute("height", height);
          canvas.setAttribute("width", width);
          canvas.setAttribute("height", height);
          streaming = true;
        }
      },
      false
    );

    captureButton.addEventListener(
      "click",
      (ev) => {
        takePicture();
        ev.preventDefault();
      },
      false
    );

    clearphoto();
  }

  enablecapturebutton.addEventListener('click', function(ev) {
      ev.preventDefault();
      document.getElementById('webcampreview').style.display = 'initial';
      enablecapturebutton.style.display = 'none';
      startCapture();
  });
};
