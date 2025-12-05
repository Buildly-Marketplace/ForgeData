"""
Database Migration Script
Migrates hardcoded credentials from environment variables to database
Run this after initializing the database schema
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dashboard.app import create_app
from config.config_loader import config_loader
from config.brand_loader import get_all_brands


def migrate_credentials():
    """Migrate credentials from environment to database"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting credential migration...")
        
        # Migrate system-wide configurations
        print("\n📋 Migrating system configurations...")
        system_configs = [
            ('OLLAMA_HOST', 'http://localhost:11434', 'Ollama AI server host', False, 'ai'),
            ('OLLAMA_MODEL', 'llama3.2:1b', 'Default Ollama model', False, 'ai'),
            ('FLASK_ENV', 'production', 'Flask environment', False, 'system'),
            ('SECRET_KEY', os.getenv('SECRET_KEY', os.urandom(24).hex()), 'Flask secret key', True, 'system'),
            ('GOOGLE_ANALYTICS_API_KEY', os.getenv('GOOGLE_ANALYTICS_API_KEY', ''), 'Google Analytics API Key', True, 'analytics'),
        ]
        
        for key, default, description, is_secret, category in system_configs:
            value = os.getenv(key, default)
            if value:
                config_loader.set_system_config(
                    key=key,
                    value=str(value),
                    description=description,
                    is_secret=is_secret,
                    category=category,
                    updated_by='migration'
                )
                print(f"  ✓ Migrated {key}")
        
        # Migrate brand-specific credentials - load from database
        brands = get_all_brands(active_only=False)
        print(f"\n🏢 Found {len(brands)} brands in database: {', '.join(brands)}")
        
        for brand in brands:
            print(f"\n🏢 Migrating credentials for {brand}...")
            
            # Twitter credentials
            twitter_creds = {
                'api_key': os.getenv(f'{brand.upper()}_TWITTER_API_KEY', os.getenv('TWITTER_API_KEY', '')),
                'api_secret': os.getenv(f'{brand.upper()}_TWITTER_API_SECRET', os.getenv('TWITTER_API_SECRET', '')),
                'access_token': os.getenv(f'{brand.upper()}_TWITTER_ACCESS_TOKEN', os.getenv('TWITTER_ACCESS_TOKEN', '')),
                'access_token_secret': os.getenv(f'{brand.upper()}_TWITTER_ACCESS_TOKEN_SECRET', os.getenv('TWITTER_ACCESS_TOKEN_SECRET', '')),
                'bearer_token': os.getenv(f'{brand.upper()}_TWITTER_BEARER_TOKEN', os.getenv('TWITTER_BEARER_TOKEN', ''))
            }
            
            if any(twitter_creds.values()):
                config_loader.set_brand_api_credential(
                    brand_name=brand,
                    service='twitter',
                    credential_type='oauth',
                    credentials=twitter_creds
                )
                print(f"  ✓ Twitter credentials")
            
            # Google Analytics credentials
            ga_creds = {
                'property_id': os.getenv(f'{brand.upper()}_GA_PROPERTY_ID', ''),
                'api_key': os.getenv('GOOGLE_ANALYTICS_API_KEY', ''),
                'credentials_file': os.getenv('GOOGLE_ANALYTICS_CREDENTIALS_FILE', '')
            }
            
            if ga_creds['property_id']:
                config_loader.set_brand_api_credential(
                    brand_name=brand,
                    service='google_analytics',
                    credential_type='api_key',
                    credentials=ga_creds
                )
                print(f"  ✓ Google Analytics credentials")
            
            # YouTube credentials
            youtube_creds = {
                'api_key': os.getenv(f'{brand.upper()}_YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY', '')),
                'channel_id': os.getenv(f'{brand.upper()}_YOUTUBE_CHANNEL_ID', os.getenv('YOUTUBE_CHANNEL_ID', ''))
            }
            
            if youtube_creds['channel_id']:
                config_loader.set_brand_api_credential(
                    brand_name=brand,
                    service='youtube',
                    credential_type='api_key',
                    credentials=youtube_creds
                )
                print(f"  ✓ YouTube credentials")
        
        print("\n✅ Migration completed successfully!")
        print("\n⚠️  IMPORTANT: Update your deployment to remove hardcoded credentials")
        print("   Credentials are now stored securely in the database")


if __name__ == '__main__':
    migrate_credentials()
