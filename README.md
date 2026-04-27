<div align="center">
  <h1>🚀 LearnFlow LMS</h1>
  <p><strong>A Modern, Full-Stack Learning Management System</strong></p>

  <!-- Badges -->
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
</div>

<br />

## 📖 Overview

**LearnFlow** is a comprehensive, full-stack monorepo Learning Management System (LMS) designed to streamline the learning experience. It combines a robust **FastAPI (Python)** backend with a dynamic **React + Vite + Tailwind CSS** frontend dashboard, backed by a **MongoDB** database.

The platform offers a beautiful user interface with four main screens: **Dashboard, Study Planner, Analytics, and My Courses**, empowering users to track their progress, plan their tasks, and manage their courses effectively.

---

## ✨ Key Features

- **🔒 Secure Authentication:** JWT-based token authentication and secure password hashing (bcrypt).
- **📊 Interactive Dashboard:** Get a bird's-eye view of KPIs, course progress, today's plan, deadlines, and weekly hours.
- **📅 Smart Study Planner:** Day, week, and month calendar views with timeline blocks and AI-assisted planning.
- **📈 Advanced Analytics:** Track performance with 6-month charts, subject breakdowns, and detailed performance tables.
- **📚 Course Management:** Manage courses with status tracking (in-progress, completed, saved) and seamlessly enroll in new subjects.
- **🎥 YouTube Integration:** Watch enrolled course content directly within the platform.
- **🔍 Fast Search:** Debounced searching across courses and materials.
- **💅 Premium UI/UX:** Built with Tailwind CSS, Recharts, and Lucide Icons for a stunning, responsive, and modern look.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** MongoDB
- **Driver:** Motor (Async MongoDB)
- **Validation:** Pydantic
- **Auth:** Python-JOSE (JWT), Passlib (Bcrypt)

### Frontend
- **Framework:** React (Vite)
- **Routing:** React Router
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts

---

## 🚀 Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/)
- [MongoDB](https://www.mongodb.com/try/download/community) (running locally at `mongodb://localhost:27017` or a cloud URI)

### 1. Backend Setup

Open a terminal and navigate to the root directory, then move to the backend folder:

```bash
cd backend
```

**Create and activate a virtual environment:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Environment Variables:**
Copy `.env.example` to `.env` and set your configurations. For local development, defaults are usually fine, but ensure `JWT_SECRET_KEY` is set.
```bash
cp .env.example .env
```

**Seed Demo Data:**
Populate the database with demo users, courses, and tasks (Creates user: `alex@learnflow.demo` / Password: `learnflow123`):
```bash
python scripts/seed_learnflow.py
```

**Run the API:**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
*API Documentation available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### 2. Frontend Setup

Open a new terminal window and navigate to the frontend folder:

```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Run the development server:**
```bash
npm run dev
```
*The app will be running at [http://localhost:5173](http://localhost:5173). The Vite dev server is configured to proxy `/api` requests to the FastAPI backend.*

---

## 📂 Project Structure

```text
LearnFlow/
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── core/          # Config, Security, JWT dependencies
│   │   ├── db/            # MongoDB connection
│   │   ├── models/        # Data models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI application entry point
│   ├── scripts/           # DB seeding scripts
│   └── requirements.txt
└── frontend/              # React Frontend
    ├── src/
    │   ├── api/           # API client wrapper (handles JWT)
    │   ├── components/    # Reusable UI components
    │   ├── context/       # React Context (Auth)
    │   ├── pages/         # Dashboard, Planner, Courses, etc.
    │   ├── App.jsx        # Routing configuration
    │   └── main.jsx       # React entry point
    ├── vite.config.js     # Vite configuration (API proxy)
    └── package.json
```

---

## 🔌 Core API Endpoints

- **Auth**
  - `POST /api/auth/login` - Authenticate user and get JWT
  - `POST /api/auth/signup` - Register a new user
- **LearnFlow Dashboards**
  - `GET /api/learnflow/dashboard` - Get KPIs, current progress, and daily plan
  - `GET /api/learnflow/planner` - Get calendar and timeline data (day/week/month)
  - `GET /api/learnflow/analytics` - Get performance metrics and subject breakdowns
  - `GET /api/learnflow/courses` - Get user courses filtered by status

---

## 📸 Screenshots

*(Add screenshots of your application here)*

| Dashboard | Study Planner |
| :---: | :---: |
| <img src="https://via.placeholder.com/600x350.png?text=Dashboard+Screenshot" alt="Dashboard" /> | <img src="https://via.placeholder.com/600x350.png?text=Planner+Screenshot" alt="Planner" /> |

| Analytics | My Courses |
| :---: | :---: |
| <img src="https://via.placeholder.com/600x350.png?text=Analytics+Screenshot" alt="Analytics" /> | <img src="https://via.placeholder.com/600x350.png?text=Courses+Screenshot" alt="Courses" /> |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---
