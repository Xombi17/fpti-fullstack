"""
Database initialization script for FPTI.
"""
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

try:
    from app.database import init_db, engine
    from app.models import Base
    print("Initializing FPTI database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    
    # Initialize database
    init_db()
    print("✓ Database initialized successfully!")
    
    print("\nDatabase setup complete. You can now:")
    print("1. Run 'python create_sample_data.py' to add sample data")
    print("2. Start the backend server: cd backend && python main.py")
    print("3. Start the frontend: cd frontend && python app.py")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure you've installed all dependencies and you're in the correct directory")
    print("Current working directory:", os.getcwd())
    print("Backend path:", backend_path)
    print("Backend exists:", os.path.exists(backend_path))
except Exception as e:
    print(f"✗ Database initialization failed: {e}")