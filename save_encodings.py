# save_encodings.py

import face_recognition
import os
import pickle

KNOWN_FACES_DIR = "known_faces"
encodings = []
names = []

if not os.path.exists(KNOWN_FACES_DIR):
    os.makedirs(KNOWN_FACES_DIR)
    print(f"📁 Created '{KNOWN_FACES_DIR}' directory.")

image_files = [f for f in os.listdir(KNOWN_FACES_DIR) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

if not image_files:
    print(f"⚠️ Warning: No image files (.jpg, .png, .jpeg) found in '{KNOWN_FACES_DIR}'.")
    print(f"👉 Please add face images named like 'YourName.jpg' into '{KNOWN_FACES_DIR}/' before running.")
    exit()

for filename in image_files:
    path = os.path.join(KNOWN_FACES_DIR, filename)
    image = face_recognition.load_image_file(path)
    encoding = face_recognition.face_encodings(image)
    if encoding:
        encodings.append(encoding[0])
        names.append(os.path.splitext(filename)[0])
        print(f"✅ Encoded: {filename}")
    else:
        print(f"❌ No face detected in: {filename}")

with open("encodings.pkl", "wb") as f:
    pickle.dump((encodings, names), f)

print(f"✅ Successfully encoded {len(names)} face(s) to 'encodings.pkl'.")
