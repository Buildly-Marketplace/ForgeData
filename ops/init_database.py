"""
Database Initialization Script
Creates all database tables and initializes default brands
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dashboard.app import create_app
from dashboard.database import DatabaseManager


def init_database():
    """Initialize database with all tables and default data"""
    
    print("🗄️  ForgeMarketing Database Initialization")
    print("=" * 50)
    
    app = create_app()
    db_manager = DatabaseManager(app)
    
    # Initialize database
    success = db_manager.init_db()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Database initialized successfully!")
        print("\nNext steps:")
        print("1. Run credential migration:")
        print("   python3 ops/migrate_credentials.py")
        print("\n2. Start the server:")
        print("   ./ops/startup.sh start")
        print("\n3. Access admin panel:")
        print("   http://localhost:8002/admin")
    else:
        print("\n" + "=" * 50)
        print("❌ Database initialization failed!")
        print("Check the error messages above for details.")
        sys.exit(1)


if __name__ == '__main__':
    init_database()
