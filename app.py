from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from backend.db import get_db_connection
import tensorflow as tf
import tensorflow_hub as hub
import cv2
import numpy as np
import base64
from functools import wraps
from pose_logic import validate_pose


# -------------------- FLASK APP --------------------
app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend",
    static_url_path=""
)

app.secret_key = "yoga_secret_key"


# -------------------- LOGIN REQUIRED DECORATOR --------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# -------------------- LOGOUT ROUTE --------------------
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# -------------------- MOVENET LOADING --------------------
movenet = hub.load(
    "https://tfhub.dev/google/movenet/singlepose/thunder/3"
).signatures["serving_default"]


def get_keypoints_from_movenet(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (256, 256))
    img = img.astype(np.int32)
    img = np.expand_dims(img, axis=0)

    outputs = movenet(tf.constant(img))
    keypoints = outputs["output_0"].numpy()[0][0]

    names = [
        "nose","left_eye","right_eye","left_ear","right_ear",
        "left_shoulder","right_shoulder",
        "left_elbow","right_elbow",
        "left_wrist","right_wrist",
        "left_hip","right_hip",
        "left_knee","right_knee",
        "left_ankle","right_ankle"
    ]

    formatted = []
    for i, name in enumerate(names):
        formatted.append({
            "name": name,
            "x": float(keypoints[i][1]),
            "y": float(keypoints[i][0])
        })

    return formatted


# -------------------- AI POSE DETECTION --------------------
@app.route("/detect", methods=["POST"])
@login_required
def detect_pose_endpoint():
    """
    POST /detect
    Detects if user's pose matches the target pose using MoveNet + pose_logic.
    
    Request JSON:
    {
        "image": "data:image/jpeg;base64,...",
        "pose": "Lotus Pose",  // or any of the 22 supported poses
        "step": 1  // optional: step number for step-wise checks
    }
    
    Response JSON:
    {
        "pose": "Lotus Pose",
        "correct": true/false,
        "tip": "Feedback message"
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON payload"}), 400
        
        image_data = data.get("image")
        pose_name = data.get("pose")
        step_no = data.get("step")
        if not step_no or step_no < 1:
            step_no = 1
        

        
        if not image_data or not pose_name:
            return jsonify({"error": "Missing 'image' or 'pose' in request"}), 400
        
        # Decode base64 image
        try:
            encoded = image_data.split(",")[1] if "," in image_data else image_data
            decoded = base64.b64decode(encoded)
            np_img = np.frombuffer(decoded, np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({"error": "Failed to decode image"}), 400
        except Exception as e:
            return jsonify({"error": f"Image decoding error: {str(e)}"}), 400
        
        # Get keypoints from MoveNet
        try:
            keypoints = get_keypoints_from_movenet(frame)
        except Exception as e:
            return jsonify({"error": f"MoveNet error: {str(e)}"}), 500
        
        # Detect pose using pose_logic.detect_pose()
        result = validate_pose(pose_name, step_no, keypoints)

        
        return jsonify({
            "pose": pose_name,
            "step": step_no,
            "correct": result["correct"],
            "tip": result["tip"]
        })
    
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# -------------------- DB TEST --------------------
@app.route("/db_test")
@login_required
def db_test():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    return str(cursor.fetchall())


# -------------------- DEBUG ROUTE --------------------
@app.route("/voice_debug")
def voice_debug():
    """Debug page to check available system voices"""
    return render_template("voice_debug.html")


# -------------------- PUBLIC ROUTES --------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, username, password FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")

        return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        bio = request.form.get("bio", "")

        profile_image = request.files.get("profile_image")
        image_filename = None

        if profile_image:
            image_filename = f"{email}_profile.jpg"
            profile_image.save("frontend/uploads/" + image_filename)

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO users (username, email, password, bio, profile_image)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, password, bio, image_filename))

        db.commit()
        return redirect("/login")

    return render_template("signup.html")


# -------------------- PROTECTED ROUTES --------------------
@app.route("/dashboard")
@login_required
def dashboard_page():
    user_id = session.get("user_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, bio, profile_image
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("dashboard.html", user=user)



@app.route("/practice")
@login_required
def practice_page():
    return render_template("practice.html")


@app.route("/poses")
@login_required
def poses_page():
    return render_template("poses.html")


@app.route("/pose_detail")
@login_required
def pose_detail_page():
    return render_template("pose_detail.html")


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


@app.route("/about")
@login_required
def about_page():
    return render_template("about.html")


# -------------------- STEPS API --------------------
@app.route("/get_steps")
@login_required
def get_steps():
    pose_name = request.args.get("pose")
    language = request.args.get("lang")

    # Language mapping: Convert language names to database codes
    language_map = {
        "English": "en",
        "Hindi": "hi",
        "Marathi": "mr",
        "Kannada": "kn",
        # Also accept codes directly
        "en": "en",
        "hi": "hi",
        "mr": "mr",
        "kn": "kn"
    }
    
    # Get the language code
    language_code = language_map.get(language, "en")  # Default to English if not found

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT step_number, step_text 
        FROM pose_steps 
        WHERE pose_name=%s AND language_code=%s 
        ORDER BY step_number
    """, (pose_name, language_code))

    return jsonify(cursor.fetchall())

@app.route("/user_profile")
@login_required
def user_profile():
    user_id = session.get("user_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, bio, profile_image
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()
    db.close()

    return jsonify(user)


# -------------------- SESSION ANALYTICS --------------------
@app.route("/save_session", methods=["POST"])
@login_required
def save_session():
    """Save practice session to database"""
    data = request.json
    user_id = session.get("user_id")
    pose_name = data.get("pose_name")
    accuracy = data.get("accuracy")
    duration = data.get("duration")  # in seconds

    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO sessions (user_id, pose_name, accuracy, duration, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
        """, (user_id, pose_name, accuracy, duration))
        db.commit()
        return jsonify({"status": "success", "message": "Session saved"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route("/user_stats", methods=["GET"])
@login_required
def user_stats():
    """Get user analytics: streak, accuracy, total sessions"""
    user_id = session.get("user_id")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Total sessions
        cursor.execute("SELECT COUNT(*) as total_sessions FROM sessions WHERE user_id=%s", (user_id,))
        total_sessions = cursor.fetchone()["total_sessions"] or 0
        
        # Average accuracy
        cursor.execute(
            "SELECT AVG(accuracy) as avg_accuracy FROM sessions WHERE user_id=%s AND accuracy IS NOT NULL",
            (user_id,)
        )
        avg_accuracy = cursor.fetchone()["avg_accuracy"] or 0
        avg_accuracy = round(float(avg_accuracy), 1)
        
        # Total duration
        cursor.execute(
            "SELECT SUM(duration) as total_duration FROM sessions WHERE user_id=%s",
            (user_id,)
        )
        total_duration = cursor.fetchone()["total_duration"] or 0
        
        # Unique poses practiced
        cursor.execute(
            "SELECT COUNT(DISTINCT pose_name) as unique_poses FROM sessions WHERE user_id=%s",
            (user_id,)
        )
        unique_poses = cursor.fetchone()["unique_poses"] or 0
        
        # Current streak (days with at least one session)
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(timestamp)) as streak_days
            FROM sessions 
            WHERE user_id=%s 
            AND DATE(timestamp) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """, (user_id,))
        streak_days = cursor.fetchone()["streak_days"] or 0
        
        # Recent sessions (last 5)
        cursor.execute("""
            SELECT pose_name, accuracy, duration, DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i') as formatted_time
            FROM sessions 
            WHERE user_id=%s 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (user_id,))
        recent_sessions = cursor.fetchall()
        
        return jsonify({
            "total_sessions": total_sessions,
            "avg_accuracy": avg_accuracy,
            "total_duration_seconds": total_duration,
            "unique_poses": unique_poses,   
            "current_streak": streak_days,
            "recent_sessions": recent_sessions
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()


# -------------------- USER SETTINGS --------------------
@app.route("/save_settings", methods=["POST"])
@login_required
def save_settings():
    """Save user preferences to database"""
    data = request.json
    user_id = session.get("user_id")
    
    theme = data.get("theme", "light")
    language = data.get("language", "en")
    difficulty = data.get("difficulty", "beginner")
    session_length = data.get("session_length", 15)
    mute_sound = data.get("mute_sound", False)
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Check if settings exist
        cursor.execute("SELECT id FROM user_settings WHERE user_id=%s", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing
            cursor.execute("""
                UPDATE user_settings 
                SET theme=%s, language=%s, difficulty=%s, session_length=%s, mute_sound=%s
                WHERE user_id=%s
            """, (theme, language, difficulty, session_length, mute_sound, user_id))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO user_settings (user_id, theme, language, difficulty, session_length, mute_sound)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, theme, language, difficulty, session_length, mute_sound))
        
        db.commit()
        return jsonify({"status": "success", "message": "Settings saved"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route("/get_settings", methods=["GET"])
@login_required
def get_settings():
    """Fetch user preferences from database"""
    user_id = session.get("user_id")
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT theme, language, difficulty, session_length, mute_sound 
            FROM user_settings 
            WHERE user_id=%s
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return jsonify(result)
        else:
            # Return defaults if no settings found
            return jsonify({
                "theme": "light",
                "language": "en",
                "difficulty": "beginner",
                "session_length": 15,
                "mute_sound": False
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        db.close()


# -------------------- START SERVER --------------------
if __name__ == "__main__":
    app.run(debug=True)
