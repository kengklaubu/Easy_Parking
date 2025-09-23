# easypark/video_stream.py

import cv2
import torch
import threading
import numpy as np
from easypark.models import ParkingLocation, ParkingSpot, ROI
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse

# โหลดโมเดล YOLOv5
def load_model():
    try:
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        return model
    except Exception as e:
        print(f"Error loading YOLOv5 model: {e}")
        return None

model = load_model()

def generate_frames(location):  
    """ สตรีมวิดีโอจากกล้องของสถานที่ และวาด ROIs ตามข้อมูลในฐานข้อมูล """
    
    cap = cv2.VideoCapture(location.camera_url)  # เปิดกล้อง
    if not cap.isOpened():
        print(f"Cannot connect to camera: {location.camera_url}")
        return
    
    while True:
        success, frame = cap.read()
        if not success:
            break

        # ✅ แปลงเฟรมเป็น numpy array (ใช้สำหรับ YOLOv5)
        frame = np.array(frame)

        # ✅ ดึง ROIs จากฐานข้อมูลตามสถานที่
        rois = ROI.objects.filter(location=location)

        # ✅ วาด ROIs (กรอบจอดรถ)
        for roi in rois:
            x, y, w, h = int(roi.x_position), int(roi.y_position), int(roi.width), int(roi.height)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # ✅ สีเขียว
            #cv2.circle(frame,(x,y), 5, (255, 165, 0), -1)

        # ✅ ตรวจจับวัตถุด้วย YOLOv5
        if model is not None:
            results = model(frame)  # 🔹 ตรวจจับรถ
            detections = results.pandas().xyxy[0]  # 🔹 ดึงผลลัพธ์ในรูปแบบ pandas DataFrame

            # ✅ วาด bounding box ของรถที่ตรวจจับได้
            for _, row in detections.iterrows():
                x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                #cv2.circle(frame,(x1,y1), 5, (255, 0, 0), -1)
                #cv2.circle(frame,(x2,y2), 5, (153, 165, 0), -1)
                conf, cls = row['confidence'], row['name']

                cv2.rectangle(frame, (x1, y1),(x2, y2),(255, 0, 0), 2)
                #cv2.rectangle(frame, (153, 0, 0), 2)
                cv2.putText(frame, f"{cls} {conf:.2f}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # ✅ แปลงภาพเป็นไฟล์ JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
