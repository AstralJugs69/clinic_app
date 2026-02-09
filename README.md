# ClinicFlow Lite

A mini clinic front-desk module for **patient registration**, **appointment scheduling**, **today's schedule view**, and **action logging**.

## Features

- **Authentication**: Login/logout with Django sessions
- **Patient Registry**: Create, list, search, and view patient details
- **Appointments**: Create appointments with datetime, duration, reason, and status
- **Today's Schedule**: Shows today-only appointments, then applies optional patient-name search
- **Realtime Workflow**: Front desk check-in -> doctor accepts -> transfer to room -> room accepts -> complete/transfer
- **Live Boards**: Front desk, doctor feed, and room feeds update in real time over WebSockets
- **Front Desk Intake**: Register walk-ins, flag emergencies, and jump to new patient registration from one screen
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
DB_TARGET=local

# Local mode options:
# 1) Leave LOCAL_DATABASE_URL empty to use local SQLite (db.sqlite3)
# 2) Set LOCAL_DATABASE_URL for local PostgreSQL
LOCAL_DATABASE_URL=

# Hosted DB URL (Supabase/Neon/etc)
SUPABASE_DATABASE_URL=postgresql://user:password@host:5432/dbname

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_INCLUDE_SUBDOMAINS=True

# Backward compatibility fallback:
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

Database target switching is env-only:

- `DB_TARGET=local` -> uses `LOCAL_DATABASE_URL`, or `db.sqlite3` if empty
- `DB_TARGET=supabase` -> uses `SUPABASE_DATABASE_URL`
- `DB_TARGET=auto` -> uses `DATABASE_URL` first (legacy mode)

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

## Deploy Checklist (Realtime Safe)

1. Use ASGI startup command (already in `Procfile`):

```bash
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

2. Set these env vars in your host:
   - `DEBUG=False`
   - `SECRET_KEY=<long random key>`
   - `ALLOWED_HOSTS=<your-domain>`
   - `DATABASE_URL=<supabase postgres url>`
   - `REDIS_URL=<managed redis url>`

3. Ensure Redis and web app are in the same network/region.

4. Run deploy check:

```bash
python manage.py check --deploy
```

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

1. Login as `demo_staff` and open `/appointments/live/frontdesk/`.
2. Use **Register Walk-In Check-In** for:
   - normal walk-in check-ins
   - emergency check-ins (toggle emergency)
   - quick links to create a new patient or scheduled appointment
3. Login as `demo_doctor` in a second browser session and open `/appointments/live/doctor/`, accept the patient, then send to `Consultation-2` or another room.
4. Login as `demo_nurse` in another session and open `/appointments/live/room/CONS2/` (or room code used), accept and complete or transfer.
5. All active boards update automatically without page refresh.

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
