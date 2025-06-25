# Easy Parking Project

## ขั้นตอนการติดตั้ง

1. ติดตั้ง Xampp บนเครื่องของคุณ
```
https://www.apachefriends.org/download.html
```
2. Clone โปรเจคนี้:
   ```bash
   git clone -b Mockupdata https://github.com/your-repo/easy-parking.git
   cd Easy_Parking
   ```

## Download Data Mockup
```
https://drive.google.com/drive/folders/1RG8kOw1wok6VPlOCsVyzghTKZauzojdB?usp=sharing
```

## ขั้นตอนการ Mockup Data
```
เมื่อดาวโหลด data มาแล้วให้ทำการสร้าง database ที่ชื่อว่า easyparking บน phpMyaAmin จากนั้นให้ทำการ Import database ที่ดาวโหลดมาลงไปใน database 

```

## Using this commands for run project
```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
