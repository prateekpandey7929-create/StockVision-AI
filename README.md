# StockVision AI

> AI-Powered Smart Stock Forecasting Platform

StockVision AI is a complete, production-ready web application designed with a premium fintech SaaS interface. It fetches real-time historical equity data using `yfinance`, fits on-demand Machine Learning models (Random Forest Regressor vs Linear Regression), evaluates predictions with standard validation metrics (R², MAE, RMSE), and allows users to manage a customized watchlist and review forecast history logs.

---

## Key Features

- **Authentication System:** Secure registration and logins, hashed credentials, and session management.
- **Landing Page:** Interactive SaaS interface detailing features, mechanical explanations, support logs, FAQs, and a contact form.
- **Predictive Workspace Dashboard:** Tracks market index movements (S&P 500, Nasdaq, Dow Jones, Nifty 50), recent predictions, watchlists, and trending stock access.
- **On-Demand ML Trainer:** Downloads 2 years of daily records and trains a Random Forest model on the fly for any valid searched ticker symbol.
- **Historical Analysis Module:** Toggles historical charts (1M, 3M, 6M, 1Y, 5Y) plotted dynamically using Chart.js.
- **Model Performance Audits:** Compares Random Forest against Linear Regression baselines, exposing Mean Absolute Error, Root Mean Squared Error, and R² scores.
- **Watchlist & History logs:** Saves custom tickers for quick lookup; paginates and filters previous prediction logs.
- **Admin Dashboard Panel:** System status panel where admins can moderate users, view global logs, and read or delete customer support messages.

---

## Technical Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy ORM, SQLite Database
- **Machine Learning:** Scikit-Learn, Pandas, NumPy, Joblib, yfinance API
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5 UI Framework, Chart.js Charts, FontAwesome Icons

---

## Project Directory Map

```text
StockVisionAI/
│
├── app.py                  # Main entrance. Initializes Flask app and seeds DB
├── requirements.txt        # Library dependencies list
├── config.py               # Path configurations & Flask environmental variables
│
├── database/
│   └── models.py           # SQLAlchemy Schemas: User, Prediction, Watchlist, ContactMessage
│
├── ml/
│   ├── train_model.py      # ML data download, feature engineering, and model trainer
│   └── predictor.py        # Forecasting logic and scheduler for stale models
│
├── routes/
│   ├── auth.py             # Login, register, logout, and profile management routes
│   ├── main.py             # Dashboards, watchlists, searches, and prediction routing
│   └── admin.py            # Administrative audit gates and message moderators
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom dark SaaS theme style configurations
│   └── js/
│       └── main.js         # Client AJAX requests, accordions, and Chart.js setup
│
├── templates/
│   ├── base.html           # Layout page with Navbar, Footer, and Toast flash alerts
│   ├── landing.html        # Public hero landing page, How It Works, and FAQs
│   ├── login.html          # Authentication sign-in form
│   ├── register.html       # Authentication registration form
│   ├── dashboard.html      # Workspace panel for indices, watchlists, and history
│   ├── stock_detail.html   # Main analysis dashboard (Chart.js charts, predictions, and model performance metrics)
│   ├── watchlist.html      # Ticker watchlist manager
│   ├── history.html        # Prediction logging tables with search and filters
│   ├── profile.html        # Name, email, and password manager
│   ├── contact.html        # Feedback mail box page
│   └── admin.html          # Administrative metrics review panel
│
└── models/                 # Dir where trained joblib model packages are saved
```

---

## Installation & Setup

### Ubuntu (WSL) Commands

To run this application inside a WSL (Ubuntu) environment, follow these terminal instructions:

```bash
# 1. Update package registry and install requirements
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# 2. Clone/Navigate into the project root directory
cd "StockVision AI"

# 3. Create a python virtual environment
python3 -m venv venv

# 4. Activate the virtual environment
source venv/bin/activate

# 5. Install all python library dependencies
pip install -r requirements.txt

# 6. Start the Flask application
python3 app.py
```

Open `http://127.0.0.1:5000` inside your browser to access the system.

---

## Default Administrative Credentials

A system administrator account is seeded during database initialization. Use these credentials to view the Admin Panel dashboard:

- **Email:** `admin@stockvision.ai`
- **Password:** `Admin@123`
