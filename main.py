

# # from flask import Flask, render_template, request, jsonify, send_file
# # from werkzeug.utils import secure_filename
# # import os
# # import cv2
# # import numpy as np
# # from ultralytics import YOLO
# # import supervision as sv
# # from PIL import Image
# # import io
# # import base64
# # from datetime import datetime
# # import requests
# # import threading
# # import time

# # app = Flask(__name__)

# # # Configuration
# # UPLOAD_FOLDER = 'uploads'
# # RESULTS_FOLDER = 'results'
# # ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# # MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# # # Firebase Configuration - Use environment variables for security
# # FIREBASE_HOST = os.environ.get('FIREBASE_HOST', "https://newcam-19ef1-default-rtdb.firebaseio.com/")
# # FIREBASE_AUTH = os.environ.get('FIREBASE_AUTH', "0njZXc3wlhf62RfoqLOlZhKNdDQCBp0NFQxRrKIB")
# # FIREBASE_INPUT_PATH = "/captured_images"
# # FIREBASE_OUTPUT_PATH = "/MVR"

# # # Create folders
# # os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# # os.makedirs(RESULTS_FOLDER, exist_ok=True)

# # app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# # app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
# # app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# # # Load YOLO model
# # MODEL_PATH = 'best.pt'
# # try:
# #     model = YOLO(MODEL_PATH)
# #     print(f"✅ Model loaded successfully from {MODEL_PATH}")
# # except Exception as e:
# #     print(f"❌ Error loading model: {e}")
# #     model = None

# # # Global variables (only for tracking, not for serving data)
# # last_processed_timestamp = None
# # firebase_monitor_running = False

# # def fetch_latest_image_from_firebase():
# #     """Fetch the latest image from Firebase."""
# #     try:
# #         firebase_url = f"{FIREBASE_HOST}{FIREBASE_INPUT_PATH}.json?auth={FIREBASE_AUTH}"
# #         response = requests.get(firebase_url, timeout=10)
        
# #         if response.status_code == 200 and response.json():
# #             images = response.json()
# #             latest_key = max(images.keys(), key=lambda k: images[k].get("timestamp", ""))
# #             latest_entry = images[latest_key]
# #             return latest_entry["image"], latest_entry["timestamp"], latest_key
# #         else:
# #             print(f"Firebase response error: {response.status_code}")
# #             return None, None, None
            
# #     except Exception as e:
# #         print(f"Error fetching image from Firebase: {e}")
# #         return None, None, None

# # def send_results_to_firebase(results_data):
# #     """Send complete detection results to Firebase with properly encoded image."""
# #     try:
# #         timestamp_key = f"detection_{int(time.time() * 1000)}"
        
# #         # Calculate tree equivalent
# #         trees_equiv = round(results_data['carbon_sequestration']['co2_tons'] * 1000 / 20)
        
# #         # Prepare complete Firebase data structure
# #         firebase_data = {
# #             "timestamp": datetime.now().isoformat(),
# #             "detection_summary": {
# #                 "total_mangroves": results_data['total_detections'],
# #                 "area_m2": results_data['carbon_sequestration']['area_m2'],
# #                 "area_hectares": results_data['carbon_sequestration']['area_ha']
# #             },
# #             "carbon_sequestration": {
# #                 "carbon_stock_tons": results_data['carbon_sequestration']['carbon_tons'],
# #                 "co2_equivalent_tons": results_data['carbon_sequestration']['co2_tons'],
# #                 "trees_equivalent_per_year": trees_equiv
# #             },
# #             "annotated_image": results_data.get('annotated_image', ''),
# #             "parameters": results_data['parameters'],
# #             "detections": results_data['detections'],
# #             "source": results_data.get('source', 'firebase_auto'),
# #             "processing_timestamp": results_data.get('processing_timestamp', datetime.now().isoformat())
# #         }
        
# #         # Send to latest_detection (real-time dashboard)
# #         dashboard_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/latest_detection.json?auth={FIREBASE_AUTH}"
# #         dashboard_response = requests.put(dashboard_url, json=firebase_data, timeout=10)
        
# #         if dashboard_response.status_code == 200:
# #             print(f"✅ Real-time dashboard updated at /MVR/latest_detection")
# #             print(f"   Total mangroves: {results_data['total_detections']}")
# #             print(f"   Image size: {len(results_data.get('annotated_image', ''))} bytes")
            
# #             # Also save to history
# #             history_data = {timestamp_key: firebase_data}
# #             history_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/history.json?auth={FIREBASE_AUTH}"
# #             requests.patch(history_url, json=history_data, timeout=10)
# #             print(f"✅ Saved to history at /MVR/history/{timestamp_key}")
# #             return True
# #         else:
# #             print(f"❌ Firebase update error: {dashboard_response.status_code}")
# #             return False
            
# #     except Exception as e:
# #         print(f"❌ Error sending to Firebase: {e}")
# #         return False

# # def calculate_carbon(total_area_m2):
# #     """Calculate carbon sequestration from mangrove area"""
# #     total_area_ha = total_area_m2 / 10000
# #     carbon_per_ha = 388  # tons C per hectare
# #     total_carbon = total_area_ha * carbon_per_ha
# #     total_co2 = total_carbon * 3.67  # Convert C to CO2
    
# #     return {
# #         'area_m2': round(total_area_m2, 2),
# #         'area_ha': round(total_area_ha, 4),
# #         'carbon_tons': round(total_carbon, 2),
# #         'co2_tons': round(total_co2, 2)
# #     }

# # def process_image_detection(image_data=None, file_path=None, confidence=0.3, pixel_to_meter=0.5, source="firebase_auto"):
# #     """Core detection function - ALWAYS returns annotated image in base64."""
# #     if model is None:
# #         return {'error': 'Model not loaded', 'success': False}
    
# #     try:
# #         # Handle image input
# #         if image_data:
# #             image_bytes = base64.b64decode(image_data)
# #             image = Image.open(io.BytesIO(image_bytes))
            
# #             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# #             filename = f"firebase_{timestamp}.jpg"
# #             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# #             image.save(filepath)
# #         elif file_path:
# #             filepath = file_path
# #             filename = os.path.basename(filepath)
# #         else:
# #             return {'error': 'No image provided', 'success': False}
        
# #         # Run YOLO detection
# #         results = model.predict(filepath, conf=confidence)
        
# #         detections_list = []
# #         total_area_pixels = 0
        
# #         # Load image for annotation
# #         image = cv2.imread(filepath)
# #         image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
# #         # Process detections
# #         for r in results:
# #             boxes = r.boxes
# #             names = r.names
            
# #             if boxes is not None and len(boxes) > 0:
# #                 # Create annotations
# #                 detections = sv.Detections.from_ultralytics(r)
                
# #                 box_annotator = sv.BoxAnnotator(
# #                     thickness=3,
# #                     color=sv.Color(r=0, g=255, b=0)
# #                 )
# #                 label_annotator = sv.LabelAnnotator(
# #                     text_color=sv.Color(r=255, g=255, b=255),
# #                     text_scale=0.5,
# #                     text_thickness=2
# #                 )
                
# #                 labels = [
# #                     f"{names[int(class_id)]} {conf:.0%}"
# #                     for class_id, conf in zip(detections.class_id, detections.confidence)
# #                 ]
                
# #                 # Annotate image
# #                 annotated_image = box_annotator.annotate(image_rgb.copy(), detections)
# #                 annotated_image = label_annotator.annotate(annotated_image, detections, labels)
                
# #                 # Process detection data
# #                 for i, box in enumerate(boxes):
# #                     class_id = int(box.cls[0])
# #                     class_name = names[class_id]
# #                     conf = float(box.conf[0])
# #                     bbox = box.xyxy[0].cpu().numpy()
                    
# #                     width = bbox[2] - bbox[0]
# #                     height = bbox[3] - bbox[1]
# #                     area_pixels = width * height
# #                     total_area_pixels += area_pixels
                    
# #                     detections_list.append({
# #                         'id': i + 1,
# #                         'class': class_name,
# #                         'confidence': round(conf * 100, 1),
# #                         'bbox': {
# #                             'x1': int(bbox[0]),
# #                             'y1': int(bbox[1]),
# #                             'x2': int(bbox[2]),
# #                             'y2': int(bbox[3])
# #                         },
# #                         'width': int(width),
# #                         'height': int(height),
# #                         'area_pixels': int(area_pixels)
# #                     })
# #             else:
# #                 # No detections - use original image
# #                 annotated_image = image_rgb
        
# #         # Save annotated image
# #         result_filename = f"result_{filename}"
# #         result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
# #         cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        
# #         # Encode image to base64
# #         _, buffer = cv2.imencode('.jpg', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
# #         img_base64 = base64.b64encode(buffer).decode('utf-8')
        
# #         # Calculate carbon metrics
# #         total_area_m2 = total_area_pixels * (pixel_to_meter ** 2)
# #         carbon_data = calculate_carbon(total_area_m2)
        
# #         response = {
# #             'success': True,
# #             'detections': detections_list,
# #             'total_detections': len(detections_list),
# #             'carbon_sequestration': carbon_data,
# #             'annotated_image': img_base64,
# #             'result_filename': result_filename,
# #             'parameters': {
# #                 'confidence_threshold': confidence,
# #                 'pixel_to_meter': pixel_to_meter
# #             },
# #             'source': source,
# #             'processing_timestamp': datetime.now().isoformat()
# #         }
        
# #         print(f"✅ Detection completed: {len(detections_list)} mangroves, image encoded: {len(img_base64)} bytes")
        
# #         return response
    
# #     except Exception as e:
# #         print(f"❌ Detection error: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return {'error': str(e), 'success': False}

# # def monitor_firebase():
# #     """Background thread to monitor Firebase for new images."""
# #     global last_processed_timestamp, firebase_monitor_running
    
# #     print("🔥 Firebase monitoring started...")
# #     firebase_monitor_running = True
# #     initial_load = True
    
# #     while firebase_monitor_running:
# #         try:
# #             image_data, timestamp, image_key = fetch_latest_image_from_firebase()
            
# #             if image_data and timestamp:
# #                 # Process on first load OR when new image detected
# #                 if initial_load or last_processed_timestamp is None or timestamp > last_processed_timestamp:
# #                     if initial_load:
# #                         print(f"🔄 Loading latest Firebase image on startup...")
# #                         initial_load = False
# #                     else:
# #                         print(f"🆕 New image detected! Timestamp: {timestamp}")
                    
# #                     last_processed_timestamp = timestamp
                    
# #                     result = process_image_detection(
# #                         image_data=image_data,
# #                         confidence=0.3,
# #                         pixel_to_meter=0.5,
# #                         source="firebase_auto"
# #                     )
                    
# #                     if result and result.get('success'):
# #                         print(f"✅ Detection completed: {result['total_detections']} mangroves found")
# #                         # Send to Firebase immediately
# #                         send_results_to_firebase(result)
# #                     else:
# #                         print(f"❌ Detection failed: {result.get('error', 'Unknown error')}")
                        
# #             time.sleep(5)  # Check every 5 seconds
            
# #         except Exception as e:
# #             print(f"❌ Error in Firebase monitor: {e}")
# #             import traceback
# #             traceback.print_exc()
# #             time.sleep(5)

# # @app.route('/')
# # def index():
# #     return render_template('index.html')

# # @app.route('/health')
# # def health():
# #     """Health check endpoint for monitoring services"""
# #     return jsonify({
# #         'status': 'healthy',
# #         'model_loaded': model is not None,
# #         'firebase_monitor': firebase_monitor_running
# #     })

# # @app.route('/get_latest_detection')
# # def get_latest_detection():
# #     """Fetch latest detection directly from Firebase (no memory cache)."""
# #     try:
# #         firebase_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/latest_detection.json?auth={FIREBASE_AUTH}"
# #         response = requests.get(firebase_url, timeout=10)
        
# #         if response.status_code == 200 and response.json():
# #             data = response.json()
# #             return jsonify({
# #                 'success': True,
# #                 'data': data
# #             })
# #         else:
# #             return jsonify({
# #                 'success': False,
# #                 'message': 'No detection available yet'
# #             })
            
# #     except Exception as e:
# #         return jsonify({
# #             'success': False,
# #             'error': str(e)
# #         })

# # @app.route('/predict_manual', methods=['POST'])
# # def predict_manual():
# #     """Manual upload endpoint - separate from auto-detection."""
# #     if model is None:
# #         return jsonify({'error': 'Model not loaded'}), 500
    
# #     try:
# #         if 'file' not in request.files:
# #             return jsonify({'error': 'No file uploaded'}), 400
        
# #         file = request.files['file']
        
# #         if file.filename == '':
# #             return jsonify({'error': 'No file selected'}), 400
        
# #         filename = secure_filename(file.filename)
# #         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# #         filename = f"manual_{timestamp}_{filename}"
# #         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# #         file.save(filepath)
        
# #         confidence = float(request.form.get('confidence', 0.3))
# #         pixel_to_meter = float(request.form.get('pixel_to_meter', 0.5))
        
# #         result = process_image_detection(
# #             file_path=filepath,
# #             confidence=confidence,
# #             pixel_to_meter=pixel_to_meter,
# #             source="manual_upload"
# #         )
        
# #         return jsonify(result)
    
# #     except Exception as e:
# #         return jsonify({'error': str(e)}), 500

# # @app.route('/firebase_status')
# # def firebase_status():
# #     """Check Firebase monitoring status."""
# #     return jsonify({
# #         'monitoring_active': firebase_monitor_running,
# #         'last_processed_timestamp': last_processed_timestamp
# #     })

# # if __name__ == '__main__':
# #     # Start Firebase monitor thread
# #     monitor_thread = threading.Thread(target=monitor_firebase, daemon=True)
# #     monitor_thread.start()
    
# #     print("="*70)
# #     print("🌳 MANGROVE DETECTION SYSTEM - FIREBASE DIRECT MODE")
# #     print("="*70)
# #     print("🔥 Firebase Auto-Monitor: ACTIVE")
# #     print("📊 Data Source: Firebase /MVR/latest_detection")
# #     print("📁 Detection History: /MVR/history/")
# #     print("🔄 Update Interval: 5 seconds")
# #     print("💾 No Local Memory - All data from Firebase")
# #     print("📤 Manual Upload: Separate from auto-detection")
# #     print("💡 Startup: Loads last Firebase image immediately")
# #     print("="*70)
    
# #     # Get port from environment variable (Render provides this)
# #     port = int(os.environ.get('PORT', 5100))
    
# #     # Run the app
# #     app.run(host='0.0.0.0', port=port)




# from flask import Flask, render_template, request, jsonify, send_file
# from werkzeug.utils import secure_filename
# import os
# import cv2
# import numpy as np
# from ultralytics import YOLO
# import supervision as sv
# from PIL import Image
# import io
# import base64
# from datetime import datetime
# import requests
# import threading
# import time

# app = Flask(__name__)

# # Configuration
# UPLOAD_FOLDER = 'uploads'
# RESULTS_FOLDER = 'results'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# # Firebase Configuration
# FIREBASE_HOST = os.environ.get('FIREBASE_HOST', "https://newcam-19ef1-default-rtdb.firebaseio.com/")
# FIREBASE_AUTH = os.environ.get('FIREBASE_AUTH', "0njZXc3wlhf62RfoqLOlZhKNdDQCBp0NFQxRrKIB")
# FIREBASE_INPUT_PATH = "/captured_images"
# FIREBASE_OUTPUT_PATH = "/MVR"

# # Create folders
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(RESULTS_FOLDER, exist_ok=True)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# # Load YOLO model
# MODEL_PATH = 'best.pt'
# try:
#     model = YOLO(MODEL_PATH)
#     print(f"✅ Model loaded successfully from {MODEL_PATH}")
# except Exception as e:
#     print(f"❌ Error loading model: {e}")
#     model = None

# # Global track variables
# last_processed_timestamp = None
# firebase_monitor_running = False


# # ----------------------------- FIREBASE FUNCTIONS ----------------------------- #

# def fetch_latest_image_from_firebase():
#     """Fetch latest image from Firebase"""
#     try:
#         firebase_url = f"{FIREBASE_HOST}{FIREBASE_INPUT_PATH}.json?auth={FIREBASE_AUTH}"
#         response = requests.get(firebase_url, timeout=10)
        
#         if response.status_code == 200 and response.json():
#             images = response.json()
#             latest_key = max(images.keys(), key=lambda k: images[k].get("timestamp", ""))
#             latest_entry = images[latest_key]
#             return latest_entry["image"], latest_entry["timestamp"], latest_key
            
#     except Exception as e:
#         print(f"❌ Error fetching image: {e}")
        
#     return None, None, None


# def send_results_to_firebase(results_data):
#     """Upload results to Firebase"""
#     try:
#         timestamp_key = f"detection_{int(time.time() * 1000)}"

#         trees_equiv = round(results_data['carbon_sequestration']['co2_tons'] * 1000 / 20)

#         firebase_data = {
#             "timestamp": datetime.now().isoformat(),
#             "detection_summary": {
#                 "total_mangroves": results_data['total_detections'],
#                 "area_m2": results_data['carbon_sequestration']['area_m2'],
#                 "area_hectares": results_data['carbon_sequestration']['area_ha']
#             },
#             "carbon_sequestration": {
#                 "carbon_stock_tons": results_data['carbon_sequestration']['carbon_tons'],
#                 "co2_equivalent_tons": results_data['carbon_sequestration']['co2_tons'],
#                 "trees_equivalent_per_year": trees_equiv
#             },
#             "annotated_image": results_data['annotated_image'],
#             "parameters": results_data['parameters'],
#             "detections": results_data['detections'],
#             "source": "firebase_auto",
#             "processing_timestamp": results_data['processing_timestamp']
#         }

#         # Update latest_detection
#         dashboard_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/latest_detection.json?auth={FIREBASE_AUTH}"
#         requests.put(dashboard_url, json=firebase_data)

#         # Save to history
#         history_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/history.json?auth={FIREBASE_AUTH}"
#         requests.patch(history_url, json={timestamp_key: firebase_data})

#         print("✅ Results uploaded to Firebase")

#     except Exception as e:
#         print(f"❌ Error sending results: {e}")


# # ----------------------------- DETECTION ENGINE ----------------------------- #

# def calculate_carbon(total_area_m2):
#     """Carbon calc"""
#     total_area_ha = total_area_m2 / 10000
#     carbon_per_ha = 388
#     total_carbon = total_area_ha * carbon_per_ha
#     total_co2 = total_carbon * 3.67

#     return {
#         'area_m2': round(total_area_m2, 2),
#         'area_ha': round(total_area_ha, 4),
#         'carbon_tons': round(total_carbon, 2),
#         'co2_tons': round(total_co2, 2)
#     }


# def process_image_detection(image_data=None, file_path=None, confidence=0.1, pixel_to_meter=0.5, source="firebase_auto"):
#     """Main detection processor – DEFAULT CONF = 0.1"""

#     if model is None:
#         return {'error': 'Model not loaded', 'success': False}

#     try:
#         # Decode image from Firebase
#         if image_data:
#             image_bytes = base64.b64decode(image_data)
#             image = Image.open(io.BytesIO(image_bytes))
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             filename = f"firebase_{timestamp}.jpg"
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             image.save(filepath)

#         # File upload path
#         elif file_path:
#             filepath = file_path
#             filename = os.path.basename(filepath)

#         else:
#             return {'error': 'No image received', 'success': False}

#         # YOLO detection
#         results = model.predict(filepath, conf=confidence)

#         detections_list = []
#         total_area_pixels = 0

#         # Load image for annotation
#         image = cv2.imread(filepath)
#         image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

#         for r in results:
#             boxes = r.boxes
#             names = r.names

#             if boxes is not None and len(boxes) > 0:
#                 dets = sv.Detections.from_ultralytics(r)
#                 box_annotator = sv.BoxAnnotator(thickness=3, color=sv.Color(0, 255, 0))
#                 label_annotator = sv.LabelAnnotator(text_color=sv.Color(255, 255, 255))

#                 labels = [
#                     f"{names[int(cid)]} {conf:.0%}"
#                     for cid, conf in zip(dets.class_id, dets.confidence)
#                 ]

#                 annotated_image = box_annotator.annotate(image_rgb.copy(), dets)
#                 annotated_image = label_annotator.annotate(annotated_image, dets, labels)

#                 # Detection details
#                 for i, box in enumerate(boxes):
#                     cid = int(box.cls[0])
#                     name = names[cid]
#                     conf = float(box.conf[0])
#                     bbox = box.xyxy[0].cpu().numpy()

#                     w = bbox[2] - bbox[0]
#                     h = bbox[3] - bbox[1]
#                     area_pixels = w * h
#                     total_area_pixels += area_pixels

#                     detections_list.append({
#                         'id': i + 1,
#                         'class': name,
#                         'confidence': round(conf * 100, 1),
#                         'bbox': {
#                             'x1': int(bbox[0]),
#                             'y1': int(bbox[1]),
#                             'x2': int(bbox[2]),
#                             'y2': int(bbox[3])
#                         },
#                         'width': int(w),
#                         'height': int(h),
#                         'area_pixels': int(area_pixels)
#                     })

#             else:
#                 annotated_image = image_rgb

#         # Save annotated
#         result_filename = f"result_{filename}"
#         result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
#         cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

#         # Convert to base64
#         _, buffer = cv2.imencode('.jpg', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
#         img_base64 = base64.b64encode(buffer).decode('utf-8')

#         # Carbon calculation
#         total_area_m2 = total_area_pixels * (pixel_to_meter ** 2)
#         carbon_data = calculate_carbon(total_area_m2)

#         return {
#             'success': True,
#             'detections': detections_list,
#             'total_detections': len(detections_list),
#             'carbon_sequestration': carbon_data,
#             'annotated_image': img_base64,
#             'result_filename': result_filename,
#             'parameters': {
#                 'confidence_threshold': confidence,
#                 'pixel_to_meter': pixel_to_meter
#             },
#             'source': source,
#             'processing_timestamp': datetime.now().isoformat()
#         }

#     except Exception as e:
#         print(f"❌ Detection Error: {e}")
#         return {'error': str(e), 'success': False}


# # ----------------------------- FIREBASE AUTO THREAD ----------------------------- #

# def monitor_firebase():
#     """Automatically detects new images every 5 seconds"""
#     global last_processed_timestamp, firebase_monitor_running

#     print("🔥 Firebase Monitor Started...")
#     firebase_monitor_running = True

#     while firebase_monitor_running:
#         try:
#             image_data, timestamp, key = fetch_latest_image_from_firebase()

#             if image_data and timestamp and (last_processed_timestamp is None or timestamp > last_processed_timestamp):

#                 print(f"🆕 New Firebase Image at: {timestamp}")
#                 last_processed_timestamp = timestamp

#                 result = process_image_detection(
#                     image_data=image_data,
#                     confidence=0.1,   # ALWAYS 0.1 HERE
#                     pixel_to_meter=0.5,
#                     source="firebase_auto"
#                 )

#                 if result.get('success'):
#                     send_results_to_firebase(result)

#             time.sleep(5)

#         except Exception as e:
#             print(f"❌ Firebase Monitor Error: {e}")
#             time.sleep(5)


# # ----------------------------- ROUTES ----------------------------- #

# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/health')
# def health():
#     return jsonify({
#         'status': 'healthy',
#         'model_loaded': model is not None,
#         'firebase_monitor_running': firebase_monitor_running
#     })


# @app.route('/predict_manual', methods=['POST'])
# def predict_manual():
#     """Manual upload with default 0.1 confidence"""
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file uploaded'}), 400

#         file = request.files['file']
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#         filename = f"manual_{timestamp}_{secure_filename(file.filename)}"
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         confidence = float(request.form.get('confidence', 0.1))

#         result = process_image_detection(
#             file_path=filepath,
#             confidence=confidence,
#             pixel_to_meter=0.5,
#             source="manual_upload"
#         )

#         return jsonify(result)

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# # ----------------------------- MAIN ----------------------------- #

# if __name__ == '__main__':
#     threading.Thread(target=monitor_firebase, daemon=True).start()

#     print("\n🌳 MANGROVE DETECTION SYSTEM IS RUNNING\n")

#     port = int(os.environ.get('PORT', 5100))
#     app.run(host='0.0.0.0', port=port)



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
import threading
import time

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Firebase Configuration - Use environment variables for security
FIREBASE_HOST = os.environ.get('FIREBASE_HOST', "https://newcam-19ef1-default-rtdb.firebaseio.com/")
FIREBASE_AUTH = os.environ.get('FIREBASE_AUTH', "0njZXc3wlhf62RfoqLOlZhKNdDQCBp0NFQxRrKIB")
FIREBASE_INPUT_PATH = "/captured_images"
FIREBASE_OUTPUT_PATH = "/MVR"

# Confidence threshold for automatic Firebase detection
FIREBASE_AUTO_CONFIDENCE = 0.1  # Lower threshold for automatic detection

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

# Global variables (only for tracking, not for serving data)
last_processed_timestamp = None
firebase_monitor_running = False

def fetch_latest_image_from_firebase():
    """Fetch the latest image from Firebase."""
    try:
        firebase_url = f"{FIREBASE_HOST}{FIREBASE_INPUT_PATH}.json?auth={FIREBASE_AUTH}"
        response = requests.get(firebase_url, timeout=10)
        
        if response.status_code == 200 and response.json():
            images = response.json()
            latest_key = max(images.keys(), key=lambda k: images[k].get("timestamp", ""))
            latest_entry = images[latest_key]
            return latest_entry["image"], latest_entry["timestamp"], latest_key
        else:
            print(f"Firebase response error: {response.status_code}")
            return None, None, None
            
    except Exception as e:
        print(f"Error fetching image from Firebase: {e}")
        return None, None, None

def send_results_to_firebase(results_data):
    """Send complete detection results to Firebase with properly encoded image."""
    try:
        timestamp_key = f"detection_{int(time.time() * 1000)}"
        
        # Calculate tree equivalent
        trees_equiv = round(results_data['carbon_sequestration']['co2_tons'] * 1000 / 20)
        
        # Prepare complete Firebase data structure
        firebase_data = {
            "timestamp": datetime.now().isoformat(),
            "detection_summary": {
                "total_mangroves": results_data['total_detections'],
                "area_m2": results_data['carbon_sequestration']['area_m2'],
                "area_hectares": results_data['carbon_sequestration']['area_ha']
            },
            "carbon_sequestration": {
                "carbon_stock_tons": results_data['carbon_sequestration']['carbon_tons'],
                "co2_equivalent_tons": results_data['carbon_sequestration']['co2_tons'],
                "trees_equivalent_per_year": trees_equiv
            },
            "annotated_image": results_data.get('annotated_image', ''),
            "parameters": results_data['parameters'],
            "detections": results_data['detections'],
            "source": results_data.get('source', 'firebase_auto'),
            "processing_timestamp": results_data.get('processing_timestamp', datetime.now().isoformat())
        }
        
        # Send to latest_detection (real-time dashboard)
        dashboard_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/latest_detection.json?auth={FIREBASE_AUTH}"
        dashboard_response = requests.put(dashboard_url, json=firebase_data, timeout=10)
        
        if dashboard_response.status_code == 200:
            print(f"✅ Real-time dashboard updated at /MVR/latest_detection")
            print(f"   Total mangroves: {results_data['total_detections']}")
            print(f"   Confidence threshold: {results_data['parameters']['confidence_threshold']}")
            print(f"   Image size: {len(results_data.get('annotated_image', ''))} bytes")
            
            # Also save to history
            history_data = {timestamp_key: firebase_data}
            history_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/history.json?auth={FIREBASE_AUTH}"
            requests.patch(history_url, json=history_data, timeout=10)
            print(f"✅ Saved to history at /MVR/history/{timestamp_key}")
            return True
        else:
            print(f"❌ Firebase update error: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending to Firebase: {e}")
        return False

def calculate_carbon(total_area_m2):
    """Calculate carbon sequestration from mangrove area"""
    total_area_ha = total_area_m2 / 10000
    carbon_per_ha = 388  # tons C per hectare
    total_carbon = total_area_ha * carbon_per_ha
    total_co2 = total_carbon * 3.67  # Convert C to CO2
    
    return {
        'area_m2': round(total_area_m2, 2),
        'area_ha': round(total_area_ha, 4),
        'carbon_tons': round(total_carbon, 2),
        'co2_tons': round(total_co2, 2)
    }

def process_image_detection(image_data=None, file_path=None, confidence=0.3, pixel_to_meter=0.5, source="firebase_auto"):
    """Core detection function - ALWAYS returns annotated image in base64."""
    if model is None:
        return {'error': 'Model not loaded', 'success': False}
    
    try:
        # Handle image input
        if image_data:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"firebase_{timestamp}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
        elif file_path:
            filepath = file_path
            filename = os.path.basename(filepath)
        else:
            return {'error': 'No image provided', 'success': False}
        
        # Run YOLO detection
        results = model.predict(filepath, conf=confidence)
        
        detections_list = []
        total_area_pixels = 0
        
        # Load image for annotation
        image = cv2.imread(filepath)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process detections
        for r in results:
            boxes = r.boxes
            names = r.names
            
            if boxes is not None and len(boxes) > 0:
                # Create annotations
                detections = sv.Detections.from_ultralytics(r)
                
                box_annotator = sv.BoxAnnotator(
                    thickness=3,
                    color=sv.Color(r=0, g=255, b=0)
                )
                label_annotator = sv.LabelAnnotator(
                    text_color=sv.Color(r=255, g=255, b=255),
                    text_scale=0.5,
                    text_thickness=2
                )
                
                labels = [
                    f"{names[int(class_id)]} {conf:.0%}"
                    for class_id, conf in zip(detections.class_id, detections.confidence)
                ]
                
                # Annotate image
                annotated_image = box_annotator.annotate(image_rgb.copy(), detections)
                annotated_image = label_annotator.annotate(annotated_image, detections, labels)
                
                # Process detection data
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
            else:
                # No detections - use original image
                annotated_image = image_rgb
        
        # Save annotated image
        result_filename = f"result_{filename}"
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
        cv2.imwrite(result_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        
        # Encode image to base64
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Calculate carbon metrics
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
            },
            'source': source,
            'processing_timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Detection completed: {len(detections_list)} mangroves, image encoded: {len(img_base64)} bytes")
        
        return response
    
    except Exception as e:
        print(f"❌ Detection error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'success': False}

def monitor_firebase():
    """Background thread to monitor Firebase for new images."""
    global last_processed_timestamp, firebase_monitor_running
    
    print("🔥 Firebase monitoring started...")
    print(f"🎯 Auto-detection confidence threshold: {FIREBASE_AUTO_CONFIDENCE}")
    firebase_monitor_running = True
    initial_load = True
    
    while firebase_monitor_running:
        try:
            image_data, timestamp, image_key = fetch_latest_image_from_firebase()
            
            if image_data and timestamp:
                # Process on first load OR when new image detected
                if initial_load or last_processed_timestamp is None or timestamp > last_processed_timestamp:
                    if initial_load:
                        print(f"🔄 Loading latest Firebase image on startup...")
                        initial_load = False
                    else:
                        print(f"🆕 New image detected! Timestamp: {timestamp}")
                    
                    last_processed_timestamp = timestamp
                    
                    # USE 0.1 CONFIDENCE FOR AUTOMATIC FIREBASE DETECTION
                    result = process_image_detection(
                        image_data=image_data,
                        confidence=FIREBASE_AUTO_CONFIDENCE,  # 0.1 threshold
                        pixel_to_meter=0.5,
                        source="firebase_auto"
                    )
                    
                    if result and result.get('success'):
                        print(f"✅ Detection completed: {result['total_detections']} mangroves found")
                        # Send to Firebase immediately
                        send_results_to_firebase(result)
                    else:
                        print(f"❌ Detection failed: {result.get('error', 'Unknown error')}")
                        
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"❌ Error in Firebase monitor: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring services"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'firebase_monitor': firebase_monitor_running,
        'auto_confidence_threshold': FIREBASE_AUTO_CONFIDENCE
    })

@app.route('/get_latest_detection')
def get_latest_detection():
    """Fetch latest detection directly from Firebase (no memory cache)."""
    try:
        firebase_url = f"{FIREBASE_HOST}{FIREBASE_OUTPUT_PATH}/latest_detection.json?auth={FIREBASE_AUTH}"
        response = requests.get(firebase_url, timeout=10)
        
        if response.status_code == 200 and response.json():
            data = response.json()
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No detection available yet'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/predict_manual', methods=['POST'])
def predict_manual():
    """Manual upload endpoint - separate from auto-detection."""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"manual_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Manual uploads can use custom confidence (default 0.3)
        confidence = float(request.form.get('confidence', 0.3))
        pixel_to_meter = float(request.form.get('pixel_to_meter', 0.5))
        
        result = process_image_detection(
            file_path=filepath,
            confidence=confidence,
            pixel_to_meter=pixel_to_meter,
            source="manual_upload"
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/firebase_status')
def firebase_status():
    """Check Firebase monitoring status."""
    return jsonify({
        'monitoring_active': firebase_monitor_running,
        'last_processed_timestamp': last_processed_timestamp,
        'auto_confidence_threshold': FIREBASE_AUTO_CONFIDENCE
    })

if __name__ == '__main__':
    # Start Firebase monitor thread
    monitor_thread = threading.Thread(target=monitor_firebase, daemon=True)
    monitor_thread.start()
    
    print("="*70)
    print("🌳 MANGROVE DETECTION SYSTEM - FIREBASE DIRECT MODE")
    print("="*70)
    print("🔥 Firebase Auto-Monitor: ACTIVE")
    print(f"🎯 Auto-Detection Confidence: {FIREBASE_AUTO_CONFIDENCE} (10%)")
    print("📊 Data Source: Firebase /MVR/latest_detection")
    print("📁 Detection History: /MVR/history/")
    print("🔄 Update Interval: 5 seconds")
    print("💾 No Local Memory - All data from Firebase")
    print("📤 Manual Upload: Separate from auto-detection (default 0.3)")
    print("💡 Startup: Loads last Firebase image immediately")
    print("="*70)
    
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5100))
    
    # Run the app
    app.run(host='0.0.0.0', port=port)