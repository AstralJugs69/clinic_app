# ClinicFlow Lite

A mini clinic front-desk module for **patient registration**, **appointment scheduling**, **today's schedule view**, and **action logging**.

## Features

- **Authentication**: Login/logout with Django sessions
- **Patient Registry**: Create, list, search, and view patient details
- **Appointments**: Create appointments with datetime, duration, reason, and status
- **Today's Schedule**: Shows today-only appointments, then applies optional patient-name search
- **Activity Logging**: Logs login/logout, patient creation, and appointment creation
- **Read-only API (session auth)**: Patients, patient detail, today's appointments, logs

## Quick Start

### 1. Clone and Setup Environment

```bash
cd clinic_app
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file with:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Preferred for deployment:
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Fallback if DATABASE_URL is not set:
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASS=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 5. Seed Demo Data (recommended)

```bash
python manage.py seed_demo
```

Demo credentials created by the command:

- Username: `demo_staff`
- Password: `DemoPass123!`

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://localhost:8000

## Pages

| URL | Description |
|-----|-------------|
| `/login/` | User login |
| `/patients/` | Patient list with search |
| `/patients/new/` | Create new patient |
| `/patients/<id>/` | Patient detail |
| `/appointments/` | Today's schedule |
| `/appointments/new/` | Create new appointment |
| `/activity/` | Activity log |
| `/admin/` | Django Admin |

## API Endpoints (login required)

| URL | Description |
|-----|-------------|
| `/api/patients/` | List patients |
| `/api/patients/<id>/` | Patient detail |
| `/api/appointments/today/` | Today's appointments |
| `/api/logs/` | Recent action logs |

## Tech Stack

- **Backend**: Django 6.0
- **Database**: PostgreSQL (Supabase)
- **Styling**: Tailwind CSS (CDN)
- **Auth**: Django Sessions

## Project Structure

```
clinic_app/
├── apps/
│   ├── accounts/     # ActionLog, UserProfile, Activity view
│   ├── appointments/ # Appointment model, Today's schedule
│   └── patients/     # Patient model, CRUD views
├── config/           # Django settings, URLs
└── templates/        # HTML templates with Tailwind
```
