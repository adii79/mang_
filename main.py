from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from PIL import Image
import io
import base64
from datetime import datetime
import requests

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Firebase Configuration
FIREBASE_HOST = "https://bluenova-7926f-default-rtdb.asia-southeast1.firebasedatabase.app/"
FIREBASE_AUTH = "hswIlGS4HikO4JnOF3spt8J3pe9rUwmHtDg53EBN"
FIREBASE_PATH = "/captured_images.json"

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Load YOLO model
MODEL_PATH = 'best.pt'
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

def fetch_latest_image_from_firebase():
    """Fetch the latest image from Firebase."""
    try:
        firebase_url = f"{FIREBASE_HOST}{FIREBASE_PATH}?auth={FIREBASE_AUTH}"
        response = requests.get(firebase_url)
        
        if response.status_code == 200 and response.json():
            images = response.json()
            latest_entry = max(images.values(), key=lambda x: x["timestamp"])
            return latest_entry["image"]
        else:
            print(f"Firebase response error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error fetching image from Firebase: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_carbon(total_area_m2):
    """Calculate carbon sequestration from mangrove area"""
    total_area_ha = total_area_m2 / 10000
    carbon_per_ha = 388  # tons C per hectare (IPCC default)
    total_carbon = total_area_ha * carbon_per_ha
    total_co2 = total_carbon * 3.67  # Convert C to CO2
    
    return {
        'area_m2': round(total_area_m2, 2),
        'area_ha': round(total_area_ha, 4),
        'carbon_tons': round(total_carbon, 2),
        'co2_tons': round(total_co2, 2)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_firebase_image', methods=['GET'])
def fetch_firebase_image():
    """Fetch the latest image from Firebase and return as base64"""
    try:
        image_data = fetch_latest_image_from_firebase()
        if image_data:
            return jsonify({
                'success': True,
                'image': image_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No image found in Firebase'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded. Please check model path.'}), 500
    
    try:
        # Check if image is from Firebase or uploaded
        use_firebase = request.form.get('use_firebase', 'false') == 'true'
        
        if use_firebase:
            # Fetch image from Firebase
            image_data = fetch_latest_image_from_firebase()
            if not image_data:
                return jsonify({'error': 'Could not fetch image from Firebase'}), 400
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Save to temporary file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"firebase_{timestamp}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            
        else:
            # Original upload logic
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Use PNG, JPG, or JPEG'}), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        
        # Get confidence threshold from form
        confidence = float(request.form.get('confidence', 0.3))
        pixel_to_meter = float(request.form.get('pixel_to_meter', 0.5))
        
        # Run detection
        results = model.predict(filepath, conf=confidence)
        
        detections_list = []
        total_area_pixels = 0
        
        for r in results:
            boxes = r.boxes
            names = r.names
            
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    class_id = int(box.cls[0])
                    class_name = names[class_id]
                    conf = float(box.conf[0])
                    bbox = box.xyxy[0].cpu().numpy()
                    
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    area_pixels = width * height
                    total_area_pixels += area_pixels
                    
                    detections_list.append({
                        'id': i + 1,
                        'class': class_name,
                        'confidence': round(conf * 100, 1),
                        'bbox': {
                            'x1': int(bbox[0]),
                            'y1': int(bbox[1]),
                            'x2': int(bbox[2]),
                            'y2': int(bbox[3])
                        },
                        'width': int(width),
                        'height': int(height),
                        'area_pixels': int(area_pixels)
                    })
            
            # Create annotated image
            if boxes is not None and len(boxes) > 0:
                detections = sv.Detections.from_ultralytics(r)
                image = cv2.imread(filepath)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                box_annotator = sv.BoxAnnotator(
                    thickness=3,
                    color=sv.Color(r=0, g=255, b=0)
                )
                label_annotator = sv.LabelAnnotator(
                    text_color=sv.Color(r=255, g=255, b=255),
                    text_scale=0.5,
                    text_thickness=2
                )
                
                # Create labels with confidence
                labels = [
                    f"{names[int(class_id)]} {conf:.0%}"
                    for class_id, conf in zip(detections.class_id, detections.confidence)
                ]
                
                annotated_image = box_annotator.annotate(image, detections)
                annotated_image = label_annotator.annotate(annotated_image, detections, labels)
                
                # Save annotated image
                result_filename = f"result_{filename}"
                result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
                cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
                
                # Convert to base64 for display
                _, buffer = cv2.imencode('.jpg', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
                img_base64 = base64.b64encode(buffer).decode('utf-8')
            else:
                img_base64 = None
                result_filename = None
        
        # Calculate carbon sequestration
        total_area_m2 = total_area_pixels * (pixel_to_meter ** 2)
        carbon_data = calculate_carbon(total_area_m2)
        
        response = {
            'success': True,
            'detections': detections_list,
            'total_detections': len(detections_list),
            'carbon_sequestration': carbon_data,
            'annotated_image': img_base64,
            'result_filename': result_filename,
            'parameters': {
                'confidence_threshold': confidence,
                'pixel_to_meter': pixel_to_meter
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)