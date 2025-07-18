# Smart Commercial Hub Solution
A full-stack Django-based web platform to manage for Mall administration like shops, tenants, rent payments, complaints, manager, report and admin operations.
## Overview
Smart Commercial Hub Solution is a web application designed for managing rental shops, tenants and managers in a commercial building. It streamlines tasks like shop allocation, rent collection, complaint tracking, and admin announcements — all with role-based access for admins, managers, and tenants.
## 🚀 Features
- ✅ Tenant, Manager and Shop Management
- ✅ Rent Payment Integration (Razorpay)
- ✅ Complaint & Announcement Module
- ✅ Role-Based Access: Admin, Tenant, Manager
- ✅ Django Admin with Enhanced UI
- ✅ Email Notifications for Shop Allocation and Resolved complaint
- ✅ Responsive Design for Mobile and Desktop
- ✅ Real-time Report with Data Visualization
## 🛠️ Built With
- **Backend:** Django, Python
- **Frontend:** HTML5, CSS3, Bootstrap, Java script
- **Database:** SQLite
- **Payment Gateway:** Razorpay (test mode & live)
- **Admin UI:** Django Admin + Enhanced UI

## 📄 License
This project is licensed under the MIT License.

## Author
**VISHNU**  
Email: vishnuofficial1137@gmail.com

## ⚙️ How to Run Locally

```bash
# Clone the repo
git clone https://github.com/vishnu1137/smart-commercial-hub.git
cd smart-commercial-hub

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate (Windows)

# Install requirements
pip install -r requirements.txt

# Apply migrations and create superuser
python manage.py makemigrations
python manage.py migrate

# Create Superuser
python manage.py createsuperuser

# Run the server
python manage.py runserver
