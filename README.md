# 🎬 Anime Netflix - Steins;Gate Fan Platform

A themed web application dedicated to **Steins;Gate**, where users can watch both seasons, create accounts, customize their profile, and interact through comments.

This project was developed as a **final course project** to demonstrate full-stack development skills using Django.

---

## 🚀 About The Project

**Anime Netflix** is a niche streaming-style website focused on a single title - *Steins;Gate*.

Unlike a real streaming service, this platform was built to showcase:

* Backend architecture with Django
* Authentication system with email confirmation
* Media handling (avatars, files)
* Dynamic UI with season switching
* User interaction via comments

The video player is implemented on the frontend side and works as an embedded media interface.

---

## ✨ Features

✅ Watch **Steins;Gate** (2 seasons)
✅ Switch between seasons and episodes
✅ User registration & login system
✅ Email confirmation during signup
✅ Profile customization:
  * Change nickname (display name)
  * Upload avatar
✅ Minimal form and data validation
✅ Comment system for registered users
✅ Pagination for comments
✅ Media file handling with Pillow
✅ PostgreSQL support for production
✅ Automated tests included
✅ Environment configuration using `.env`
✅ Fully functional Django backend

---

## 🛠️ Tech Stack

**Backend**

* Django 6
* Django Authentication System
* SQLite / PostgreSQL
* ASGI support

**Frontend**

* HTML5
* CSS3
* JavaScript (vanilla)

**Libraries**

* Pillow - image processing (avatars)
* python-dotenv / dotenv - environment variables

---

## 📦 Dependencies

```
asgiref==3.11.1
Django==6.0.2
dotenv==0.9.9
pillow==12.1.0
python-dotenv==1.2.1
sqlparse==0.5.5
tzdata==2025.3
bleach
psycopg2-binary
```

---

## ⚙️ Installation & Run Locally

Clone the repository:

```
git clone https://github.com/oniqq1/anime_netflix.git
cd anime_netflix
```

Create virtual environment:

```
python -m venv venv
```

Activate it:

**Windows**

```
venv\Scripts\activate
```

**Mac/Linux**

```
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Go to the core directory:

```
cd core
```

Create logs:

```
mkdir logs
```

Make migrations:

```
python manage.py makemigrations
```

Run migrations:

```
python manage.py migrate
```

Start the development server:

```
python manage.py runserver
```

Open in browser:

```
http://127.0.0.1:8000/
```

---

## 🔐 Authentication Flow

1. User registers an account
2. Confirmation email is sent
3. After confirmation, user can:

   * Log in
   * Upload avatar
   * Change nickname
   * Leave comments

---
## .env

In main directory (anime_netflix) you need create .env and
write here 

```
DB_NAME='your_db_name'
DB_USER='your_db_user'
DB_PASSWORD='your_db_password'
DB_HOST='your_db_host'
DB_PORT='your_db_port'

EMAIL_HOST_USER='your_email'
EMAIL_HOST_PASSWORD='your_app_password'
```

After that project is ready to run

---

## 🎯 Purpose of the Project

This project was created to demonstrate:

* Full-stack development workflow
* Working with Django authentication
* Handling user-generated content
* File uploads & media storage
* Backend + frontend integration
* Real-world application structure

It is intended as a **portfolio project**, not a production streaming service.

---

## 📌 Notes
* The project is deployed and hosted online.
* Designed for learning and demonstration purposes.
* Focused on a single anime to emphasize functionality over scale.

---

## 🧠 What This Project Demonstrates

✔ Understanding of Django architecture<br>
✔ Ability to build authentication flows<br>
✔ Handling of media uploads<br>
✔ Creating interactive UI with backend logic<br>
✔ Managing database connections (PostgreSQL/SQLite)<br>
✔ Testing backend functionality<br>
✔ Managing environment configuration<br>
✔ Structuring and deploying a real web application<br>

---

## 👨‍💻 Author

[mailor](https://github.com/mailorq) - frontend, backend <br><br>
[oinqq](https://github.com/oniqq1) - backend 

---

⭐ If you found this project interesting - feel free to explore and improve it!
