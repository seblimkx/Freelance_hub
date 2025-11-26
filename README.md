# FreelanceHub Setup Guide

## Recent Code Improvements

### Security Fixes
- ✅ Added Flask `SECRET_KEY` for secure session management
- ✅ Removed unsafe `check_same_thread=False` for SQLite
- ✅ Fixed all database connection leaks (proper close() calls)
- ✅ Created `.env.example` template for environment variables

### Bug Fixes
- ✅ Removed duplicate `recommend.py` file (conflicted with `search_algo.py`)
- ✅ Fixed duplicate password validation in registration
- ✅ Fixed all `freelance_post` constructor calls with proper parameters
- ✅ Fixed `Profile` initialization with proper keyword arguments
- ✅ Removed debug print statements
- ✅ Fixed default image path ("/static/default_image.png")

### Code Quality
- ✅ Created `requirements.txt` for dependency management
- ✅ Improved `.gitignore` to protect sensitive files
- ✅ Closed all database connections properly
- ✅ Standardized error handling

## Setup Instructions

### 1. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add:
- Generate `SECRET_KEY`: `python -c "import os; print(os.urandom(24).hex())"`
- Add your Stripe API keys from https://dashboard.stripe.com/apikeys

### 4. Run the Application
```powershell
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Project Structure
```
Freelance_hub/
├── app.py                 # Main Flask application
├── search_algo.py         # Search engine & freelance_post class
├── user_profile.py        # User profile management
├── unit_test.py          # Unit tests for search functionality
├── project.db            # SQLite database
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Template for environment variables
├── .gitignore           # Git ignore rules
├── static/              # Static files (CSS, JS, uploads)
├── templates/           # HTML templates
└── flask_session/       # Session storage
```

## Important Notes

- **Never commit `.env`** - It contains sensitive keys
- **Database**: SQLite is used (`project.db`)
- **Sessions**: Stored in `flask_session/` directory
- **Uploads**: Resumes uploaded to `static/uploads/`

## Next Steps (Recommendations)

1. Add CSRF protection using Flask-WTF
2. Add input validation and sanitization
3. Implement rate limiting for API endpoints
4. Add comprehensive error handling
5. Write more unit tests
6. Add logging for debugging
7. Consider migrating to PostgreSQL for production
