# ClinicFlow Lite

A mini clinic front-desk module for **patient registration**, **appointment scheduling**, **today's schedule view**, and **action logging**.

## Features

- **Authentication**: Login/logout with Django sessions
- **Patient Registry**: Create, list, search, and view patient details
- **Appointments**: Create appointments with datetime, duration, reason, and status
- **Today's Schedule**: Shows today-only appointments, then applies optional patient-name search
- **Realtime Workflow**: Front desk check-in -> doctor accepts -> transfer to room -> room accepts -> complete/transfer
- **Live Boards**: Front desk, doctor feed, and room feeds update in real time over WebSockets
- **Activity Logging**: Logs login/logout, patient/appointment creation, and workflow transitions
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
REDIS_URL=redis://127.0.0.1:6379/0

# Preferred for deployment:
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Fallback if DATABASE_URL is not set:
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASS=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432
```

`REDIS_URL` is strongly recommended for realtime in multi-worker deployments.
If omitted, the app falls back to in-memory channels (works only in single-process dev).

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

- `demo_staff` (receptionist)
- `demo_doctor` (doctor)
- `demo_nurse` (nurse)
- Password for all: `DemoPass123!`

### 6. Run Development Server

Start Redis locally if you use realtime boards in separate sessions:

```bash
redis-server
```

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
| `/appointments/live/frontdesk/` | Front desk realtime board |
| `/appointments/live/doctor/` | Doctor realtime feed |
| `/appointments/live/room/<code>/` | Room realtime feed |
| `/activity/` | Activity log |
| `/admin/` | Django Admin |

## API Endpoints (login required)

| URL | Description |
|-----|-------------|
| `/api/patients/` | List patients |
| `/api/patients/<id>/` | Patient detail |
| `/api/appointments/today/` | Today's appointments |
| `/api/logs/` | Recent action logs |

## Realtime Flow Demo

1. Login as `demo_staff` and open `/appointments/live/frontdesk/`, then check in a patient.
2. Login as `demo_doctor` in a second browser session and open `/appointments/live/doctor/`, accept the patient, then send to `Consultation-2` or another room.
3. Login as `demo_nurse` in another session and open `/appointments/live/room/CONS2/` (or room code used), accept and complete or transfer.
4. All active boards update automatically without page refresh.

## Tech Stack

- **Backend**: Django 6.0
- **Database**: PostgreSQL (Supabase)
- **Styling**: Tailwind CSS (CDN)
- **Auth**: Django Sessions
- **Realtime**: Django Channels + Redis

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
