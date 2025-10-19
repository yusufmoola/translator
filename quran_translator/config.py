"""
Configuration management for Quran Translator
Handles API credentials and settings
"""

import os
from typing import Dict, Optional

class Config:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from .env file"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        # Default configuration
        self.config = {
            'QURAN_CLIENT_ID': None,
            'QURAN_CLIENT_SECRET': None,
            'QURAN_ENDPOINT': 'https://oauth2.quran.foundation',
            'USE_OFFICIAL_API': False,
            'FALLBACK_API': 'https://api.alquran.cloud/v1',
            'DEFAULT_TRANSLATION': 20  # Saheeh International
        }
        
        # Load from .env if it exists
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
            
            # Check if official API credentials are available
            if self.config.get('QURAN_CLIENT_ID') and self.config.get('QURAN_CLIENT_SECRET'):
                self.config['USE_OFFICIAL_API'] = True
                print("✓ Official API credentials found")
            else:
                print("⚠ Official API credentials not found, using fallback API")
        else:
            print("⚠ No .env file found, using fallback API only")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def has_official_api(self) -> bool:
        """Check if official API is available"""
        return self.config.get('USE_OFFICIAL_API', False)

# Global config instance
config = Config()