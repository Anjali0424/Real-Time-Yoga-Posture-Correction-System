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
   ✅ STEP-BY-STEP VALIDATION PRACTICE LOGIC
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
    let isCheckingStep = false; // Prevent multiple checks at once
    let stepsPracticeData = []; // Store step texts for speaking

    // ✅ GET STEPS FROM UI
    setTimeout(() => {
        steps = document.querySelectorAll(".step-item");
        // Extract step text for speaking
        steps.forEach(step => {
            const stepText = step.querySelector(".step-text")?.innerText || "Unknown step";
            stepsPracticeData.push(stepText);
        });
    }, 1000);

    // ✅ VIDEO + CANVAS (NOT AUTO START)
    const video = document.createElement("video");
    video.setAttribute("autoplay", true);
    video.setAttribute("playsinline", true);
    document.querySelector(".webcam-feed").innerHTML = "";
    document.querySelector(".webcam-feed").appendChild(video);

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // ✅ SPEAK FUNCTION (with language support)
    function speak(text) {
        if (isMuted || !practiceStarted) return;

        const speech = new SpeechSynthesisUtterance(text);
        
        // Detect language from practice language selector
        const languageSelect = document.getElementById("practiceLanguage");
        const currentLanguage = languageSelect?.value || "English";
        
        if (currentLanguage === "Hindi") speech.lang = "hi-IN";
        else if (currentLanguage === "Marathi") speech.lang = "mr-IN";
        else speech.lang = "en-US";

        window.speechSynthesis.speak(speech);
    }

    // ✅ START PRACTICE (CAMERA + VOICE ON, SPEAK FIRST STEP)
    startBtn.onclick = async () => {
        try {
            practiceStarted = true;
            currentStep = 0;
            practiceStartTime = Date.now();
            sessionAccuracy = 0;
            detectionCount = 0;
            isCheckingStep = false;

            startBtn.disabled = true;
            stopBtn.disabled  = false;
            checkBtn.disabled = false;

            // Get webcam access
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            // Highlight first step
            highlightStep(currentStep);

            // Speak first step instructions
            if (stepsPracticeData[currentStep]) {
                speak("Practice started. Here is step one:");
                setTimeout(() => {
                    speak(stepsPracticeData[currentStep]);
                }, 500);
            }

            // Start continuous auto-detection (every 1.2 seconds)
            detectInterval = setInterval(autoDetectPose, 1200);
        } catch (error) {
            alert("Unable to access webcam. Please check permissions.");
            startBtn.disabled = false;
            practiceStarted = false;
        }
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

    // ✅ MANUAL CHECK BUTTON (for when hands are busy)
    checkBtn.onclick = () => {
        if (!practiceStarted || isCheckingStep) return;
        checkCurrentStep();
    };

    // ✅ AUTO-DETECT POSE (runs continuously every 1.2s)
    function autoDetectPose() {
        if (!practiceStarted || video.videoWidth === 0 || isCheckingStep) return;

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
            detectionCount++;
            
            // Check if pose is correct
            if (data.correct === true) {
                sessionAccuracy++;
                handleStepSuccess();
            } else {
                // Pose is wrong - could show subtle feedback without stopping
                // Optional: log failures for debugging
                console.log("Pose incorrect for step", currentStep + 1, ":", data.tip);
            }
        })
        .catch(error => console.error("Detection error:", error));
    }

    // ✅ MANUAL CHECK CURRENT STEP (triggered by button or auto-detect on success)
    function checkCurrentStep() {
        if (!practiceStarted || isCheckingStep) return;
        
        isCheckingStep = true;
        
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
            detectionCount++;
            
            if (data.correct === true) {
                sessionAccuracy++;
                handleStepSuccess();
            } else {
                handleStepFailure(data.tip);
            }
            
            isCheckingStep = false;
        })
        .catch(error => {
            console.error("Check error:", error);
            isCheckingStep = false;
        });
    }

    // ✅ HANDLE STEP SUCCESS
    function handleStepSuccess() {
        const stepNumber = currentStep + 1;
        const successMessage = `Step ${stepNumber} is correct! Excellent work!`;

        // Show alert
        alert(successMessage);
        
        // Speak success message
        speak(successMessage);

        currentStep++;

        // Check if all steps completed
        if (currentStep < steps.length) {
            // Speak next step after a short delay
            setTimeout(() => {
                highlightStep(currentStep);
                speak("Now perform step " + (currentStep + 1) + ":");
                setTimeout(() => {
                    speak(stepsPracticeData[currentStep]);
                }, 500);
            }, 1000);
        } else {
            // All steps completed!
            speak("Congratulations! You have successfully completed all steps of the pose.");
            alert("Congratulations! You have successfully completed " + selectedPose + "!");
            
            // Auto-stop practice
            setTimeout(() => {
                stopBtn.click();
            }, 2000);
        }
    }

    // ✅ HANDLE STEP FAILURE
    function handleStepFailure(feedback) {
        const stepNumber = currentStep + 1;
        const failureMessage = `Step ${stepNumber} needs correction. ${feedback}`;

        // Show alert
        alert(failureMessage);
        
        // Speak failure feedback
        speak(failureMessage);
        
        // Stay on current step - user must retry
        console.log("User must retry step", stepNumber);
    }

    // ✅ STEP HIGHLIGHT UI
    function highlightStep(index) {
        removeHighlights();
        if (steps[index]) {
            steps[index].classList.add("active-step");
        }
    }

    function removeHighlights() {
        steps.forEach(step => step.classList.remove("active-step"));
    }

    // ✅ MUTE BUTTON
    muteBtn.onclick = () => {
        isMuted = !isMuted;
        muteBtn.innerText = isMuted ? "🔇 Muted" : "🔊 Mute";
        window.speechSynthesis.cancel();
    };
}
