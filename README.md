# YogaMaster - AI-Powered Yoga Pose Detection

A full-stack web application for real-time yoga pose detection, practice tracking, and multi-language voice guidance using TensorFlow's MoveNet AI model.

## Features

✅ **User Authentication** - Signup, login, session management  
✅ **AI Pose Detection** - Real-time pose checking via MoveNet Thunder model  
✅ **22 Yoga Poses** - Lotus, Warrior I/II/III, Mountain, Tree, Bridge, Plank, Downward Dog, etc.  
✅ **Multi-Language Support** - English, Hindi, Marathi, Kannada with Web Speech API voice guidance  
✅ **Practice Mode** - Live webcam, step-by-step instructions, accuracy feedback  
✅ **Dashboard Analytics** - Streak tracking, session history, accuracy metrics  
✅ **Settings & Preferences** - Dark mode, language selection, difficulty levels  
✅ **Responsive Design** - Mobile-friendly UI, works on tablets and desktops  

## Tech Stack

- **Backend**: Flask (Python) + MySQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI/ML**: TensorFlow Hub (MoveNet Thunder), OpenCV
- **Database**: MySQL with normalized schema

## Prerequisites

- Python 3.8+
- MySQL 5.7+ or MariaDB 10.4+
- A modern web browser with WebRTC support (for webcam access)
- ~2GB free disk space (for TensorFlow models)

## Installation

### 1. Clone Repository
```bash
cd c:\Users\ombat\Yoga-pose-detection
```

### 2. Set Up Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Python Dependencies
```bash
pip install -r requirement.txt
```

**Note**: TensorFlow installation can take 5-10 minutes. If you encounter issues:
- Ensure you have 4GB+ free RAM
- For CPU-only: No additional setup needed
- For GPU support: Install CUDA 11.8 and cuDNN 8.6 (optional, advanced)

### 4. Set Up MySQL Database

**Option A: Using phpMyAdmin**
1. Log into phpMyAdmin (usually `http://localhost/phpmyadmin`)
2. Create a new database named `yoga_db`
3. Go to "Import" tab → Select `yoga_db.sql` → Click Import
4. Then run the migration: Copy contents of `migrations/001_add_poses_and_constraints.sql` into SQL tab → Execute

**Option B: Using MySQL CLI**
```powershell
mysql -u root -p < yoga_db.sql
mysql -u root -p yoga_db < migrations/001_add_poses_and_constraints.sql
```

### 5. Configure Database Connection

Edit `backend/db.py`:
```python
def get_db_connection():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_mysql_password",  # <-- Change this
        database="yoga_db"
    )
    return db
```

### 6. Run the Flask Server
```powershell
python app.py
```

Server will start at `http://localhost:5000`

## Usage

### For Users
1. **Sign Up**: Create account at `/signup`
2. **Login**: Access dashboard at `/login`
3. **Browse Poses**: View all 22 poses at `/poses`
4. **Start Practice**: Click "Start Practice" on any pose detail page
5. **Practice Mode**: 
   - Allow webcam access
   - Follow step-by-step instructions
   - AI provides real-time feedback
   - Complete all steps to finish

### For Developers

#### Understanding the Code Structure
```
app.py                    # Main Flask app, routes, /detect endpoint
pose_logic.py            # Pose detection functions (22 poses)
backend/
  └── db.py              # MySQL connection
frontend/
  ├── templates/         # HTML pages (Jinja2)
  ├── css/               # Styling
  ├── js/                # Frontend logic
  └── assets/            # Images, lang.json
migrations/              # Database migration scripts
```

#### Key APIs

**POST /detect**
- Detects if user's current pose matches target pose
- Requires: `image` (base64), `pose` (string), optional `step` (int)
- Returns: `{"pose": "Lotus Pose", "correct": true/false, "tip": "feedback message"}`

**GET /get_steps**
- Fetches pose steps from database
- Params: `pose` (pose name), `lang` (en/hi/mr/kn)
- Returns: JSON array of step objects

#### Adding New Poses

1. Add SQL INSERT in `migrations/` for new pose metadata
2. Create a detection function in `pose_logic.py`:
   ```python
   def is_my_new_pose(keypoints, step=None):
       # keypoints: dict of body part positions (x, y normalized 0..1)
       # step: optional step number for multi-step poses
       return {"pose": "My New Pose", "correct": True/False, "tip": "..."}
   ```
3. Register in `POSE_FUNCTIONS` dict in `pose_logic.py`

#### Pose Detection Logic

Each pose function uses keypoints from MoveNet (17 body points: shoulders, hips, knees, ankles, elbows, wrists, nose).

Example: Detect if knees are bent
```python
if keypoints["left_knee"][1] > keypoints["left_hip"][1]:
    return {"pose": "Chair Pose", "correct": True, "tip": "Good knee bend"}
```

## Performance Tips

- **First Load**: MoveNet model downloads (~50MB) on first `/detect` call — takes ~5 seconds
- **GPU**: If available, TensorFlow will use it automatically (much faster)
- **Webcam**: Ensure good lighting for best pose detection accuracy
- **Steps**: Increase detection interval in `frontend/js/script.js` if CPU usage high

## Database Schema

**poses**
- `id`: PK (1-22)
- `pose_name`: string (e.g., "Lotus Pose")
- `pose_description`: text (e.g., "Meditation pose")
- `difficulty_level`: enum (beginner/intermediate)

**pose_steps**
- `id`: PK
- `pose_id`: FK → poses.id
- `pose_name`: string (denormalized for queries)
- `language_code`: enum (en/hi/mr/kn)
- `step_number`: int (1-6)
- `step_text`: text (instruction)

**users**
- `id`: PK
- `username`, `email`, `password` (plaintext — **TODO: hash**)
- `created_at`: timestamp

## Known Issues & TODOs

⚠️ **Security**
- [ ] Password hashing (currently plaintext)
- [ ] CSRF protection on forms
- [ ] Input validation on signup/login

⚠️ **Features**
- [ ] Dashboard analytics (DB schema ready, frontend pending)
- [ ] User settings persistence (localStorage only)
- [ ] Pose images (not yet linked)

⚠️ **Performance**
- [ ] Pose detection rate limiting
- [ ] Session management for long practice

## Troubleshooting

**TensorFlow takes too long to install**
- Use `pip install --no-cache-dir tensorflow-cpu==2.13.0` for CPU-only (faster)

**MoveNet model fails to download**
- Check internet connection
- Try: `python -c "import tensorflow_hub; hub.load('https://tfhub.dev/google/movenet/singlepose/thunder/4')"`

**Database connection errors**
- Verify MySQL is running: `mysql -u root -p -e "SELECT 1"`
- Check `backend/db.py` credentials match your MySQL setup

**Webcam doesn't work**
- Use HTTPS or localhost (browser security)
- Check browser permissions: Settings → Privacy → Camera

## Deployment

For production:
1. Set `app.run(debug=False)` in `app.py`
2. Use a production WSGI server: `pip install gunicorn` → `gunicorn app:app`
3. Implement password hashing: `from werkzeug.security import generate_password_hash, check_password_hash`
4. Use environment variables: `python-dotenv` is already in dependencies
5. Enable HTTPS and CSRF protection via Flask-Talisman

## Future Enhancements

- [ ] Pose image library with copyright-free yoga images
- [ ] Real-time pose visualization (draw skeleton on webcam)
- [ ] Leaderboard & social features
- [ ] Mobile app (React Native / Flutter)
- [ ] Advanced analytics: Weekly trends, pose difficulty progression
- [ ] Export session videos with pose feedback overlays

## Contributing

For bug reports or feature requests, please document:
1. Steps to reproduce
2. Expected vs actual behavior
3. Python/Browser versions
4. Screenshots/logs

## License

This project is for educational purposes.

## Support

For issues:
1. Check this README for known issues
2. Review database migration output for schema errors
3. Check browser console (F12) for frontend errors
4. Check Flask server terminal for backend errors

---

**Last Updated**: December 8, 2025  
**DB Migration Status**: ✅ Complete (22 poses, 320 steps, 4 languages)  
**Pose Detection**: ✅ Implemented (22 poses in `pose_logic.py`)  
**API Integration**: ✅ Complete (`/detect` endpoint wired)
