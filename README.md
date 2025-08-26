# 🌍 Borderless Backend — "Unbordered Core"

## 🛠 Tech Stack
- **Django 4.x** — Web framework
- **Django REST Framework (DRF)** — API layer
- **drf-spectacular** — API schema & docs
- **PostgreSQL (Supabase-hosted)** — Database
- **django-cors-headers** — CORS handling
- **Railway** — Deployment platform
- **pytest / Django test runner** — Testing

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/vik2ry/borderless.git
cd borderless
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables  
Create a `.env` file in the project root with the following:
```ini
DEBUG=True
SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost,unbordered-production.up.railway.app

DB_NAME=postgres
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=6543

CSRF_TRUSTED_ORIGINS=https://unbordered-production.up.railway.app,https://localhost:3000
CORS_ALLOWED_ORIGINS=https://unbordered-production.up.railway.app,https://localhost:3000

or follow the .env.example file
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Start development server
```bash
python manage.py runserver
```

---

## 🔑 Admin Credentials
By default, no superuser exists. To create one:
```bash
python manage.py createsuperuser
```
Use the credentials you provide during creation.

---

## 🚀 Walkthrough of Features
- **User Accounts & Authentication** — Signup, login, password reset
- **CSRF & CORS Security** — Locked down origins for frontend
- **Admin API Token** — Secured endpoints for admin-only usage
- **Exchange Rate Integration** — Support for fixed overrides & live FX
- **Booking / Workspace Management (Planned)** — Manage spaces and transactions
- **RESTful API** — All endpoints available at `/api/`
- **Interactive API Docs** — Swagger/OpenAPI via `/api/schema/` and `/api/docs/`

---

## ✨ Prototype Codename
**"Unbordered Core"** — powering seamless global transactions.
