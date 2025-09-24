#!/bin/bash

# FPTI Application Startup Script

echo "Starting FPTI - Financial Portfolio Tracking Interface"
echo "======================================================"

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python init_db.py

# Create sample data
echo "Creating sample data..."
python create_sample_data.py

echo ""
echo "Setup complete! Starting services..."
echo ""

# Start backend in background
echo "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend dashboard..."
cd frontend
python app.py &
FRONTEND_PID=$!
cd ..

echo ""
echo "FPTI is now running!"
echo "- Backend API: http://localhost:8000"
echo "- Frontend Dashboard: http://localhost:8050"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT
wait