# WATS Auto-Triage Flask Application

A Flask-based web application for automated test failure triage and JIRA ticket management for the WATS (Web Automation Test System).

## 🚀 Features

- **Automated Triage**: Automatically match and categorize test failures
- **JIRA Integration**: Create and update JIRA tickets automatically
- **Image Comparison**: Visual validation using screenshot comparison
- **Multi-Feature Support**: Support for Driver, Rider, Freight, U4B, London GRAT, Tooling, and Customer Obsession
- **RESTful API**: Complete API for integration with other systems
- **Web Interface**: Modern, responsive UI for manual operations
- **Background Processing**: Long-running tasks execute asynchronously
- **Task Monitoring**: Track status of all running tasks

## 📁 Project Structure

```
flask_app/
├── app.py                              # Main Flask application with API routes
├── requirements.txt                    # Python dependencies
├── README.md                          # This file
├── .gitignore                         # Git ignore rules
│
├── templates/                         # HTML templates
│   └── index.html                     # Web UI dashboard
│
├── static/                            # Static files
│   ├── css/
│   │   └── style.css                  # Application styles
│   └── js/
│       └── main.js                    # Frontend JavaScript
│
├── utility/                           # Utility modules
│   ├── __init__.py
│   ├── AutoTriageUtility.py          # Core triage utilities
│   ├── CompareSimilarity.py          # String and image comparison
│   ├── DBQueryExecutor.py            # Database operations
│   ├── JiraAuth.py                   # JIRA authentication and operations
│   ├── LocalDBQueries.py             # Local database management
│   ├── UpdateMetesRun.py             # Update test run metadata
│   └── utils.py                      # General utilities
│
├── wats_feature_triage.py            # Core triage logic
├── wats_feature_triage_driver.py     # Driver-specific triage
├── wats_feature_triage_rider.py      # Rider-specific triage
├── wats_feature_triage_freight.py    # Freight-specific triage
├── wats_feature_triage_u4b.py        # U4B-specific triage
├── wats_feature_triage_londongrat.py # London GRAT-specific triage
├── wats_feature_triage_tooling.py    # Tooling-specific triage
├── wats_feature_triage_customerobsession.py # Customer Obsession triage
├── AddComment.py                     # JIRA comment utilities
├── WebTriageSkipped.py               # Handle skipped triage items
└── clean.py                          # Cleanup utilities
```

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to WATS database
- JIRA API credentials

### Setup

1. Navigate to the project directory:
```bash
cd /home/vgarud/vgarud_nfs/AutoTraiging/WTA/flask_app
```

2. Create a virtual environment:
```bash
python3 -m venv venv
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🏃 Running the Application

### Development Mode

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Production Mode

For production, use Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
```

## 📡 API Endpoints

### 1. Health Check

**GET** `/api/hello`
- Returns API status and timestamp

**Response:**
```json
{
  "message": "Hello from WATS Auto-Triage Flask API!",
  "timestamp": "2025-11-17T10:00:00",
  "status": "success"
}
```

### 2. Get Available Features

**GET** `/api/features`
- Returns list of supported features

**Response:**
```json
{
  "status": "success",
  "features": ["customerobsession", "u4b", "londongrat", "rider", "freight", "driver", "tooling"]
}
```

### 3. Run Auto-Triage

**POST** `/api/triage/run`
- Start auto-triage process for a specific feature

**Request Body:**
```json
{
  "feature_name": "driver"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Triage process started for driver",
  "task_id": "driver_1700000000.123"
}
```

### 4. Get Task Status

**GET** `/api/triage/status/<task_id>`
- Get status of a running or completed task

**Response:**
```json
{
  "status": "success",
  "task": {
    "status": "running",
    "feature": "driver",
    "started_at": "2025-11-17T10:00:00",
    "untriaged_count": 25,
    "triaged_count": 150
  }
}
```

### 5. Get Triaged Data

**GET** `/api/triage/triaged-data`
- Retrieve all triaged test data

**Response:**
```json
{
  "status": "success",
  "count": 150,
  "data": [...]
}
```

### 6. Get Untriaged Data

**GET** `/api/triage/untriaged-data?feature_name=driver`
- Retrieve untriaged data for a specific feature

**Query Parameters:**
- `feature_name` (required): Feature name

**Response:**
```json
{
  "status": "success",
  "feature": "driver",
  "count": 25,
  "data": [...]
}
```

### 7. Add JIRA Comments

**POST** `/api/comments/add`
- Add comments to JIRA tickets for failed tests

**Request Body:**
```json
{
  "exe_date": "2025-11-17",
  "triage_by": "auto-triage"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Comment addition started for 2025-11-17",
  "task_id": "comment_1700000000.123"
}
```

### 8. Process Skipped Items

**POST** `/api/triage/skipped`
- Process and triage skipped test items

**Response:**
```json
{
  "status": "success",
  "message": "Skipped triage processing started",
  "task_id": "skipped_1700000000.123"
}
```

### 9. Clean Temporary Files

**POST** `/api/clean`
- Clean up temporary files and databases

**Response:**
```json
{
  "status": "success",
  "message": "Cleanup completed successfully"
}
```

### 10. Get All Tasks

**GET** `/api/tasks`
- Get status of all tasks

**Response:**
```json
{
  "status": "success",
  "tasks": {
    "driver_1700000000.123": {...},
    "comment_1700000000.456": {...}
  }
}
```

## 🎯 Usage Examples

### Using cURL

```bash
# Run triage for driver feature
curl -X POST http://localhost:5000/api/triage/run \
  -H "Content-Type: application/json" \
  -d '{"feature_name": "driver"}'

# Get task status
curl http://localhost:5000/api/triage/status/driver_1700000000.123

# Add comments to JIRA
curl -X POST http://localhost:5000/api/comments/add \
  -H "Content-Type: application/json" \
  -d '{"exe_date": "2025-11-17", "triage_by": "auto-triage"}'
```

### Using Python

```python
import requests

# Run triage
response = requests.post('http://localhost:5000/api/triage/run',
                        json={'feature_name': 'driver'})
print(response.json())

# Get triaged data
response = requests.get('http://localhost:5000/api/triage/triaged-data')
print(response.json())
```

## 🔍 How It Works

1. **Data Collection**: Fetches triaged and untriaged test data from WATS database
2. **Failure Matching**: Compares new failures with historical data using:
   - String similarity (96% threshold)
   - Image comparison for visual validation
3. **Ticket Management**:
   - Creates new JIRA tickets for unmatched failures
   - Links matched failures to existing tickets
   - Adds comments to existing tickets
4. **Categorization**: Assigns triage categories (L1, L2) to failures
5. **Background Processing**: Long-running tasks execute asynchronously

## 🛠️ Configuration

Edit `app.py` to modify configuration:

```python
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!
app.config['DEBUG'] = False  # Set to False in production
```

## 📊 Supported Features

- **driver**: Driver team tests
- **rider**: Rider team tests
- **freight**: Freight team tests
- **u4b**: Uber for Business tests
- **londongrat**: London GRAT tests
- **tooling**: Tooling team tests
- **customerobsession**: Customer Obsession tests

## 🔒 Security Notes

⚠️ **Important for Production:**

1. Change the `SECRET_KEY` to a strong, random value
2. Set `DEBUG = False`
3. Use environment variables for sensitive data (database credentials, JIRA tokens)
4. Use a production WSGI server (Gunicorn, uWSGI)
5. Set up proper HTTPS/TLS
6. Implement authentication and authorization
7. Add rate limiting for API endpoints

## 🐛 Troubleshooting

### Port Already in Use
Change the port in `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### Database Connection Issues
Check database credentials in utility modules

### JIRA Authentication Errors
Verify JIRA API credentials and permissions

## 📝 License

Internal use only - Uber Technologies

## 👥 Contributors

WATS Auto-Triage Team

---

**Created:** November 17, 2025  
**Framework:** Flask 3.0.0  
**Python Version:** 3.8+
