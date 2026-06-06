// i18n.js

const LANGUAGES = {
    en: {
        code: "en-US",
        messages: {
            start: "Start the pose",
            correct: "Good job, pose is correct",
            wrong: "Adjust your posture",
            completed: "Pose completed successfully"
        }
    },
    hi: {
        code: "hi-IN",
        messages: {
            start: "आसन शुरू करें",
            correct: "बहुत बढ़िया, आसन सही है",
            wrong: "अपनी मुद्रा सुधारें",
            completed: "आसन सफलतापूर्वक पूरा हुआ"
        }
    },
    mr: {
        code: "mr-IN",
        messages: {
            start: "आसन सुरू करा",
            correct: "छान, आसन योग्य आहे",
            wrong: "आपली मुद्रा सुधारा",
            completed: "आसन यशस्वीपणे पूर्ण झाले"
        }
    }
};

let currentLang = "en";

function setLanguage(lang) {
    currentLang = lang;
}

function speakMessage(key) {
    const msg = LANGUAGES[currentLang].messages[key];
    if (!msg) return;

    const utterance = new SpeechSynthesisUtterance(msg);
    utterance.lang = LANGUAGES[currentLang].code;
    utterance.rate = 0.95;     // fluent speed
    utterance.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

function getMessage(key) {
    return LANGUAGES[currentLang].messages[key];
}
