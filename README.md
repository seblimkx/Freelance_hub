### Code Structure

```
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
```


### Core Files

#### `app_new.py` (New Main App)
- Application factory pattern
- Registers all blueprints
- Minimal code (~50 lines vs 600+)

#### `src/config/settings.py`
- Environment configuration
- SERVICE_TAGS
- Flask config classes
- Stripe keys

#### `src/utils/database.py`
- `get_db_connection()` function
- Centralized database access
- Easy to switch databases later

#### `src/utils/search_engine.py`
- `SearchQuery` class
- Semantic search functionality
- Moved from `search_algo.py`

### Route Modules

#### `src/routes/auth.py`
Routes:
- `/` - Login page
- `/login` - Login handler
- `/register` - Registration
- `/logout` - Logout

#### `src/routes/buyer.py`
Routes:
- `/buyer` - Buyer dashboard
- `/search` - Search services
- `/set_preferences` - Set preferences

Functions:
- `recommend()` - Recommendation engine

#### `src/routes/seller.py`
Routes:
- `/seller` - Seller dashboard
- `/add_service` - Create service
- `/edit_service` - Update service
- `/delete_service` - Remove service
- `/seller/inbox` - Message inbox

#### `src/routes/services.py`
Routes:
- `/service/<id>` - Service details
- `/create-checkout-session/<id>` - Stripe checkout
- `/success` - Payment success
- `/cancel` - Payment cancelled

#### `src/routes/chat.py`
Routes:
- `/chat/<service_id>` - Start/view chat
- `/chat/convo/<id>` - View conversation
- `/send_message/<id>` - Send message

#### `src/routes/resume.py`
Routes:
- `/upload_resume` - Upload/edit resume

## 🧪 Testing the New Structure

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the new organized app
python app_new.py

# Test all features:
# ✓ Login/Register
# ✓ Buyer dashboard
# ✓ Seller dashboard
# ✓ Search functionality
# ✓ Service CRUD
# ✓ Chat system
# ✓ Resume upload
# ✓ Payments
```

## 🔍 Finding Code

**Before (Monolithic):**
- Everything in `app.py` (600+ lines)
- Hard to find specific features
- Difficult to modify without breaking things

**After (Organized):**
| Feature | Location |
|---------|----------|
| Login/Register | `src/routes/auth.py` |
| Buyer Features | `src/routes/buyer.py` |
| Seller Features | `src/routes/seller.py` |
| Chat/Messages | `src/routes/chat.py` |
| Search Engine | `src/utils/search_engine.py` |
| Database | `src/utils/database.py` |
| Config | `src/config/settings.py` |
| Models | `src/models/` |

## 🚀 Next Steps

1. **Test thoroughly** - Ensure all features work
2. **Add error handling** - Better exception management
3. **Add logging** - Track errors and usage
4. **Write tests** - Unit tests for each module
5. **API endpoints** - Add REST API for mobile app
6. **Documentation** - API docs with Swagger

## 🎓 Learning Resources

- [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/)
- [Application Factory Pattern](https://flask.palletsprojects.com/en/latest/patterns/appfactories/)
- [Python Package Structure](https://docs.python.org/3/tutorial/modules.html#packages)
