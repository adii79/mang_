# pip install requests numpy opencv-python

import requests
import numpy as np
import cv2
import base64
import time
import random

# -------------------------------
# Firebase Config
# -------------------------------
FIREBASE_HOST = "https://bluenova-7926f-default-rtdb.asia-southeast1.firebasedatabase.app/"
FIREBASE_AUTH = "hswIlGS4HikO4JnOF3spt8J3pe9rUwmHtDg53EBN"
FIREBASE_PATH = "/captured_images.json"   # Upload like ESP32 does

# -------------------------------
# Function: Create Random Image
# -------------------------------
def generate_random_image(width=320, height=240):
    """Generate a random RGB image."""
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

# -------------------------------
# Function: Upload Image to Firebase
# -------------------------------
def upload_to_firebase():
    try:
        # 1. Generate random image
        img = generate_random_image()

        # 2. Convert to JPG
        _, img_encoded = cv2.imencode(".jpg", img)
        img_bytes = img_encoded.tobytes()

        # 3. Base64 encode (Firebase-friendly)
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # 4. Prepare data
        timestamp = int(time.time())
        data = {
            "timestamp": timestamp,
            "image": img_base64
        }

        # 5. Send to Firebase
        url = f"{FIREBASE_HOST}{FIREBASE_PATH}?auth={FIREBASE_AUTH}"
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print(f"✔ Uploaded random image at {timestamp}")
        else:
            print(f"✘ Firebase upload failed: {response.status_code}")

    except Exception as e:
        print("Error:", e)

# -------------------------------
# Continuous Upload Loop
# -------------------------------
if __name__ == "__main__":
    print("🔥 Simulating ESP32 image uploads to Firebase…")

    while True:
        upload_to_firebase()
        time.sleep(5)   # Upload every 5 seconds (change if needed)
