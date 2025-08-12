const canvas = document.getElementById('drawingCanvas');
const preview = document.getElementById("gif-preview")
const ctx = canvas.getContext('2d');
const clearButton = document.getElementById('clear-canvas');
const colorPicker = document.getElementById('color-picker');
const saveFrame = document.getElementById("save-frame")
const animationDelaySlider = document.getElementById("anim-delay")
const clearSavedFrames = document.getElementById("clear-saved-frames")
const form = document.getElementById("signup-form")
const csrfElement = document.getElementById("csrf_token");


canvas.width = 50;
canvas.height = 50;

let frames = Array();

let drawing = false;
let currentColor = colorPicker.value;

canvas.addEventListener('mousedown', () => drawing = true);
canvas.addEventListener('mousedown', draw);
canvas.addEventListener('mouseup', () => drawing = false);
canvas.addEventListener('mousemove', draw);

colorPicker.addEventListener('input', (e) => currentColor = e.target.value);
clearButton.addEventListener('click', clear)
saveFrame.addEventListener('click', save)
animationDelaySlider.addEventListener('input', restartAnimation);
clearSavedFrames.addEventListener("click", clearFrames)

form.addEventListener("submit", sendFrames)

function sendFrames(event) {
    event.preventDefault();

    const formData = new FormData(form);
    const jsonData = {};

    formData.forEach((value, key) => {
        jsonData[key] = value;
    });

    jsonData.frames = frames;
    jsonData.animSpeed = animationDelaySlider.value
    console.log(JSON.stringify(jsonData))
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            return response.json();
        } else {
            return response.text().then(text => {
                throw new Error(text);
            });
        }
    })
    .then(data => {
        console.log('Success:', data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred: ' + error.message);
    });
}

function clearFrames() {
    if (frames.length > 0) {
        frames = Array()
    }
    for (const child of preview.children) {
        if (child.className === "img-container") {
            preview.removeChild(child)
        }
    }
}

function restartAnimation() {
    if (animationInterval) {
        clearInterval(animationInterval);
        startAnimation();
    }
}

function clear() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}


function draw(event) {
    if (!drawing) return;

    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / (rect.width / canvas.width));
    const y = Math.floor((event.clientY - rect.top) / (rect.height / canvas.height));

    // Snap to the nearest block
    const snappedX = Math.floor(x / 5) * 5;
    const snappedY = Math.floor(y / 5) * 5;

    ctx.fillStyle = currentColor;
    ctx.fillRect(snappedX, snappedY, 5, 5); // Fill a 5x5 block
}


let currentFrameIndex = 0;
let animationInterval;

function startAnimation() {
    const timeout = (Number(animationDelaySlider.value) / 100 ) * 1000;

    if (frames.length === 0) return;

    if (animationInterval) clearInterval(animationInterval);

    animationInterval = setInterval(() => {
        const imgContainer = document.querySelector('.img-container');
        if (!imgContainer) return;

        const img = imgContainer.querySelector('img');
        if (!img) return;

        img.src = frames[currentFrameIndex];
        currentFrameIndex = (currentFrameIndex + 1) % frames.length;
    }, timeout);
}

function save() {
    if (frames.length >= 10) {
        alert('You have reached the maximum frame limit of 10.');
        return;
    }
    const frame = canvas.toDataURL(); // b64 string
    frames.push(frame);

    const imgContainer = document.querySelector('.img-container');

    if (!imgContainer) {
        const newImgContainer = document.createElement("div");
        newImgContainer.className = "img-container";
        newImgContainer.height = 250;
        newImgContainer.width = 250;
        preview.appendChild(newImgContainer);

        const img = document.createElement('img');
        img.src = frame;
        img.height = 250;
        img.width = 250;
        img.style.imageRendering = "pixelated";
        img.style.opacity = "0";
        img.style.transition = "opacity 0.5s ease";
        newImgContainer.appendChild(img);

        setTimeout(() => {
            img.style.opacity = "1";
        }, 50);
    }

    clear();
    startAnimation();
}
