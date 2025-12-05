#!/usr/bin/env python3
"""
Initialize all required databases for ForgeMarketing
Creates database files and schemas on first run
"""

import sqlite3
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def init_databases():
    """Initialize all database files and schemas"""
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    print("🗄️  Initializing ForgeMarketing Databases")
    print("=" * 50)
    
    # 1. Marketing Dashboard Database (main)
    print("\n1. Marketing Dashboard Database")
    try:
        from dashboard.app import app, db
        with app.app_context():
            db.create_all()
            print("   ✅ Schema created: brands, email configs, API credentials")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        print("   Creating empty database file...")
        db_path = data_dir / 'marketing_dashboard.db'
        conn = sqlite3.connect(str(db_path))
        conn.close()
        print(f"   ✅ Created: {db_path}")
    
    # 2. Unified Outreach Database
    print("\n2. Unified Outreach Database")
    db_path = data_dir / 'unified_outreach.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            brand TEXT NOT NULL,
            email TEXT NOT NULL,
            name TEXT,
            company TEXT,
            status TEXT DEFAULT 'pending',
            contacted_at TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unified_outreach_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            target_email TEXT NOT NULL,
            subject TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unified_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            target_email TEXT NOT NULL,
            response_text TEXT,
            responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    print("      Tables: campaigns, targets, outreach_log, responses")
    
    # 3. Unified Contacts Database
    print("\n3. Unified Contacts Database")
    db_path = data_dir / 'unified_contacts.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            company TEXT,
            brand TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    
    # 4. Influencer Discovery Database
    print("\n4. Influencer Discovery Database")
    db_path = data_dir / 'influencer_discovery.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            platform TEXT,
            followers INTEGER,
            engagement_rate REAL,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'discovered'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discovery_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            platform TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    
    # 5. Activity Tracker Database
    print("\n5. Activity Tracker Database")
    db_path = data_dir / 'activity_tracker.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            content_type TEXT NOT NULL,
            prompt TEXT,
            result TEXT,
            quality_score REAL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    
    # 6. Cron Management Database
    print("\n6. Cron Management Database")
    db_path = data_dir / 'cron_management.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cron_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT UNIQUE NOT NULL,
            brand TEXT,
            schedule TEXT NOT NULL,
            script_path TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cron_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            status TEXT NOT NULL,
            output TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    
    # 7. Email Stats Database
    print("\n7. Email Stats Database")
    db_path = data_dir / 'email_stats.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            campaign_type TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            delivered INTEGER DEFAULT 0,
            opens INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            bounces INTEGER DEFAULT 0,
            date DATE NOT NULL,
            service TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created: {db_path}")
    
    print("\n" + "=" * 50)
    print("✅ All databases initialized successfully!")
    print(f"📁 Location: {data_dir}")
    print("\nNext steps:")
    print("1. Start the server: ./ops/startup.sh start")
    print("2. Complete onboarding at: http://localhost:8002/onboarding")
    print("=" * 50)

if __name__ == '__main__':
    try:
        init_databases()
    except Exception as e:
        print(f"\n❌ Error initializing databases: {e}")
        sys.exit(1)
