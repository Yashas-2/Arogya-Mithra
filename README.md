# 🏥 Swasthya Sakhi

**Intelligent Healthcare Assistance for Karnataka Government Hospitals.**

Swasthya Sakhi is a smart healthcare platform designed to empower patients by bridging the gap between medical services and patient understanding. Powered by **Gemini AI**, it helps users identify government scheme eligibility, securely store hospital reports, and understand complex medical terms in simple language.

---

## ✨ Key Features

- 🧠 **Gemini Scheme Predictor**: Predicts eligibility for Central & Karnataka Government schemes.
- 📂 **Digital Health Locker**: End-to-end encrypted storage for medical reports.
- 💊 **AI Medical Interpreter**: Converts medical jargon into simple Kannada or English.
- 🔐 **Secure access**: OTP-protected report viewing with full audit logs.
- 👨‍⚕️ **Doctor Portal**: Dedicated dashboard for doctors to manage profiles and view stats.
- 🏥 **Hospital Staff Portal**: Secure upload interface for authorized laboratory/hospital staff.

---

## 🏗️ Project Structure

This is a **Monorepo** containing both the backend and frontend:

- `/` (Root): Django Backend & Project Configuration.
- `/core`: Main Django App logic (Models, Views, APIs).
- `/arogyamitra-react`: React Frontend (Vite + Tailwind/CSS).

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Backend Setup (Django)
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment variables
# Copy .env.example to .env and add your GEMINI_API_KEY
copy .env.example .env

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```
*Backend runs on: `http://127.0.0.1:8000`*

### 3. Frontend Setup (React)
```bash
cd arogyamitra-react

# Install dependencies
npm install

# Start the development server
npm run dev
```
*Frontend runs on: `http://localhost:5173`*

---

## ⚙️ Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key for security. |
| `DEBUG` | Set to `True` for development, `False` for production. |
| `GEMINI_API_KEY` | Your Google Gemini AI API Key (Required). |
| `TWILIO_ACCOUNT_SID` | Twilio SID for OTP SMS (Optional - has Dev fallback). |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token (Optional). |
| `TWILIO_PHONE_NUMBER`| Your Twilio virtual number (Optional). |

---

## 🛠️ Tech Stack

- **Backend**: Django 5.2, Django REST Framework, SimpleJWT.
- **Frontend**: React 18, Vite, Vanilla CSS (Glassmorphism), FontAwesome.
- **AI Engine**: Google Gemini Pro.
- **Database**: SQLite (Development) / PostgreSQL (Production ready).
- **Security**: Fernet (AES-128) Encryption, OTP verification.

---

## 💡 Troubleshooting

- **API Connectivity**: If the frontend cannot connect to the backend, ensure `apiService.js` is pointing to `http://127.0.0.1:8000`. We use the IP `127.0.0.1` instead of `localhost` to avoid IPv6 resolution issues on Windows.
- **Missing Images**: Ensure the Django server is running, as it serves the media files from the `/media/` directory.

---

Made with 💚 for Karnataka Healthcare.
