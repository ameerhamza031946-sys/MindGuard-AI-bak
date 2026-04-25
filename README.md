# 🧠 MindGuard AI — Full Stack

FastAPI + MongoDB backend with secure auth, connected to the MindGuard frontend.

---

## 📁 Project Structure

```
mindguard-backend/
├── mindguard.html              ← Frontend (open in browser)
├── requirements.txt
├── .env.example                ← Copy to .env and fill values
└── app/
    ├── main.py                 ← FastAPI app entry point
    ├── core/
    │   ├── config.py           ← Settings from .env
    │   ├── security.py         ← JWT + bcrypt
    │   ├── database.py         ← Motor (async MongoDB)
    │   └── deps.py             ← Auth guard (get_current_user)
    ├── middleware/
    │   └── security.py         ← Security headers + size limit
    ├── routers/
    │   ├── auth.py             ← Register, Login, Logout, Refresh, Reset
    │   ├── checkin.py          ← Stress check-ins, trends, stats
    │   └── chat.py             ← Chat messages & history
    └── schemas/
        ├── auth.py             ← Pydantic validation
        └── checkin.py          ← Checkin & chat schemas
```

---

## 🚀 Setup (Step by Step)

### 1. Install MongoDB
```bash
# Ubuntu/Debian
sudo apt install mongodb
sudo systemctl start mongodb

# macOS
brew install mongodb-community
brew services start mongodb-community

# Windows: Download installer from mongodb.com
```

### 2. Clone & install Python dependencies
```bash
cd mindguard-backend
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```

Open `.env` and set:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=mindguard_db

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your_random_secret_here
JWT_REFRESH_SECRET_KEY=another_random_secret_here

DEBUG=True   # set False in production
ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:3000
```

### 4. Run the backend
```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be live at: **http://localhost:8000**
API docs (debug mode): **http://localhost:8000/docs**

### 5. Open the frontend
Open `mindguard.html` in your browser using **Live Server** (VS Code extension)
or:
```bash
python -m http.server 5500
# then visit http://localhost:5500/mindguard.html
```

> ⚠️ Make sure `ALLOWED_ORIGINS` in `.env` includes your frontend URL.

---

## 🔐 Security Features

| Feature | Detail |
|---|---|
| **Password Hashing** | bcrypt with cost factor 12 |
| **JWT Tokens** | Short-lived access (30min) + refresh (7 days) |
| **Token Blacklisting** | Logout invalidates tokens server-side via MongoDB TTL |
| **Brute Force Protection** | Lockout after 5 failed logins (15 min) |
| **Input Validation** | Pydantic v2 — strict types, length limits |
| **XSS Prevention** | bleach sanitization + Content-Security-Policy header |
| **Clickjacking** | X-Frame-Options: DENY |
| **MIME Sniffing** | X-Content-Type-Options: nosniff |
| **CORS** | Whitelist only — no wildcard `*` |
| **Rate Limiting** | 200 requests/minute per IP (slowapi) |
| **Request Size** | Max 1 MB body |
| **Error Leakage** | Stack traces hidden in production |
| **Email Enumeration** | Forgot password always returns 200 |

---

## 🌐 API Endpoints

### Auth
```
POST /api/auth/register         Register new account
POST /api/auth/login            Login, get tokens
POST /api/auth/logout           Logout (blacklist token)
POST /api/auth/refresh          Get new access token
GET  /api/auth/me               Get current user
POST /api/auth/forgot-password  Send reset email
POST /api/auth/reset-password   Reset with token
```

### Check-ins
```
POST /api/checkins              Log stress level (0-100)
GET  /api/checkins              Get history (paginated)
GET  /api/checkins/trends       Weekly chart data
GET  /api/checkins/stats        Avg, max, min, streak
```

### Chat
```
POST /api/chat                  Send message, get AI reply
GET  /api/chat/history          Get message history
DELETE /api/chat                Clear all messages
```

### Auth Header (required for protected routes)
```
Authorization: Bearer <access_token>
```

---

## 🔑 Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 digit (0-9)
- Maximum 128 characters

---

## 🏭 Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong random `JWT_SECRET_KEY` (32+ chars)
- [ ] Use MongoDB Atlas or secured MongoDB with auth
- [ ] Enable HTTPS (add HSTS header in middleware)
- [ ] Set `ALLOWED_ORIGINS` to your actual domain only
- [ ] Integrate real email service for password reset (SendGrid/SMTP)
- [ ] Deploy with `gunicorn` + `uvicorn` workers
- [ ] Use environment secrets manager (not plain `.env`)

---

## 📦 Tech Stack
- **Backend**: FastAPI 0.111, Python 3.11+
- **Database**: MongoDB (Motor async driver)
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Validation**: Pydantic v2 + bleach
- **Rate Limiting**: slowapi
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
