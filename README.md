### Code Structure

Freelance_hub/
├── app.py                    # Original monolithic app (backup)
├── app_new.py                # New organized app with blueprints
├── project.db                # SQLite database
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── .gitignore               # Git ignore rules
│
├── src/                      # Source code package
│   ├── __init__.py
│   │
│   ├── config/              # Configuration
│   │   ├── __init__.py
│   │   └── settings.py      # App config, SERVICE_TAGS
│   │
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── user_profile.py  # Profile class
│   │   └── freelance_post.py # freelance_post class
│   │
│   ├── routes/              # Route blueprints
│   │   ├── __init__.py
│   │   ├── auth.py          # Login, register, logout
│   │   ├── buyer.py         # Buyer dashboard, search, preferences
│   │   ├── seller.py        # Seller dashboard, service CRUD
│   │   ├── services.py      # Service details, payments
│   │   ├── chat.py          # Messaging system
│   │   └── resume.py        # Resume upload
│   │
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── database.py      # Database connection
│       └── search_engine.py # SearchQuery class
│
├── static/                  # Static files
│   └── uploads/            # Uploaded resumes
│
└── templates/              # HTML templates
    ├── login.html
    ├── register.html
    ├── mainpage_buyer.html
    ├── mainpage_seller.html
    └── ...
