// ================================
// COMMON FUNCTIONS (NO CHANGE)
// ================================

function updateNavigation() {
    const navMenu = document.querySelector('.nav-menu');
    if (!navMenu) return;

    const logoutLink = navMenu.querySelector('a[href="#logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function (e) {
            e.preventDefault();
            showLogoutConfirmation();
        });
    }
}

function showLogoutConfirmation() {
    const overlay = document.createElement('div');
    overlay.className = 'logout-overlay';

    const popup = document.createElement('div');
    popup.className = 'logout-popup';

    popup.innerHTML = `
        <h3>Confirm Logout</h3>
        <p>Are you sure you want to logout?</p>
        <div class="logout-actions">
            <button id="confirmLogout" class="btn-logout-confirm">Yes, Logout</button>
            <button id="cancelLogout" class="btn-logout-cancel">Cancel</button>
        </div>
    `;

    overlay.appendChild(popup);
    document.body.appendChild(overlay);

    document.getElementById('confirmLogout').addEventListener('click', function() {
        fetch('/logout', { method: 'POST' })
            .then(() => {
                overlay.remove();
                window.location.href = '/login';
            });
    });

    document.getElementById('cancelLogout').addEventListener('click', function() {
        overlay.remove();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    updateNavigation();
    initializePage();
});

function initializePage() {
    const currentPage = window.location.pathname.split('/').pop();

    switch(currentPage) {
        case 'practice':
        case 'practice.html':
        case 'practice?pose=12':
            initPracticePage();
            break;
    }
}

/* ===========================
   ✅ PRACTICE PAGE FINAL LOGIC
=========================== */

function initPracticePage() {

    const startBtn = document.getElementById("startPractice");
    const stopBtn  = document.getElementById("stopPractice");
    const checkBtn = document.getElementById("checkStep");
    const muteBtn  = document.getElementById("muteBtn");
    const stepsContainer = document.getElementById("stepsList");

    let practiceStarted = false;
    let currentStep = 0;
    let detectInterval = null;
    let isMuted = false;
    let steps = [];
    let practiceStartTime = null;
    let sessionAccuracy = 0;
    let detectionCount = 0;

    // ✅ GET STEPS FROM UI
    setTimeout(() => {
        steps = document.querySelectorAll(".step-item");
    }, 1000);

    // ✅ VIDEO + CANVAS (NOT AUTO START)
    const video = document.createElement("video");
    video.setAttribute("autoplay", true);
    video.setAttribute("playsinline", true);
    document.querySelector(".webcam-feed").innerHTML = "";
    document.querySelector(".webcam-feed").appendChild(video);

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // ✅ SPEAK FUNCTION
    function speak(text) {
        if (isMuted || !practiceStarted) return;

        const speech = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(speech);
    }

    // ✅ START PRACTICE (ONLY HERE CAMERA + VOICE ON)
    startBtn.onclick = async () => {
        practiceStarted = true;
        currentStep = 0;
        practiceStartTime = Date.now();
        sessionAccuracy = 0;
        detectionCount = 0;

        startBtn.disabled = true;
        stopBtn.disabled  = false;
        checkBtn.disabled = false;

        speak("Practice started. Perform step one.");

        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;

        highlightStep(currentStep);

        detectInterval = setInterval(sendFrameToBackend, 1200);
    };

    // ✅ STOP PRACTICE (CAMERA + VOICE OFF)
    stopBtn.onclick = async () => {
        practiceStarted = false;

        startBtn.disabled = false;
        stopBtn.disabled  = true;
        checkBtn.disabled = true;

        clearInterval(detectInterval);
        window.speechSynthesis.cancel();

        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }

        removeHighlights();
        
        // Save session to backend
        if (practiceStartTime) {
            const duration = Math.floor((Date.now() - practiceStartTime) / 1000);
            const accuracy = detectionCount > 0 ? Math.round((sessionAccuracy / detectionCount) * 100) : 0;
            
            try {
                await fetch('/save_session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pose_name: selectedPose,
                        accuracy: accuracy,
                        duration: duration
                    })
                });
                console.log('Session saved successfully');
            } catch (error) {
                console.error('Error saving session:', error);
            }
        }
        
        speak("Practice stopped");
    };

    // ✅ CHECK BUTTON
    checkBtn.onclick = () => {
        speak("Checking your posture");
    };

    // ✅ SEND FRAME TO BACKEND
    function sendFrameToBackend() {
        if (!practiceStarted || video.videoWidth === 0) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const imageData = canvas.toDataURL("image/jpeg");

        fetch("/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image: imageData,
                pose: selectedPose,
                step: currentStep + 1
            })
        })
        .then(res => res.json())
        .then(data => {
            // Track accuracy
            detectionCount++;
            if (data.correct === true) {
                sessionAccuracy++;
            }

            if (data.correct === true) {

                speak("Step correct");
                currentStep++;

                if (currentStep < steps.length) {
                    highlightStep(currentStep);
                    speak("Now perform next step");
                } else {
                    speak("Pose completed successfully");
                    stopBtn.click();
                }

            } else {
                speak(data.tip);
            }
        });
    }

    // ✅ STEP HIGHLIGHT UI
    function highlightStep(index) {
        removeHighlights();
        if (steps[index]) steps[index].classList.add("active-step");
    }

    function removeHighlights() {
        steps.forEach(step => step.classList.remove("active-step"));
    }

    // ✅ MUTE
    muteBtn.onclick = () => {
        isMuted = !isMuted;
        muteBtn.innerText = isMuted ? "🔇 Muted" : "🔊 Mute";
        window.speechSynthesis.cancel();
    };
}
