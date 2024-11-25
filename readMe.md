# 🛍️ Modern E-commerce Platform

A full-featured e-commerce platform built with Django and modern web technologies.

## ✨ Features

- 🛒 Shopping cart functionality with real-time updates
- 🔐 User authentication and authorization
- 💳 Secure checkout process
- 🎨 Responsive design with Bootstrap 4
- 🔍 Product filtering and search
- 💰 Price filtering system
- 🎯 Product categorization
- 📱 Mobile-friendly interface

## 🚀 Technologies Used

- **Backend:** Django
- **Frontend:** 
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap 4
- **Database:** Django ORM
- **Security:** Django CSRF Protection

## 🛠️ Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ecommerce-platform.git
cd ecommerce-platform
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Run the development server
```bash
python manage.py runserver
```

6. Access the application at `http://localhost:8000`

## Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update the `.env` file with your PayPal credentials:
```
PAYPAL_CLIENT_ID=your_actual_client_id
PAYPAL_SECRET_KEY=your_actual_secret_key
DEBUG=True
```

3. Never commit the `.env` file to version control
