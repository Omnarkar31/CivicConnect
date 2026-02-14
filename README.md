# CivicConnect 🏛️
**Bridging the gap between Citizens and Local Government.**

CivicConnect is a responsive web application designed to streamline ward-level management. It allows citizens to report local issues (like potholes, water leakage, or garbage) with file attachments and enables Ward Admins to manage infrastructure projects and broadcast urgent announcements.

---

## 🚀 Key Features

### 👤 For Citizens
* **Report Problems:** Submit grievances with photo, video, or PDF proof.
* **Track Progress:** View the real-time status of reported issues.
* **Ward Awareness:** Stay updated with local construction projects and government announcements.

### 🔑 For Ward Admins
* **Grievance Management:** View all issues reported within the specific ward.
* **Project Tracking:** Add and update local ward projects (budget, deadline, progress).
* **Emergency Alerts:** Broadcast urgent notices to all citizens in the ward.

---

## 🛠️ Tech Stack
* **Backend:** Python (Flask)
* **Database:** MySQL (SQLAlchemy ORM)
* **Frontend:** HTML5, CSS3, Bootstrap 5 (Mobile-Responsive)
* **Authentication:** Flask-Login
* **Security:** Password Hashing (Werkzeug)

---

## 📂 File Structure
```text
CivicConnect/
├── app.py               # Main Flask Application
├── requirements.txt     # Dependencies
├── static/
│   ├── css/style.css    # Custom Styling
│   └── uploads/         # User-uploaded proof (images/videos)
├── templates/           # HTML Templates (Bootstrap-based)
└── README.md
