"""
Quran Text Matching Module
Handles matching recognized Arabic text to Quran verses
"""

import json
import re
from typing import Optional, List, Dict, Tuple
from difflib import SequenceMatcher
import unicodedata

class QuranMatcher:
    def __init__(self, quran_data_path: str = "data/quran.json"):
        self.quran_data = {}
        self.verse_index = {}
        
        # Mapping for mysterious letters and common variations
        self.special_mappings = {
            'ياسين': 'يس',
            'طاها': 'طه', 
            'حاميم': 'حم',
            'صاد': 'ص',
            'قاف': 'ق',
            'نون': 'ن',
            # Add more common spoken forms
            'الف لام ميم': 'الم',
            'الف لام راء': 'الر',
            'كاف ها يا عين صاد': 'كهيعص',
        }
        
        self.load_quran_data(quran_data_path)
        self.build_search_index()
    
    def load_quran_data(self, data_path: str):
        """Load Quran data from JSON file"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.quran_data = json.load(f)
            print(f"Loaded Quran data with {len(self.quran_data.get('surahs', []))} surahs")
        except FileNotFoundError:
            print(f"Quran data file not found: {data_path}")
            # Try to load complete Quran data
            complete_data_path = data_path.replace('sample_quran.json', 'quran_complete.json')
            try:
                with open(complete_data_path, 'r', encoding='utf-8') as f:
                    self.quran_data = json.load(f)
                print(f"Loaded complete Quran data with {len(self.quran_data.get('surahs', []))} surahs")
            except FileNotFoundError:
                print("Complete Quran data not found either, creating sample data")
                self.create_sample_data()
        except Exception as e:
            print(f"Error loading Quran data: {e}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample Quran data for testing"""
        self.quran_data = {
            "surahs": [
                {
                    "number": 1,
                    "name": "Al-Fatihah",
                    "verses": [
                        {
                            "number": 1,
                            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                            "translation": "In the name of Allah, the Entirely Merciful, the Especially Merciful."
                        },
                        {
                            "number": 2,
                            "arabic": "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                            "translation": "All praise is due to Allah, Lord of the worlds."
                        },
                        {
                            "number": 3,
                            "arabic": "الرَّحْمَٰنِ الرَّحِيمِ",
                            "translation": "The Entirely Merciful, the Especially Merciful,"
                        }
                    ]
                }
            ]
        }
    
    def build_search_index(self):
        """Build search index for faster verse lookup"""
        self.verse_index = {}
        
        for surah in self.quran_data.get('surahs', []):
            surah_num = surah['number']
            for verse in surah.get('verses', []):
                verse_num = verse['number']
                arabic_text = verse['arabic']
                
                # Normalize Arabic text for better matching
                normalized_text = self.normalize_arabic_text(arabic_text)
                
                # Create multiple index entries for different text segments
                words = normalized_text.split()
                
                # Index by full text
                self.verse_index[normalized_text] = {
                    'surah': surah_num,
                    'verse': verse_num,
                    'arabic': arabic_text,
                    'translation': verse['translation'],
                    'surah_name': surah['name']
                }
                
                # Index by word combinations (for partial matching)
                for i in range(len(words)):
                    for j in range(i + 3, min(len(words) + 1, i + 8)):  # 3-7 word phrases
                        phrase = ' '.join(words[i:j])
                        if phrase not in self.verse_index:
                            self.verse_index[phrase] = {
                                'surah': surah_num,
                                'verse': verse_num,
                                'arabic': arabic_text,
                                'translation': verse['translation'],
                                'surah_name': surah['name']
                            }
    
    def normalize_arabic_text(self, text: str) -> str:
        """Normalize Arabic text for better matching"""
        # Remove BOM and invisible characters
        text = text.replace('\ufeff', '').replace('\u200f', '').replace('\u200e', '')
        
        # Apply special mappings FIRST (before other normalizations)
        for full_form, short_form in self.special_mappings.items():
            text = text.replace(full_form, short_form)
        
        # Handle special cases for mysterious letters and common variations
        # Ya-Sin variations: يس، ياسين، يٰسٓ
        text = re.sub(r'يٰسٓ', 'يس', text)   # Convert API form to short form
        
        # Other mysterious letters normalizations
        text = re.sub(r'طٰهٰ', 'طه', text)   # Ta-Ha
        text = re.sub(r'حٰمٓ', 'حم', text)   # Ha-Mim
        
        # Remove all diacritics (tashkeel) - expanded range including special marks
        text = re.sub(r'[\u064B-\u065F\u0670\u0640\u06D6-\u06ED\u08F0-\u08FF\u06E5-\u06E6]', '', text)
        
        # Normalize different forms of alef (including the API's ٱ)
        # But preserve the definite article ال
        text = re.sub(r'ٱل', 'ال', text)  # Convert API alef-lam to regular first
        text = re.sub(r'[آأإ]', 'ا', text)  # Then normalize other alefs (but not ٱ in ال)
        
        # Normalize different forms of yeh
        text = re.sub(r'[يىئ]', 'ي', text)
        
        # Normalize different forms of heh
        text = re.sub(r'[هة]', 'ه', text)
        
        # Normalize different forms of waw
        text = re.sub(r'[وؤ]', 'و', text)
        
        # Handle common speech variations
        # "يا أيها" variations - normalize different forms
        text = re.sub(r'يا\s*ايها', 'يا أيها', text)
        text = re.sub(r'يا\s*أيها', 'يا أيها', text)
        text = re.sub(r'يَٰٓأَيُّهَا', 'يا أيها', text)  # API form to speech form
        
        # Remove extra whitespace and normalize spaces
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase equivalent (for Arabic this helps with some variations)
        text = text.lower()
        
        return text
    
    def find_matching_verse(self, recognized_text: str, threshold: float = 0.3) -> Optional[Dict]:
        """Find the best matching verse for recognized text"""
        if not recognized_text:
            return None
        
        normalized_input = self.normalize_arabic_text(recognized_text)
        best_match = None
        best_score = 0
        
        # Try exact match first
        if normalized_input in self.verse_index:
            result = self.verse_index[normalized_input].copy()
            result['confidence'] = 1.0
            return result
        
        # Try fuzzy matching with all indexed text
        for indexed_text, verse_info in self.verse_index.items():
            score = self.calculate_similarity(normalized_input, indexed_text)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = verse_info.copy()
        
        # Also try substring matching for partial recognition
        if not best_match or best_score < 0.7:
            for indexed_text, verse_info in self.verse_index.items():
                # Check if recognized text is contained in verse or vice versa
                if (normalized_input in indexed_text or indexed_text in normalized_input) and len(normalized_input) > 2:
                    containment_score = min(len(normalized_input), len(indexed_text)) / max(len(normalized_input), len(indexed_text))
                    if containment_score > best_score and containment_score >= threshold:
                        best_score = containment_score
                        best_match = verse_info.copy()
        
        # Try word-level matching for inputs (including single words)
        if not best_match:
            input_words = set(normalized_input.split())
            for indexed_text, verse_info in self.verse_index.items():
                indexed_words = set(indexed_text.split())
                
                # Check if most input words are found in the verse
                common_words = input_words.intersection(indexed_words)
                if common_words:
                    word_score = len(common_words) / len(input_words) if input_words else 0
                    # Bonus for longer matches
                    if len(common_words) >= 2:
                        word_score *= 1.2
                    
                    if word_score > best_score and word_score >= 0.2:  # Lower threshold for word matching
                        best_score = word_score
                        best_match = verse_info.copy()
        
        # Try partial phrase matching (remove common prefixes like Bismillah)
        if not best_match:
            # Remove Bismillah from both input and indexed text for comparison
            bismillah_pattern = r'بسم\s+الله\s+الرحمن\s+الرحيم\s*'
            clean_input = re.sub(bismillah_pattern, '', normalized_input).strip()
            
            if clean_input and len(clean_input) > 5:  # Only if there's substantial content left
                for indexed_text, verse_info in self.verse_index.items():
                    clean_indexed = re.sub(bismillah_pattern, '', indexed_text).strip()
                    
                    if clean_indexed:
                        phrase_score = self.calculate_similarity(clean_input, clean_indexed)
                        if phrase_score > best_score and phrase_score >= 0.3:
                            best_score = phrase_score
                            best_match = verse_info.copy()
        
        if best_match:
            best_match['confidence'] = best_score
            return best_match
        
        return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two Arabic texts"""
        # Use sequence matcher for basic similarity
        basic_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Word-level similarity for better Arabic matching
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return basic_similarity
        
        word_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        
        # Combine both similarities
        return (basic_similarity * 0.4) + (word_similarity * 0.6)
    
    def search_verses(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for verses containing the query"""
        normalized_query = self.normalize_arabic_text(query)
        results = []
        
        for indexed_text, verse_info in self.verse_index.items():
            if normalized_query in indexed_text:
                score = self.calculate_similarity(normalized_query, indexed_text)
                verse_info_copy = verse_info.copy()
                verse_info_copy['confidence'] = score
                results.append(verse_info_copy)
        
        # Sort by confidence and return top results
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:limit]
    
    def get_verse_context(self, surah: int, verse: int, context_size: int = 2) -> Dict:
        """Get verse with surrounding context"""
        result = {
            'main_verse': None,
            'context_before': [],
            'context_after': []
        }
        
        # Find the surah
        target_surah = None
        for surah_data in self.quran_data.get('surahs', []):
            if surah_data['number'] == surah:
                target_surah = surah_data
                break
        
        if not target_surah:
            return result
        
        verses = target_surah.get('verses', [])
        target_verse_idx = None
        
        # Find the target verse
        for i, verse_data in enumerate(verses):
            if verse_data['number'] == verse:
                target_verse_idx = i
                result['main_verse'] = verse_data
                break
        
        if target_verse_idx is None:
            return result
        
        # Get context before
        start_idx = max(0, target_verse_idx - context_size)
        result['context_before'] = verses[start_idx:target_verse_idx]
        
        # Get context after
        end_idx = min(len(verses), target_verse_idx + context_size + 1)
        result['context_after'] = verses[target_verse_idx + 1:end_idx]
        
        return result