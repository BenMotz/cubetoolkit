var setupPage = function() {
    /* 'Derived' from:
     * https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Taking_still_photos
     */
    var streaming     = false,
        video         = document.getElementById('video'),
        canvas        = document.getElementById('canvas'),
        photo         = document.getElementById('photo'),
        capturebutton = document.getElementById('capturebutton'),
        enablecapturebutton = document.getElementById('enablecapturebutton'),
        width = 320,
        height = 0;

    navigator.getMedia = (navigator.getUserMedia ||
                          navigator.webkitGetUserMedia ||
                          navigator.mozGetUserMedia ||
                          navigator.msGetUserMedia);

    function startCapture() {
        navigator.getMedia(
            {
                video: true,
                audio: false
            },
            function(stream) {
                if (navigator.mozGetUserMedia) {
                    video.mozSrcObject = stream;
                } else {
                    var vendorURL = window.URL || window.webkitURL;
                    video.src = vendorURL ? vendorURL.createObjectURL(stream) : stream;
                }
                video.play();
            },
            function(err) {
                console.log("An error occured! " + err);
            }
        );
    }

    video.addEventListener('canplay', onCanplaySetSize, false);

    function onCanplaySetSize() {
        if (!streaming) {
            height = video.videoHeight / (video.videoWidth/width);
            // Some versions of Firefox have a bug where the height can't be
            // read from the video, so make assumptions if this happens:
            if (isNaN(height)) {
              height = width / (4/3);
            }
            video.setAttribute('width', width);
            video.setAttribute('height', height);
            canvas.setAttribute('width', width);
            canvas.setAttribute('height', height);
            streaming = true;
        }
    }

    function takepicture() {
        var capturedimage;
        canvas.width = width;
        canvas.height = height;
        canvas.getContext('2d').drawImage(video, 0, 0, width, height);
        capturedimage = canvas.toDataURL('image/png');
        photo.setAttribute('src', capturedimage);
        document.getElementById('id_vol-image_data').value = capturedimage;
    }

    capturebutton.addEventListener('click', function(ev) {
        takepicture();
        ev.preventDefault();
    }, false);

    enablecapturebutton.addEventListener('click', function(ev) {
        document.getElementById('webcampreview').style.display = 'initial';
        enablecapturebutton.style.display = 'none';
        startCapture();
        ev.preventDefault();
    });

    if (navigator.getMedia != undefined) {
        enablecapturebutton.style.display = 'initial';
    } else {
        console.log("WebRTC not supported");
    }
};
