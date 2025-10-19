"""
Official Quran Foundation API Integration with OAuth2
Secure API client with authentication and full Quran content
"""

import requests
import json
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin
import base64

class QuranFoundationOAuth:
    def __init__(self):
        self.load_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuranTranslator/1.0',
            'Accept': 'application/json'
        })
        self.session.timeout = 30
        self.access_token = None
        self.token_expires_at = 0
        
    def load_config(self):
        """Load API configuration from .env file"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        if not os.path.exists(env_path):
            raise FileNotFoundError(
                f"Configuration file not found: {env_path}\n"
                f"Please copy .env.example to .env and add your API credentials"
            )
        
        # Simple .env parser
        config = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        self.client_id = config.get('QURAN_CLIENT_ID')
        self.client_secret = config.get('QURAN_CLIENT_SECRET')
        self.endpoint = config.get('QURAN_ENDPOINT')
        
        if not all([self.client_id, self.client_secret, self.endpoint]):
            raise ValueError(
                "Missing required configuration. Please check your .env file:\n"
                "QURAN_CLIENT_ID, QURAN_CLIENT_SECRET, QURAN_ENDPOINT"
            )
        
        print(f"✓ Loaded API configuration for endpoint: {self.endpoint}")
    
    def get_access_token(self) -> str:
        """Get or refresh OAuth2 access token"""
        # Check if current token is still valid
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        print("🔐 Authenticating with Quran Foundation API...")
        
        # Prepare OAuth2 client credentials request
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Try different scope configurations
        scope_options = [None, '', 'quran:read', 'api:read', 'public']
        token_endpoints = [
            f"{self.endpoint}/oauth/token",
            f"{self.endpoint}/token", 
            f"{self.endpoint}/oauth2/token"
        ]
        
        for scope in scope_options:
            data = {'grant_type': 'client_credentials'}
            if scope:
                data['scope'] = scope
            
            print(f"Trying scope: {scope or 'none'}")
            
            for token_url in token_endpoints:
                try:
                    response = self.session.post(token_url, headers=headers, data=data)
                    if response.status_code == 200:
                        token_data = response.json()
                        
                        self.access_token = token_data['access_token']
                        expires_in = token_data.get('expires_in', 3600)
                        self.token_expires_at = time.time() + expires_in - 60
                        
                        print(f"✓ Authentication successful with scope '{scope or 'none'}' (expires in {expires_in}s)")
                        return self.access_token
                        
                except requests.RequestException as e:
                    if scope == scope_options[-1] and token_url == token_endpoints[-1]:
                        print(f"Last attempt failed: {e}")
                        if hasattr(e, 'response') and e.response is not None:
                            print(f"Response: {e.response.text}")
                    continue
        
        raise requests.RequestException("All authentication attempts failed. Please check your API credentials.")
    
    def make_authenticated_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make an authenticated API request"""
        token = self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Try different API base URLs and endpoint patterns
        api_patterns = [
            # Standard REST API patterns
            f"{self.endpoint}/api/v1/{endpoint}",
            f"{self.endpoint}/v1/{endpoint}",
            f"{self.endpoint}/api/{endpoint}",
            f"{self.endpoint}/{endpoint}",
            # Quran-specific patterns
            f"{self.endpoint}/quran/v1/{endpoint}",
            f"{self.endpoint}/quran/{endpoint}",
            # Alternative patterns
            f"https://api.quran.foundation/v1/{endpoint}",
            f"https://api.quran.foundation/{endpoint}",
        ]
        
        for url in api_patterns:
            try:
                print(f"Trying: {url}")
                response = self.session.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    print(f"✓ Success with: {url}")
                    return response.json()
                elif response.status_code == 404:
                    print(f"404 Not Found: {url}")
                    continue
                else:
                    print(f"Status {response.status_code}: {url}")
                    print(f"Response: {response.text[:200]}...")
                    continue
                    
            except requests.RequestException as e:
                print(f"Error with {url}: {e}")
                continue
        
        raise requests.RequestException(f"All API endpoints failed for: {endpoint}")

class QuranFoundationDataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.api = QuranFoundationOAuth()
        self.quran_file = os.path.join(data_dir, "quran_foundation_official.json")
        
        os.makedirs(data_dir, exist_ok=True)
    
    def download_complete_quran(self, translation_id: int = 20, force_refresh: bool = False) -> bool:
        """
        Download complete Quran from official API
        translation_id 20 = Saheeh International (widely supported)
        """
        if os.path.exists(self.quran_file) and not force_refresh:
            print(f"Official Quran data already exists at {self.quran_file}")
            return True
        
        print("📖 Downloading complete Quran from Official Quran Foundation API...")
        
        try:
            # Get list of chapters/surahs
            print("1. Fetching chapters list...")
            chapters_data = self.api.make_authenticated_request("chapters")
            chapters = chapters_data.get('chapters', chapters_data.get('data', []))
            
            if not chapters:
                print("✗ No chapters found in API response")
                return False
            
            print(f"✓ Found {len(chapters)} chapters")
            
            # Build complete Quran data structure
            quran_data = {
                "source": "Official Quran Foundation API",
                "translation_id": translation_id,
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "api_endpoint": self.api.endpoint,
                "surahs": []
            }
            
            # Download each chapter with verses
            for i, chapter in enumerate(chapters, 1):
                chapter_id = chapter.get('id', chapter.get('number', i))
                chapter_name = chapter.get('name_simple', chapter.get('name', f'Chapter {chapter_id}'))
                
                print(f"2. Downloading Chapter {i}/{len(chapters)}: {chapter_name}")
                
                try:
                    # Get verses for this chapter
                    verses_endpoint = f"chapters/{chapter_id}/verses"
                    verses_params = {'translations': translation_id}
                    
                    verses_data = self.api.make_authenticated_request(verses_endpoint, verses_params)
                    verses = verses_data.get('verses', verses_data.get('data', []))
                    
                    if not verses:
                        print(f"⚠ No verses found for chapter {chapter_id}")
                        continue
                    
                    # Process verses
                    processed_verses = []
                    for verse in verses:
                        # Extract Arabic text
                        arabic_text = verse.get('text_uthmani', verse.get('text', ''))
                        
                        # Extract translation
                        translation = ""
                        if 'translations' in verse and verse['translations']:
                            translation = verse['translations'][0].get('text', '')
                        elif 'translation' in verse:
                            translation = verse['translation']
                        
                        processed_verse = {
                            "number": verse.get('verse_number', verse.get('number', 0)),
                            "verse_key": verse.get('verse_key', f"{chapter_id}:{verse.get('verse_number', 0)}"),
                            "arabic": arabic_text,
                            "translation": translation,
                            "juz": verse.get('juz_number', 0),
                            "hizb": verse.get('hizb_number', 0),
                            "page": verse.get('page_number', 0)
                        }
                        processed_verses.append(processed_verse)
                    
                    # Add chapter to quran data
                    chapter_data = {
                        "number": chapter_id,
                        "name": chapter_name,
                        "name_arabic": chapter.get('name_arabic', ''),
                        "revelation_place": chapter.get('revelation_place', ''),
                        "verses_count": len(processed_verses),
                        "verses": processed_verses
                    }
                    quran_data["surahs"].append(chapter_data)
                    
                    print(f"   ✓ {len(processed_verses)} verses")
                    
                    # Small delay to be respectful to the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ✗ Error downloading chapter {chapter_id}: {e}")
                    continue
            
            # Save to file
            with open(self.quran_file, 'w', encoding='utf-8') as f:
                json.dump(quran_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Official Quran data saved to {self.quran_file}")
            print(f"Total chapters: {len(quran_data['surahs'])}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error downloading from official API: {e}")
            return False
    
    def get_data_stats(self) -> Dict:
        """Get statistics about the downloaded data"""
        try:
            if not os.path.exists(self.quran_file):
                return {"error": "No official data available"}
            
            with open(self.quran_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_verses = sum(len(surah.get('verses', [])) for surah in data.get('surahs', []))
            
            return {
                "chapters": len(data.get('surahs', [])),
                "total_verses": total_verses,
                "translation_id": data.get('translation_id'),
                "source": data.get('source'),
                "api_endpoint": data.get('api_endpoint'),
                "downloaded_at": data.get('downloaded_at')
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Test the official API"""
    try:
        manager = QuranFoundationDataManager()
        
        print("Official Quran Foundation API Test")
        print("=" * 40)
        
        # Test authentication
        print("Testing authentication...")
        token = manager.api.get_access_token()
        print(f"✓ Got access token: {token[:20]}...")
        
        # Download complete Quran
        print("\nDownloading complete Quran...")
        success = manager.download_complete_quran()
        
        if success:
            stats = manager.get_data_stats()
            print("\nData statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        print("\nDone!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()