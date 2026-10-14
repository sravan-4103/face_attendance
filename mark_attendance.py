import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
import csv
import pickle
import time

# Configuration
KNOWN_FACES_DIR = 'known_faces'
INTRUDER_DIR = 'intruders'
ATTENDANCE_FILE = 'attendance.csv'
ENCODINGS_FILE = 'encodings.pkl'
TOLERANCE = 0.6
INTRUDER_COOLDOWN = 5  # seconds

# Liveness (Blink) Settings
EYE_ASPECT_RATIO_THRESHOLD = 0.23  # If eyes are closed, ratio falls below this
EYE_ASPECT_RATIO_CONSEC_FRAMES = 3 # How many frames eyes must be closed to count as a blink (3 ≈ 100ms)

# Setup Directories
if not os.path.exists(INTRUDER_DIR): os.makedirs(INTRUDER_DIR)

# Load Encodings
if not os.path.exists(ENCODINGS_FILE):
    print(f"[ERROR] {ENCODINGS_FILE} not found. Run save_encodings.py first.")
    exit()

with open(ENCODINGS_FILE, "rb") as f:
    known_face_encodings, known_face_names = pickle.load(f)
print(f"[INFO] Loaded {len(known_face_names)} known face(s).")

# Load Today's Attendance
marked_names = set()
today_str = datetime.now().strftime("%Y-%m-%d")
if os.path.isfile(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0] != "Name" and row[1] == today_str:
                marked_names.add(row[0])
else:
    # Create the file with a header row
    with open(ATTENDANCE_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time"])

# Helper: Calculate Eye Ratio
def get_ear(eye_points):
    # Vertical distances
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    # Horizontal distance
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    # Compute ratio
    return (A + B) / (2.0 * C)

# Runtime Variables
video_capture = cv2.VideoCapture(0)
last_intruder_save_time = 0

# Track blinks: Dictionary { "Name": consecutive_closed_frames }
blink_counters = {} 
# Track verified users: Set { "Name" }
verified_real_users = set()

print("[INFO] Camera started. Blink to record attendance. Press 'q' to quit.")

while True:
    ret, frame = video_capture.read()
    if not ret: break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # 1. Detect Face Locations
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    
    # 2. Detect Facial Landmarks (Eyes, Nose, etc.)
    face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)

    for (face_encoding, face_location, landmarks) in zip(face_encodings, face_locations, face_landmarks_list):
        # Default values in case no branch sets them
        color = (128, 128, 128)  # Grey
        label = "Unknown"
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=TOLERANCE)
        name = "Unknown"
        
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

        # Scale coordinates back up
        top, right, bottom, left = [v * 4 for v in face_location]

        if name == "Unknown":
            # INTRUDER LOGIC
            color = (0, 0, 255) # Red
            label = "Unknown"
            
            if time.time() - last_intruder_save_time > INTRUDER_COOLDOWN:
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                cv2.imwrite(os.path.join(INTRUDER_DIR, f"intruder_{ts}.jpg"), frame)
                print(f"[ALERT] Unknown face captured: {ts}")
                last_intruder_save_time = time.time()

        else:
            # KNOWN USER LOGIC 
            
            # Initialize blink counter for this person if not exists
            if name not in blink_counters: blink_counters[name] = 0

            # 1. Calculate Eye Aspect Ratio (Liveness)
            left_eye = np.array(landmarks['left_eye'])
            right_eye = np.array(landmarks['right_eye'])
            ear = (get_ear(left_eye) + get_ear(right_eye)) / 2.0

            # 2. Check for Blink
            if ear < EYE_ASPECT_RATIO_THRESHOLD:
                blink_counters[name] += 1
            else:
                # If eyes open AND they were closed for enough frames -> Verified Blink!
                if blink_counters[name] >= EYE_ASPECT_RATIO_CONSEC_FRAMES:
                    verified_real_users.add(name)
                blink_counters[name] = 0  # Reset counter

            # 3. Determine Status
            if name in verified_real_users:
                #  LIVE & VERIFIED 
                if name not in marked_names:
                    marked_names.add(name)
                    # Save to CSV
                    with open(ATTENDANCE_FILE, 'a', newline='') as f:
                        writer = csv.writer(f)
                        now = datetime.now()
                        writer.writerow([name, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")])
                    print(f"[ATTENDANCE] Marked {name} at {now.strftime('%H:%M:%S')}")
                
                color = (0, 255, 0) # Green
                label = f"{name} (Verified)"
            else:
                # WAITING FOR BLINK
                color = (0, 165, 255) # Orange
                label = "Please Blink..."

        # Draw Graphics
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow('Face Attendance Liveness', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

video_capture.release()
cv2.destroyAllWindows()