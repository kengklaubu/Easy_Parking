import json
import requests
import csv
from django.shortcuts import render
import csv
import os
from django.conf import settings

def get_sheet_data():
    file_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'parking_data.csv')  # ตัวอย่างที่เก็บไฟล์ใน static/data/
    
    data = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)
    except FileNotFoundError:
        print("ไฟล์ CSV ไม่พบในโปรเจค")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    
    return data

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'manager':
                return redirect('manager_location_selection')  # เปลี่ยนเป็นหน้าเลือกลานจอดรถ
            else:
                return redirect('user_dashboard')
        else:
            return render(request, 'easypark/login.html', {'error': 'Invalid login credentials'})

    return render(request, 'easypark/login.html')




from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login
from .models import CustomUser  

def register_page(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  
            user.set_password(form.cleaned_data['password'])  
            user.save()  
            login(request, user)  
            return redirect('homepage')  
    else:
        form = RegisterForm()
    
    return render(request, 'easypark/register.html', {'form': form})



from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

# ฟังก์ชันนี้ใช้ตรวจสอบบทบาท
def is_admin(user):
    return user.role == 'admin'


# ฟังก์ชันนี้จะทำให้แค่แอดมินสามารถเข้าใช้งาน
from django.contrib.auth.decorators import login_required
from .models import CustomUser, ParkingLocation
@login_required
@user_passes_test(is_admin)
@login_required
def admin_dashboard(request):
    users = CustomUser.objects.all()  # ดึงผู้ใช้ทั้งหมด
    total_users = users.count()  # นับจำนวนผู้ใช้ทั้งหมด
    locations = ParkingLocation.objects.all()
    total_locations = locations.count()

    context = {
        'users': users,
        'total_users': total_users,
        'total_locations': total_locations,
    }
    return render(request, 'easypark/admin_dashboard.html', context)

@login_required
def manager_location_selection(request):
    # ตรวจสอบสิทธิ์ว่าเป็น manager
    if request.user.role != 'manager':
        return HttpResponseForbidden("You do not have permission to access this page.")
        
    # ดึงข้อมูลลานจอดรถทั้งหมดที่ manager เป็นเจ้าของ
    locations = ParkingLocation.objects.filter(owner=request.user)
    
    return render(request, 'easypark/manager_locations.html', {
        'locations': locations
    })

@login_required
def manager_dashboard(request, location_id=None):
    # ตรวจสอบสิทธิ์ว่าเป็น manager
    rois = ROI.objects.all()
    if request.user.role != 'manager':
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # กรณีที่มีการส่ง location_id มาใน URL
    if location_id is not None:
        try:
            location = ParkingLocation.objects.get(id=location_id, owner=request.user)
        except ParkingLocation.DoesNotExist:
            return HttpResponseForbidden("You do not have permission to access this location.")
    # กรณีที่มีการส่ง location_id มาทาง GET parameter
    elif 'location_id' in request.GET:
        try:
            location_id = request.GET['location_id']
            location = ParkingLocation.objects.get(id=location_id, owner=request.user)
        except ParkingLocation.DoesNotExist:
            return HttpResponseForbidden("You do not have permission to access this location.")
    # กรณีที่ไม่มี location_id ใดๆ ให้ redirect ไปยังหน้าเลือกลานจอดรถ
    else:
        return redirect('manager_location_selection')
    
    # ดึงข้อมูลที่ต้องการแสดงในหน้า dashboard
    reservations = Reservation.objects.filter(parking_spot__location=location)
    bookings = Booking.objects.filter(parking_spot__location=location)
    parking_spots = ParkingSpot.objects.filter(location=location)
    rois = ROI.objects.filter(location=location)
    
    return render(request, 'easypark/manager_dashboard.html', {
        'location': location,
        'reservations': reservations,
        'parking_spots': parking_spots,
        'current_location': location,
        'bookings': bookings,
        'rois': rois,
        'user_locations': ParkingLocation.objects.filter(owner=request.user)  # เพื่อทำ dropdown หรือ sidebar
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ParkingLocation
from .forms import ParkingLocationForm

@login_required
def manager_add_location(request):
    location = None
    if request.method == "POST":
        form = ParkingLocationForm(request.POST, request.FILES)
        if form.is_valid():
            # ตรวจสอบว่ามีรูปภาพหรือไม่
            if 'image' not in request.FILES:
                form.add_error('image', 'กรุณาเลือกรูปภาพสถานที่')
                messages.error(request, "❌ กรุณาเลือกรูปภาพสถานที่")
                return render(request, 'easypark/manager_add_location.html', {
                    'form': form,
                    'location': location
                })
                
            location = form.save(commit=False)
            location.owner = request.user
            location.save()
            messages.success(request, "✅ เพิ่มสถานที่จอดรถเรียบร้อยแล้ว!")
            return redirect('manager_dashboard', location_id=location.id)
        else:
            # แสดงข้อผิดพลาดของฟอร์ม
            messages.error(request, "❌ พบข้อผิดพลาดในฟอร์ม กรุณาตรวจสอบข้อมูล")
    else:
        form = ParkingLocationForm()

    return render(request, 'easypark/manager_add_location.html', {
        'form': form,
        'location': location
    })




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def update_parking_spot_position(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            spot_id = data.get("spot_id")
            x_position = data.get("x_position")
            y_position = data.get("y_position")

            spot = ParkingSpot.objects.get(id=spot_id)
            spot.x_position = x_position
            spot.y_position = y_position
            spot.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"})






@login_required
def cancel_reservation(request, reservation_id):
    # ตรวจสอบว่าเป็น Manager
    if request.user.role != 'manager':
        return redirect('homepage')

    try:
        reservation = Reservation.objects.get(id=reservation_id)
        reservation.status = 'cancelled'  
        reservation.save()
        return redirect('manager_dashboard')  
    except Reservation.DoesNotExist:
        return redirect('manager_dashboard')  
    


from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import ParkingSpot

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import ParkingSpot

@login_required
def suspend_parking_spot(request, spot_id):
    # ตรวจสอบว่า user มีสิทธิ์เป็น 'manager'
    if request.user.role != 'manager':
        return JsonResponse({'success': False, 'message': 'Access Denied'}, status=403)

    try:
        # ดึงข้อมูลช่องจอดที่ตรงกับ spot_id
        parking_spot = ParkingSpot.objects.get(id=spot_id)

        # สลับสถานะความพร้อมใช้งานของช่องจอด
        parking_spot.is_available = not parking_spot.is_available
        parking_spot.save()

        # ส่งผลลัพธ์กลับในรูปแบบ JSON
        return JsonResponse({
            'success': True,
            'is_available': parking_spot.is_available
        })
    except ParkingSpot.DoesNotExist:
        # หากไม่พบช่องจอด
        return JsonResponse({'success': False, 'message': 'Parking spot not found'}, status=404)
    except Exception as e:
        # จัดการข้อผิดพลาดอื่น ๆ
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

    

    



from django.http import JsonResponse
from .models import ParkingLocation
from .detection_service import detect_cars  # ฟังก์ชันตรวจจับที่เชื่อมต่อกับกล้อง

def get_camera_url(location_name):
    try:
        location = ParkingLocation.objects.get(name=location_name)
        return location.camera_url
    except ParkingLocation.DoesNotExist:
        print(f"Location {location_name} does not exist.")
        return None



import time
import logging
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.apps import apps
from .detection_service import start_detection_in_background

logger = logging.getLogger(__name__)  # ใช้ logger แทน print()

def start_detection(request):
    start_time = time.time()

    # รองรับทั้ง `location` และ `location_id`
    location_param = request.GET.get('location') or request.GET.get('location_id', '').strip()
    print(f"Received location_id: {location_param}")  # ✅ ตรวจสอบค่า
    if not location_param:
        logger.warning("No location provided in request.")
        return JsonResponse({"status": "error", "message": "Location parameter is required."}, status=400)

    logger.debug(f"Received location parameter: {location_param}")

    ParkingLocation = apps.get_model('easypark', 'ParkingLocation')

    try:
        try:
            location_id = int(location_param)
            location = get_object_or_404(ParkingLocation, id=location_id)
        except ValueError:
            location = get_object_or_404(ParkingLocation, name=location_param)

        logger.debug(f"Found location: {location.id}, Camera URL: {location.camera_url}")

        if not location.camera_url:
            logger.warning(f"Cannot find camera URL for location: {location.id}")
            return JsonResponse({
                "status": "error",
                "message": f"Cannot find camera URL for location: {location.name}"
            }, status=404)
        logger.debug(f"Camera URL for {location.name}: {location.camera_url}")


        logger.debug(f"Starting detection for location ID: {location.id}")
        start_detection_in_background(location.id)


        end_time = time.time()
        logger.info(f"start_detection() took {end_time - start_time:.2f} seconds")

        return JsonResponse({"status": "success", "message": f"Detection started for location: {location.name}"})

    except Exception as e:
        logger.error(f"Error in start_detection: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)















from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404
from .models import ParkingLocation
import cv2

def generate_raw_frames(camera_url):
    """
    สตรีมวิดีโอสดแบบปกติ (ไม่มี Bounding Box)
    """
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Cannot connect to camera: {camera_url}")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

def stream_video(request, location_id):
    """
    สตรีมวิดีโอสด (ไม่มี Bounding Box)
    """
    location = get_object_or_404(ParkingLocation, id=location_id)
    camera_url = location.camera_url

    return StreamingHttpResponse(
        generate_raw_frames(camera_url),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )



from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from easypark.models import ParkingLocation
from easypark.video_stream import generate_frames  # Import ฟังก์ชัน generate_frames

def video_feed(request, location_id):
    """
    สตรีมวิดีโอจากกล้องของสถานที่ที่เลือก
    """
    location = get_object_or_404(ParkingLocation, id=location_id)  # ดึงข้อมูลสถานที่
    camera_url = location.camera_url  # ดึง URL ของกล้อง

    if not camera_url:
        return StreamingHttpResponse(b'Error: Camera URL not found', content_type="text/plain")

    return StreamingHttpResponse(
        generate_frames(location),  # ✅ ส่งทั้ง `camera_url` และ `location.name`
        content_type="multipart/x-mixed-replace; boundary=frame"
    )











from django.http import JsonResponse
from .models import ParkingSpot

def get_parking_spots(request, location_id):
    parking_spots = ParkingSpot.objects.filter(location_id=location_id)

    spots_data = []
    for spot in parking_spots:
        reserved_by = spot.reserved_by.username if spot.reserved_by else 'None'
        license_plate = spot.license_plate if spot.license_plate else 'N/A'
        spots_data.append({
            'spot_number': spot.spot_number,
            'is_available': spot.is_available,
            'reserved_by': reserved_by,
            'license_plate': license_plate,
            'id': spot.id  # ทำให้มั่นใจว่า spot.id ถูกส่งมาด้วย
        })
    
    return JsonResponse({'parking_spots': spots_data})












from django.shortcuts import render, get_object_or_404
from .models import ParkingLocation

#def locations_page(request):
    #return render(request, 'easypark/locations.html')

def parking_location(request, location_slug):
    location = get_object_or_404(ParkingLocation, slug=location_slug)
    spots = location.parking_spots.all() 
    return render(request, 'easypark/parking_location.html', {'location': location, 'spots': spots})



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Reservation,Booking # นำเข้า Model ที่เก็บประวัติการจอง

@login_required
def profile(request):
    reservations = Reservation.objects.filter(user=request.user)  # ดึงประวัติการจองของผู้ใช้
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'easypark/profile.html', {'reservations': reservations,'bookings':bookings})

@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    return redirect('profile')



from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

@login_required
def view_reservation_history(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
    # Logic สำหรับผู้ดูแลระบบ


from django.shortcuts import render
from django.http import HttpResponseForbidden

def manage_parking_spots(request):
    if request.user.role != 'manager':
        return HttpResponseForbidden("คุณไม่มีสิทธิ์จัดการที่จอดรถ")
    # Logic สำหรับเจ้าของร้าน (สถานที่)
    return render(request, 'manage_parking_spots.html')




#ดึงข้อมูลทั้งหมด
#from django.shortcuts import render
#from .models import Reservation
#def reservation_history(request):
    # ตรวจสอบว่า Query ครบทุกข้อมูลในตาราง Reservation
    #reservations = Reservation.objects.select_related('location').all()
    #return render(request, 'reservation_history.html', {'reservations': reservations})





    
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('login_page')

# easypark/views.py

from django.shortcuts import render

def password_reset(request):
    # แสดงหน้า password reset
    return render(request, 'easypark/password_reset1221.html')





from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import os
import csv
from django.conf import settings

def homepage(request):
    locations = ParkingLocation.objects.all()
    # เลือกสถานที่แรกตามลำดับ id (จะได้ None ถ้าไม่มีสถานที่)
    default_location = locations.order_by('id').first()

    if request.user.is_authenticated:
        # ตรวจสอบ role ของผู้ใช้ที่ล็อกอิน
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return redirect('admin_dashboard')  # เปลี่ยนไปหน้าแดชบอร์ดของแอดมิน
        elif role == 'manager':
            # พาไปยังหน้าเลือกลานจอดรถแทนการพาไปที่ลานจอดรถแรกโดยตรง
            return redirect('manager_location_selection')
        else:
            # สำหรับผู้ใช้ทั่วไป
            return render(request, 'easypark/home.html', {
                'locations': locations,
                'default_location': default_location
            })
    else:
        # ถ้าผู้ใช้ไม่ได้ล็อกอิน ก็ให้แสดงหน้า homepage
        return render(request, 'easypark/home.html', {
            'locations': locations,
            'default_location': default_location
        })


    








from django.http import JsonResponse
from .models import ParkingSpot

def get_parking_status(request):
    # ดึง location_id จาก request
    location_id = request.GET.get('location_id')

    # ตรวจสอบว่า location_id ถูกส่งมาหรือไม่
    if not location_id:
        return JsonResponse({'error': 'กรุณาระบุ location_id'}, status=400)

    # ตรวจสอบว่า location_id เป็นตัวเลขหรือไม่
    try:
        location_id = int(location_id)
    except ValueError:
        return JsonResponse({'error': 'location_id ต้องเป็นตัวเลข'}, status=400)

    # ดึงข้อมูลจากฐานข้อมูล
    spots = ParkingSpot.objects.filter(location_id=location_id)
    if not spots.exists():  # กรณีไม่มีข้อมูลใน location_id นี้
        return JsonResponse({'error': 'ไม่มีข้อมูลช่องจอดสำหรับ location_id นี้'}, status=404)

    result = []
    for spot in spots:
        # ตรวจสอบการจองล่าสุด
        booking = Booking.objects.filter(parking_spot=spot).order_by('-created_at').first()
        status = 'available'
        
        if booking and booking.status in ['active', 'pending']:
            status = booking.status
        
        result.append({
            'id': spot.id,
            'spot_number': spot.spot_number,
            'is_available': spot.is_available,
            'status': status
        })
    
    return JsonResponse(result, safe=False)




# easypark/views.py







from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import ParkingLocation, ParkingSpot

def get_spot_details(request):
    location_id = request.GET.get('location_id')
    spot_id = request.GET.get('spot_id')

    # ตรวจสอบค่าที่ส่งเข้ามา
    if not location_id or not spot_id:
        return JsonResponse({'error': 'Missing location_id or spot_id'}, status=400)

    try:
        location = get_object_or_404(ParkingLocation, id=location_id)
        spot = get_object_or_404(ParkingSpot, id=spot_id, location=location)
    except:
        return JsonResponse({'error': 'Invalid location or spot ID'}, status=400)

    # ตรวจสอบการจองล่าสุดของช่องจอดนี้
    booking = Booking.objects.filter(parking_spot=spot).order_by('-created_at').first()
    
    status = 'available'
    if booking and booking.status in ['active', 'pending']:
        status = booking.status
    
    # ส่งข้อมูลเพิ่มเติมเกี่ยวกับสถานะ
    return JsonResponse({
        'spot_number': spot.spot_number,
        'is_available': spot.is_available,
        'status': status,  # เพิ่มสถานะ
        'reserved_by': spot.reserved_by.username if spot.reserved_by else None,
    })





    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
@login_required
def parking_detail(request, spot_id):
    # ค้นหาข้อมูลที่จอดรถจาก ID ที่ส่งเข้ามา
    parking_spot = ParkingSpot.objects.get(id=spot_id)

    context = {
        'parking_spot': parking_spot,
    }
    return render(request, 'easypark/parking_details.html', context)



# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from .models import ParkingSpot
# @login_required
# def reserve_parking_spot(request, spot_id):
#     spot = ParkingSpot.objects.get(id=spot_id)

#     if spot.is_available:
#         spot.is_available = False
#         spot.reserved_by = request.user  # เก็บข้อมูลผู้ใช้งานที่ทำการจอง
#         spot.save()

#         return redirect('parking_detail')  # หลังจากจองเสร็จให้ไปยังหน้า parking_detail
#     else:
#         return render(request, 'error_page.html', {'message': 'ช่องจอดนี้ถูกจองแล้ว'})
    



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ParkingSpot, Booking, ParkingLocation

from threading import Timer

@login_required
def reserve_page(request, spot_number):
    location_id = request.GET.get('location_id')

    try:
        parking_spot = ParkingSpot.objects.get(spot_number=spot_number, location_id=location_id)
    except ParkingSpot.DoesNotExist:
        return render(request, 'easypark/error.html', {'message': 'ไม่พบที่จอดนี้ในสถานที่นี้'})
    except ParkingSpot.MultipleObjectsReturned:
        return render(request, 'easypark/error.html', {'message': 'มีที่จอดหลายรายการในสถานที่นี้ กรุณาติดต่อผู้ดูแล'})

    if request.method == 'POST':
        start_time = request.POST.get('start_time', '08:00:00')
        end_time = request.POST.get('end_time', '12:00:00')

        if not parking_spot.is_available:
            return render(request, 'easypark/error.html', {'message': 'ที่จอดนี้ถูกจองแล้ว'})

        booking = Booking.objects.create(
            user=request.user,
            parking_spot=parking_spot,
            location=parking_spot.location,
            reservation_date=timezone.now().date(),
            reservation_start_time=start_time,
            reservation_end_time=end_time,
            status='pending',  # เปลี่ยนจาก active เป็น pending แสดงถึงว่ากำลังรอให้รถเข้า
            reserved_at=timezone.now()
        )

        parking_spot.is_available = False
        parking_spot.reserved_by = request.user
        parking_spot.save()

        Timer(300, auto_cancel_booking, args=[booking.id]).start()

        return redirect('profile')

    return render(request, 'easypark/reserve_page.html', {
        'spot': parking_spot,
        'spot_number': parking_spot.spot_number,
    })

def auto_cancel_booking(booking_id):
    from django.utils import timezone

    try:
        booking = Booking.objects.get(id=booking_id)
        parking_spot = booking.parking_spot

        # เช็คว่าเกิน 5 นาทีแล้วยังไม่มีรถเข้าจอดจริงหรือไม่
        if booking.status == 'pending' and parking_spot.is_available:
            booking.status = 'cancelled'
            booking.cancelled_at = timezone.now()
            booking.save()

            # คืนสถานะให้ที่จอดเป็นว่าง
            parking_spot.is_available = True
            parking_spot.reserved_by = None
            parking_spot.save()

            print(f"❌ Reservation {booking.id} was automatically cancelled due to no arrival within 5 minutes.")
    except Booking.DoesNotExist:
        print("⚠️ Booking not found for auto-cancellation.")



def success_page(request):
    return render(request, 'easypark/success_page.html')





from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Booking, ParkingLocation
from django.utils import timezone

@login_required
def cancel_booking(request, booking_id):
    print(f"Booking ID: {booking_id}")
    booking = get_object_or_404(Booking, id=booking_id)

    # ตรวจสอบสิทธิ์การยกเลิก
    if booking.user == request.user:  # ผู้จอง
        role = 'user'
    elif request.user.is_manager() and booking.parking_spot.location.owner == request.user:  # Manager
        role = 'manager'
    else:
        messages.error(request, "⚠️ คุณไม่มีสิทธิ์ยกเลิกการจองนี้")
        return redirect('manager_dashboard', location_id=booking.parking_spot.location.id)

    # ยกเลิกการจอง
    if booking.status == 'active' or booking.status == 'pending':
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.parking_spot.is_available = True
        booking.parking_spot.reserved_by = None
        booking.parking_spot.save()
        booking.save()

        messages.success(request, f"🚫 {role.capitalize()} ยกเลิกการจองสำเร็จ สำหรับที่จอด #{booking.parking_spot.spot_number}")
    else:
        messages.warning(request, "❌ ไม่สามารถยกเลิกได้ เพราะการจองนี้ไม่อยู่ในสถานะ Active")

    # กลับไปยังหน้าเดิมตาม role
    if role == 'manager':
        return redirect('manager_dashboard', location_id=booking.parking_spot.location.id)
    else:
        return redirect('profile')  # หน้าแดชบอร์ดของผู้ใช้ทั่วไป









from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import ParkingSpot, ParkingLocation

@login_required
def sc_parking(request, location_id=None):  # เพิ่ม location_id
    locations = ParkingLocation.objects.all()
    print("🔍 Location ID received:", location_id)  # ตรวจสอบค่าใน Terminal

    # กำหนดค่า location_id ตามลำดับความสำคัญ (URL > POST > ค่าเริ่มต้น)
    if location_id is None:
        location_id = request.POST.get('location') or request.GET.get('location_id')

    # แปลงค่า location_id เป็น int และตรวจสอบว่ามีอยู่จริงหรือไม่
    try:
        location_id = int(location_id)
        selected_location = get_object_or_404(ParkingLocation, pk=location_id)
    except (ValueError, TypeError, ParkingLocation.DoesNotExist):
        selected_location = locations.first()  # ใช้ค่าเริ่มต้นหากไม่มีค่า

    # ดึงข้อมูลที่จอดรถของสถานที่ที่เลือก
    spots = ParkingSpot.objects.filter(location=selected_location).select_related('location')

    context = {
        'spots': spots,
        'location': selected_location,
        'locations': locations,
    }
    return render(request, 'easypark/sc_parking.html', context)




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import ParkingSpot, ParkingLocation

@login_required
def add_parking_spot(request, location_id):
    location = get_object_or_404(ParkingLocation, id=location_id)

    # ตรวจสอบว่าเป็นเจ้าของที่จอดรถ
    if request.user != location.owner:
        return JsonResponse({"success": False, "error": "คุณไม่มีสิทธิ์เพิ่มช่องจอดที่นี่"}, status=403)

    if request.method == "POST":
        spot_number = request.POST.get("spot_number")

        if not spot_number or not spot_number.isdigit():
            return JsonResponse({"success": False, "error": "กรุณาระบุหมายเลขช่องจอดที่ถูกต้อง"}, status=400)

        spot_number = int(spot_number)

        if ParkingSpot.objects.filter(location=location, spot_number=spot_number).exists():
            return JsonResponse({"success": False, "error": "❌ ช่องจอดนี้มีอยู่แล้ว"}, status=400)

        # บันทึกข้อมูลลงฐานข้อมูล
        new_spot = ParkingSpot.objects.create(
            location=location,
            spot_number=spot_number,
            is_available=True
        )

        return JsonResponse({
            "success": True,
            "message": "✅ เพิ่มช่องจอดเรียบร้อยแล้ว!",
            "spot_id": new_spot.id,
            "spot_number": new_spot.spot_number
        })

    return JsonResponse({"success": False, "error": "❌ วิธีการส่งข้อมูลไม่ถูกต้อง"}, status=400)








from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ParkingSpot

@csrf_exempt  # ✅ ปิด CSRF ตรวจสอบเฉพาะ POST
def delete_parking_spot(request, spot_id):
    if request.method == "POST":
        try:
            spot = ParkingSpot.objects.get(id=spot_id)
            spot.delete()
            return JsonResponse({"success": True, "message": "ช่องจอดถูกลบแล้ว!"})
        except ParkingSpot.DoesNotExist:
            return JsonResponse({"success": False, "error": "ไม่พบช่องจอดที่ต้องการลบ!"})
    return JsonResponse({"success": False, "error": "ไม่รองรับการร้องขอแบบนี้!"})

from django.shortcuts import render
from .models import CustomUser # ตรวจสอบให้แน่ใจว่าใช้ Model ที่ถูกต้อง

def user_management(request):
    user_roles = CustomUser.ROLE_CHOICES
    users = CustomUser.objects.all()
    return render(request, 'admin/user_management.html', {'users': users, 'user_roles': user_roles})


from django.shortcuts import render
from .models import ParkingLocation, CustomUser # ตรวจสอบให้แน่ใจว่าใช้ Model ที่ถูกต้อง

def locations_management(request):
    users = CustomUser.objects.all()
    locations = ParkingLocation.objects.all()
    return render(request, 'admin/locations_management.html', {'locations': locations, 'users': users})



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import CustomUser  # ตรวจสอบให้แน่ใจว่าใช้ Model ที่ถูกต้อง

@csrf_exempt
def update_user(request, user_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user = CustomUser.objects.get(id=user_id)
            user.username = data["username"]
            user.email = data["email"]
            user.role = data["role"]
            user.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser  # ใช้ Model ที่ถูกต้อง
import json

@csrf_exempt
def delete_user(request, user_id):
    if request.method == "DELETE":
        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return JsonResponse({"success": True})
        except CustomUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "ไม่พบผู้ใช้"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


@csrf_exempt
def add_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_user = CustomUser.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                role=data["role"]
            )
            return JsonResponse({"success": True, "user_id": new_user.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)





from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import ParkingLocation
from django.contrib.auth import get_user_model
User = get_user_model()

@csrf_exempt
def edit_location(request, location_id):
    location = get_object_or_404(ParkingLocation, id=location_id)
    if request.method == "POST":
        # print("📥 ข้อมูลที่รับมา:", request.POST)  # ✅ Debug
        # print("📷 ไฟล์ที่แนบมา:", request.FILES)

        try:
            location.name = request.POST.get("name")
            location.description = request.POST.get("description")
            location.total_spots = request.POST.get("total_spots")
            location.available_spots = request.POST.get("available_spots")
            location.camera_url = request.POST.get("camera_url")

            owner_id = request.POST.get("owner")
            if owner_id:
                location.owner = get_object_or_404(User, id=owner_id)

            if "image" in request.FILES:
                location.image = request.FILES["image"]

            location.save()
            return JsonResponse({"success": True, "message": "สถานที่ถูกแก้ไขแล้ว"})
        except Exception as e:
            print("❌ Error:", str(e))
            return JsonResponse({"success": False, "error": str(e)})







@csrf_exempt
def delete_location(request, location_id):
    location = get_object_or_404(ParkingLocation, id=location_id)
    location.delete()
    return JsonResponse({"success": True, "message": "สถานที่ถูกลบแล้ว"})




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import ParkingLocation

@csrf_exempt
def get_location(request, location_id):
    location = get_object_or_404(ParkingLocation, id=location_id)
    
    data = {
        "id": location.id,
        "name": location.name,
        "description": location.description or "",
        "total_spots": location.total_spots,
        "available_spots": location.available_spots,
        "camera_url": location.camera_url or "",
        "owner": location.owner.id if location.owner else "",
        "image_url": location.image.url if location.image else None  # ✅ เช็คก่อนว่ามีภาพไหม
    }
    
    return JsonResponse({"success": True, "location": data})


from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ParkingLocation
from .forms import AdminLocationForm
from django.contrib import messages
from django.utils.text import slugify
@login_required
@csrf_exempt
def admin_add_location(request):
    """ให้ Admin เพิ่มสถานที่ โดยเลือกเจ้าของสถานที่เอง"""
    if request.method == "POST":
        try:
            # print("📥 ข้อมูลที่รับมา:", request.POST)
            # print("📷 ไฟล์ที่แนบมา:", request.FILES)

            name = request.POST.get("name")
            if not name:
                return JsonResponse({"success": False, "error": "Missing name"})

            description = request.POST.get("description", "")
            total_spots = request.POST.get("total_spots", "0")
            available_spots = request.POST.get("available_spots", "0")
            camera_url = request.POST.get("camera_url", "")
            owner_id = request.POST.get("owner")

            if not owner_id:
                return JsonResponse({"success": False, "error": "Missing owner ID"})

            owner = get_object_or_404(User, id=owner_id)
            image = request.FILES.get("image")
            
            # ตรวจสอบว่ามีการอัปโหลดรูปภาพหรือไม่
            if not image:
                return JsonResponse({"success": False, "error": "กรุณาอัปโหลดรูปภาพของสถานที่"})

            # ✅ ป้องกันค่า slug ซ้ำ
            base_slug = slugify(name)
            unique_slug = base_slug
            counter = 1
            while ParkingLocation.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1

            # ✅ บันทึกข้อมูลใหม่
            location = ParkingLocation(
                name=name,
                slug=unique_slug,  # ✅ ใช้ slug ที่ไม่ซ้ำ
                description=description,
                total_spots=int(total_spots),
                available_spots=int(available_spots),
                camera_url=camera_url,
                owner=owner,
                image=image
            )
            location.save()

            # ✅ ส่งข้อมูลกลับไปให้ UI
            return JsonResponse({
                "success": True,
                "message": "สถานที่ถูกเพิ่มแล้ว",
                "location": {
                    "id": location.id,
                    "name": location.name
                }
            })
        except Exception as e:
            print("❌ Error:", str(e))
            return JsonResponse({"success": False, "error": str(e)})




from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ParkingLocation
from .forms import AdminLocationForm

@login_required
@csrf_exempt
def admin_edit_location(request, location_id):
    """ให้ Admin แก้ไขสถานที่"""
    location = get_object_or_404(ParkingLocation, id=location_id)

    if request.method == "POST":
        # print("📥 ข้อมูลที่รับมา:", request.POST)  # ✅ Debug ดูค่าที่ถูกส่ง
        # print("📷 ไฟล์ที่แนบมา:", request.FILES)

        form = AdminLocationForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            form.save()
            print("✅ แก้ไขสำเร็จ:", form.cleaned_data)  # ✅ Debug ค่าหลังแก้ไข
            return JsonResponse(
                {"success": True, "message": "สถานที่ถูกแก้ไขแล้ว"},
                json_dumps_params={'ensure_ascii': False}
            )
        else:
            print("❌ ฟอร์มไม่ผ่าน:", form.errors)  # ✅ Debug ข้อผิดพลาด
            return JsonResponse(
                {"success": False, "error": form.errors},
                json_dumps_params={'ensure_ascii': False}
            )


    else:
        form = AdminLocationForm(instance=location)

    return render(request, 'admin_edit_location.html', {'form': form, 'location': location})


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import ParkingLocation

@csrf_exempt
def delete_location(request, location_id):
    """ฟังก์ชันลบสถานที่จอดรถ"""
    if request.method == "DELETE":
        try:
            location = get_object_or_404(ParkingLocation, id=location_id)
            location.delete()
            return JsonResponse({"success": True, "message": "สถานที่ถูกลบแล้ว"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    else:
        return JsonResponse({"success": False, "error": "Invalid request method"})


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ROI

@csrf_exempt
def update_roi_position(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            roi = ROI.objects.get(id=data["roi_id"])
            roi.x_position = float(data["x_position"])
            roi.y_position = float(data["y_position"])
            roi.save()
            return JsonResponse({"success": True, "roi_id": roi.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})


import os
import cv2
from django.conf import settings
from django.http import JsonResponse
from easypark.models import ParkingLocation

def capture_frame(request, location_id):
    """แคปภาพจากกล้องของสถานที่ และบันทึกเป็นไฟล์"""
    try:
        location = ParkingLocation.objects.get(id=location_id)
        camera_url = location.camera_url
        
        cap = cv2.VideoCapture(camera_url)
        success, frame = cap.read()
        cap.release()
        
        if not success:
            return JsonResponse({'success': False, 'error': 'ไม่สามารถจับภาพจากกล้องได้'}, status=500)

        # ✅ ดึงขนาดภาพ
        height, width, _ = frame.shape  # เพิ่มตรงนี้เพื่อหาขนาดรูป

        # ✅ สร้างโฟลเดอร์ `media/roi_snapshots/` ถ้ายังไม่มี
        roi_dir = os.path.join(settings.MEDIA_ROOT, 'roi_snapshots')
        if not os.path.exists(roi_dir):
            os.makedirs(roi_dir)

        # ✅ กำหนด path ของไฟล์ภาพ
        image_path = f'roi_snapshots/location_{location_id}.jpg'
        full_path = os.path.join(settings.MEDIA_ROOT, image_path)

        # ✅ บันทึกภาพ
        save_success = cv2.imwrite(full_path, frame)

        if not save_success:
            return JsonResponse({'success': False, 'error': 'บันทึกไฟล์ภาพไม่สำเร็จ'}, status=500)

        # ✅ เพิ่มการคืนค่าขนาดภาพ
        return JsonResponse({
            'success': True,
            'image_url': settings.MEDIA_URL + image_path,
            'image_width': width,
            'image_height': height
        })

    except ParkingLocation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'ไม่พบสถานที่'}, status=404)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




from PIL import Image

def roi_modal_view(request):
    image_path = "roi_snapshots/location_{location_id}"
    with Image.open(image_path) as img:
        image_width, image_height = img.size

    context = {
        "rois": ROI.objects.all(),
        "image_width": image_width,
        "image_height": image_height
    }
    return render(request, 'easypark/manager_dashboard.html', context)



from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import ParkingLocation

def update_parking_image(request, location_id):
    if request.method == 'POST' and request.FILES.get('image'):
        location = get_object_or_404(ParkingLocation, id=location_id)
        location.image = request.FILES['image']
        location.save()
        return JsonResponse({'message': 'รูปภาพอัปเดตสำเร็จ!'})
    return JsonResponse({'error': 'คำขอไม่ถูกต้อง'}, status=400)














