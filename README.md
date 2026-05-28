# Student Management System

A secure student management web application built with Flask. It offers student registration, profile completion, admin monitoring, student account management, and security logging.

## Features

- Student registration and login
- Student profile completion enforcement
- Admin dashboard with statistics and audit logs
- Student account management: add, edit, delete, reset password
- Secure session handling and rate limiting
- PostgreSQL database support via SQLAlchemy and `pg8000`
- HTTPS development server using `ssl_context='adhoc'`

## Project Structure

- `app/`
  - `__init__.py` — Flask application factory and extension setup
  - `forms.py` — WTForms definitions and validation rules
  - `models.py` — database models for users, student profiles, and security logs
  - `routes.py` — main, auth, and admin routes
  - `utils.py` — helper utilities and decorators
  - `static/` — CSS, JavaScript, and assets
  - `templates/` — Jinja2 templates for the web UI
- `config.py` — application configuration and environment variable loading
- `run.py` — development server entry point
- `make_admin.py` — create or reset the admin account
- `fix_db.py` — synchronize database schema and missing columns
- `update_profiles.py` — update existing student profiles with default names
- `requirements.txt` — Python dependencies

## Requirements

- Python 3.11+ (recommended)
- PostgreSQL database
- Virtual environment tool such as `venv`

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd Student_management
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root if needed and configure:

   ```env
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql+pg8000://user:password@localhost:5432/student_db
   UPLOAD_FOLDER=app/static/uploads
   MAX_CONTENT_LENGTH=5242880
   ```

## Database Setup

1. Make sure PostgreSQL is running and the target database exists.
2. Initialize or synchronize the database schema:

   ```bash
   python fix_db.py
   ```

3. Create the admin user:

   ```bash
   python make_admin.py
   ```

4. Optionally update existing student profiles:

   ```bash
   python update_profiles.py
   ```

## Running the Application

Start the Flask development server:

```bash
python run.py
```

Then open:

```text
https://127.0.0.1:5000
```

## Notes

- The app uses `flask-limiter` to protect login routes and limit requests.
- Session cookies are secured with `HttpOnly`, `Secure`, and `SameSite=Lax` settings.
- The admin interface includes student statistics and a security audit log.

## License

This project is provided as-is for educational or internal use.
