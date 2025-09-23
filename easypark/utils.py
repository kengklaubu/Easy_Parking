import time
from django.apps import apps
DETECTION_DELAY = 3  # กำหนดค่าหน่วงเวลาเป็น 3 วินาที
# ใช้ dictionary เพื่อเก็บเวลาเริ่มต้นของแต่ละช่องจอด
spot_timers = {}

def update_parking_status(rois, detections, location_name):
    """
    อัปเดตสถานะช่องจอดรถในฐานข้อมูล (เพิ่มการหน่วงเวลา 3 วินาที)
    """
    ParkingSpot = apps.get_model('easypark', 'ParkingSpot')
    ParkingLocation = apps.get_model('easypark', 'ParkingLocation')

    try:
        location = ParkingLocation.objects.get(id=int(location_name)) if str(location_name).isdigit() \
            else ParkingLocation.objects.get(name=location_name)
    except ParkingLocation.DoesNotExist:
        print(f"❌ Location '{location_name}' does not exist.")
        return

    print(f"🔍 Updating parking status for location: {location.name} (ID {location.id})")

    current_time = time.time()

    for roi in rois:
        spot_number, x, y, w, h = roi
        detected = False

        for _, row in detections.iterrows():
            label = row['name']
            
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            if label == 'car':
                if (x1 < x + w) and (x2 > x) and (y1 < y + h) and (y2 > y):
                    detected = True
                    break


        

        # ตรวจสอบว่ามีรถในช่องจอดต่อเนื่อง 3 วินาทีหรือไม่
        if detected:
            if spot_number not in spot_timers:
                spot_timers[spot_number] = current_time  # บันทึกเวลาครั้งแรกที่เจอรถ
            elif current_time - spot_timers[spot_number] >= DETECTION_DELAY:  # ถ้าเกิน 3 วินาที ค่อยอัปเดตสถานะ
                try:
                    parking_spot = ParkingSpot.objects.get(spot_number=spot_number, location=location)
                    parking_spot.is_available = False  # มีรถจอด
                    parking_spot.save()
                    print(f"✅ Updated spot {spot_number}: Occupied")
                except ParkingSpot.DoesNotExist:
                    print(f"❌ Parking spot {spot_number} in location '{location.name}' does not exist.")
        else:
            spot_timers.pop(spot_number, None)  # ถ้ารถออกก่อน 3 วิ ให้ลบ timer ออก

            try:
                parking_spot = ParkingSpot.objects.get(spot_number=spot_number, location=location)
                parking_spot.is_available = True  # ช่องว่างอยู่
                parking_spot.save()
                print(f"✅ Updated spot {spot_number}: Available")
            except ParkingSpot.DoesNotExist:
                print(f"❌ Parking spot {spot_number} in location '{location.name}' does not exist.")

        

