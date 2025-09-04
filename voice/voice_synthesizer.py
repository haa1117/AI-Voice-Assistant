import logging
import asyncio
import os
from datetime import datetime
from typing import Optional

# Handle potential compatibility issues
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError as e:
    logging.warning(f"pyttsx3 not available: {e}")
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    def __init__(self):
        self.engine = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize text-to-speech engine"""
        if not PYTTSX3_AVAILABLE:
            logger.warning("pyttsx3 not available - voice synthesis disabled")
            return
            
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to set a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.engine.setProperty('voice', voices[0].id)
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
            
            logger.info("Voice synthesizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Voice synthesizer initialization error: {e}")
            self.engine = None
    
    async def generate_response(self, text: str, save_to_file: bool = True) -> Optional[str]:
        """Generate speech from text"""
        if not PYTTSX3_AVAILABLE:
            logger.warning("Voice synthesis not available - pyttsx3 compatibility issue")
            return None
            
        if not self.engine:
            logger.warning("Voice synthesizer not available")
            return None
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            
            if save_to_file:
                # Generate audio file
                filename = f"voice_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                file_path = os.path.join("voice_logs", filename)
                
                # Ensure voice_logs directory exists
                os.makedirs("voice_logs", exist_ok=True)
                
                # Save to file
                self.engine.save_to_file(clean_text, file_path)
                self.engine.runAndWait()
                
                logger.info(f"Voice response saved to {file_path}")
                return file_path
            else:
                # Just speak without saving
                self.engine.say(clean_text)
                self.engine.runAndWait()
                logger.info(f"Spoke text: {clean_text[:50]}...")
                return "spoken"
                
        except Exception as e:
            logger.error(f"Voice synthesis error: {e}")
            return None
    
    async def speak_text(self, text: str):
        """Speak text immediately without saving"""
        if not PYTTSX3_AVAILABLE:
            logger.warning("Voice synthesis not available - pyttsx3 compatibility issue")
            return
            
        if not self.engine:
            logger.warning("Voice synthesizer not available")
            return
        
        try:
            clean_text = self._clean_text(text)
            self.engine.say(clean_text)
            self.engine.runAndWait()
            logger.info(f"Spoke: {clean_text[:50]}...")
            
        except Exception as e:
            logger.error(f"Speech error: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        # Remove special characters that might cause issues
        clean_text = text.replace('\n', ' ').replace('\t', ' ')
        
        # Replace common abbreviations with full words for better pronunciation
        replacements = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            'Ltd.': 'Limited',
            'Inc.': 'Incorporated',
            '&': 'and',
            '%': 'percent',
            '@': 'at',
            '#': 'number'
        }
        
        for abbrev, full in replacements.items():
            clean_text = clean_text.replace(abbrev, full)
        
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        
        return clean_text
    
    def set_voice_properties(self, rate: int = None, volume: float = None, voice_id: str = None):
        """Set voice properties"""
        if not PYTTSX3_AVAILABLE or not self.engine:
            return
        
        try:
            if rate is not None:
                self.engine.setProperty('rate', rate)
            
            if volume is not None:
                self.engine.setProperty('volume', min(1.0, max(0.0, volume)))
            
            if voice_id is not None:
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if voice.id == voice_id:
                        self.engine.setProperty('voice', voice.id)
                        break
            
            logger.info("Voice properties updated")
            
        except Exception as e:
            logger.error(f"Error setting voice properties: {e}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not PYTTSX3_AVAILABLE or not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [{'id': voice.id, 'name': voice.name, 'age': voice.age, 'gender': voice.gender} 
                    for voice in voices] if voices else []
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if voice synthesizer is available"""
        return PYTTSX3_AVAILABLE and self.engine is not None 