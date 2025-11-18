# Simple Flask Web Application

A clean and modern Flask web application with a responsive UI.

## Features

- Home page with interactive greeting form
- About page
- RESTful API endpoint
- Modern, responsive design
- Error handling (404 page)

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Project Structure

```
flask_web_app/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   └── 404.html
└── static/           # Static files (CSS, JS)
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## API Endpoints

### POST /api/greet
Greets a user by name.

**Request:**
```json
{
  "name": "John"
}
```

**Response:**
```json
{
  "message": "Hello, John! Welcome to the Flask app.",
  "status": "success"
}
```
