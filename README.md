# Face Attendance System with Anti-Spoofing Liveness Detection

Face attendance system that uses facial recognition and blink detection to verify live presence before marking attendance. Built with OpenCV, dlib, and the face_recognition library.

---

## Key Features

- Face recognition with 128D embeddings via dlib
- Blink-based liveness check using Eye Aspect Ratio (EAR) to prevent photo spoofing
- Unknown face detection with periodic snapshot saving to `intruders/`
- Each person is marked only once per day in `attendance.csv`
- Frame downscaling (0.25x) to keep detection fast

---

## Prerequisites & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd face_attendance
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

> Note: On Windows, building `dlib` requires **CMake** and **Visual Studio C++ Build Tools**. Ensure `cmake` is installed before installing packages.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you encounter issues installing `dlib` on Windows, install `cmake` first:
```bash
pip install cmake
pip install dlib
pip install -r requirements.txt
```

---

## How to Run

### Step 1: Register Known Faces
1. Take clear, well-lit portrait photos of authorized individuals.
2. Place the images into the `known_faces/` folder.
3. Name each image after the person (the filename becomes their attendance name):
   ```
   known_faces/
     Sravan.jpg
     John.png
     Alice.jpeg
   ```

### Step 2: Generate Face Encodings
Processes all images in `known_faces/` and saves the encodings to `encodings.pkl`:
```bash
python save_encodings.py
```

### Step 3: Launch Attendance System
```bash
python mark_attendance.py
```

- Position your face in front of the camera.
- The interface will display `Please Blink...` in orange.
- Blink naturally: once detected, your status turns green (Verified) and your record is written to `attendance.csv`.
- Press `q` to quit.

---

## Sample Attendance Output (`attendance.csv`)

| Name | Date | Time |
| :--- | :--- | :--- |
| Sravan | 2026-10-14 | 09:15:32 |
| John | 2026-10-14 | 09:18:05 |

---

## Configuration

All runtime thresholds can be customized at the top of `mark_attendance.py`:

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `TOLERANCE` | `0.6` | Maximum euclidean distance for face match. Lower is stricter. |
| `EYE_ASPECT_RATIO_THRESHOLD` | `0.23` | EAR value below which an eye is categorized as closed. |
| `EYE_ASPECT_RATIO_CONSEC_FRAMES` | `3` | Number of consecutive frames eyes must remain closed to confirm a blink. |
| `INTRUDER_COOLDOWN` | `5` | Minimum seconds between consecutive intruder photo captures. |

---

## Anti-Spoofing Details

The Eye Aspect Ratio (EAR) is calculated using vertical and horizontal distances between 6 eye landmark points:

    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)

- Eyes open: EAR stays roughly between 0.28 and 0.35.
- Eyes closed (blink): EAR drops below 0.23.
- A static photo or screen replay without natural blinks fails verification.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'face_recognition'`**: Activate the virtual environment where the requirements were installed.
- **Camera Not Opening**: Change the index in `cv2.VideoCapture(0)` to `1` if using an external USB webcam.
- **False Unknown Rejections**: Use well-lit, front-facing photos in `known_faces/` without heavy shadows or occlusions.

---

## License
MIT License. Free to use and modify for personal or educational use.
