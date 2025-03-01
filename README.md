# Course Management System Backend

The Course Management System is a platform for managing courses, students, and instructors. This repository contains the backend code for the platform, built with **Flask**, **SQLAlchemy**, and **SQLite** as the database.

---

## Tech Stack

- **Backend**: Flask
- **Database**: SQLite (or PostgreSQL for production)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-JWT-Extended for secure token-based authentication
- **Deployment**: Docker and AWS EC2 Instance

---

## Getting Started

### Prerequisites

- **Python**: Install from [python.org](https://www.python.org/).
- **SQLite**: SQLite comes pre-installed with Python. Optionally, for production, install [PostgreSQL](https://www.postgresql.org/).
- **Pip**: Package manager for Python, typically installed with Python.

---

### Installation

1. **Install Dependencies**:
- python3 -m venv venv
- source venv/bin/activate   # On Windows use `venv\Scripts\activate`
- pip install -r requirements.txt

### Run Application
- run **python app.py**
