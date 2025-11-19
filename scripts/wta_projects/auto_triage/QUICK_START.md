# 🚀 Quick Start Guide - WATS Auto-Triage Flask App

## ⚡ Instant Setup

### Option 1: Using the Startup Script (Recommended)
```bash
cd /home/vgarud/vgarud_nfs/AutoTraiging/WTA/flask_app
./run.sh
```

That's it! The script will:
- Create virtual environment (if needed)
- Install dependencies
- Start the Flask server

### Option 2: Manual Setup
```bash
cd /home/vgarud/vgarud_nfs/AutoTraiging/WTA/flask_app

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## 🌐 Access the Application

Once running, open your browser and go to:
**http://localhost:5000**

Or access the API directly:
**http://localhost:5000/api/hello**

## 🎯 First Steps

### 1. Web UI (Easiest)
1. Open http://localhost:5000 in your browser
2. Select a feature from the dropdown (e.g., "Driver")
3. Click "Start Triage"
4. Watch the results appear in real-time

### 2. API Testing
```bash
# Test the API is working
curl http://localhost:5000/api/hello

# Get list of features
curl http://localhost:5000/api/features

# Run triage for driver feature
curl -X POST http://localhost:5000/api/triage/run \
  -H "Content-Type: application/json" \
  -d '{"feature_name": "driver"}'
```

## 📋 Common Tasks

### Run Auto-Triage for a Feature
**Via Web UI:**
1. Select feature from dropdown
2. Click "Start Triage"

**Via API:**
```bash
curl -X POST http://localhost:5000/api/triage/run \
  -H "Content-Type: application/json" \
  -d '{"feature_name": "driver"}'
```

### Add Comments to JIRA Tickets
**Via Web UI:**
1. Select date (defaults to today)
2. Click "Add Comments to JIRA"

**Via API:**
```bash
curl -X POST http://localhost:5000/api/comments/add \
  -H "Content-Type: application/json" \
  -d '{"exe_date": "2025-11-17", "triage_by": "auto-triage"}'
```

### View Triaged Data
**Via Web UI:**
- Click "Get Triaged Data" button

**Via API:**
```bash
curl http://localhost:5000/api/triage/triaged-data
```

### Clean Temporary Files
**Via Web UI:**
- Click "Clean Temporary Files" button

**Via API:**
```bash
curl -X POST http://localhost:5000/api/clean
```

## 🔧 Configuration

### Environment Variables (Optional)
Copy the example file and customize:
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

### Change Port
Edit `app.py` and change:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```
to your desired port.

## 📊 Available Features

You can run triage for these features:
- `driver` - Driver team tests
- `rider` - Rider team tests
- `freight` - Freight team tests
- `u4b` - Uber for Business tests
- `londongrat` - London GRAT tests
- `tooling` - Tooling team tests
- `customerobsession` - Customer Obsession tests

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process or change the port in app.py
```

### "Module not found"
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "Database connection error"
- Check database credentials in utility modules
- Verify network access to database

## 📚 More Information

- Full documentation: See `README.md`
- Conversion details: See `CONVERSION_SUMMARY.md`
- API endpoints: See README.md or visit http://localhost:5000

## 🆘 Need Help?

1. Check the logs in the terminal where Flask is running
2. Review `README.md` for detailed documentation
3. Check `CONVERSION_SUMMARY.md` for conversion details

## 🎉 You're Ready!

The Flask application is now set up and ready to use. Happy triaging! 🚀
