"""
Configuration management for Quran Translator
Handles API credentials, feature flags, and settings
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
            'QURAN_ENVIRONMENT': 'production',
            'QURAN_ENDPOINT': 'https://oauth2.quran.foundation',
            'FALLBACK_API': 'https://api.alquran.cloud/v1',
            'DEFAULT_TRANSLATION': 20,  # Saheeh International
            'OAUTH_REDIRECT_PORT': 8765,
            # Feature flags
            'USE_OFFICIAL_API': False,
            'USE_FOUNDATION_CONTENT_API': True,
            'USE_OFFLINE_FALLBACK': True,
        }

        # Load from .env if it exists
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Parse booleans
                        if value.lower() in ('true', '1', 'yes'):
                            value = True
                        elif value.lower() in ('false', '0', 'no'):
                            value = False
                        self.config[key] = value

            # Check if official API credentials are available
            if self.config.get('QURAN_CLIENT_ID') and self.config.get('QURAN_CLIENT_SECRET'):
                self.config['USE_OFFICIAL_API'] = True
                print("✓ Quran.Foundation API credentials found")
            else:
                print("⚠ API credentials not found, using offline fallback")
                self.config['USE_FOUNDATION_CONTENT_API'] = False
        else:
            print("⚠ No .env file found, using offline fallback only")
            self.config['USE_FOUNDATION_CONTENT_API'] = False

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def has_official_api(self) -> bool:
        """Check if official API credentials are available"""
        return bool(self.config.get('USE_OFFICIAL_API', False))

    def use_foundation_api(self) -> bool:
        """Check if Foundation Content API should be used (feature flag)"""
        return bool(self.config.get('USE_FOUNDATION_CONTENT_API', False)) and self.has_official_api()

    def use_offline_fallback(self) -> bool:
        """Check if offline fallback data should be used"""
        return bool(self.config.get('USE_OFFLINE_FALLBACK', True))

    @property
    def client_id(self) -> Optional[str]:
        return self.config.get('QURAN_CLIENT_ID')

    @property
    def client_secret(self) -> Optional[str]:
        return self.config.get('QURAN_CLIENT_SECRET')

    @property
    def environment(self) -> str:
        return self.config.get('QURAN_ENVIRONMENT', 'production')

    @property
    def redirect_port(self) -> int:
        try:
            return int(self.config.get('OAUTH_REDIRECT_PORT', 8765))
        except (ValueError, TypeError):
            return 8765


# Global config instance
config = Config()