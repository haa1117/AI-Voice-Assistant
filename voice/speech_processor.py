import logging
import os
import asyncio
from typing import Optional
import numpy as np

# Handle Python 3.13 compatibility issues
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SpeechRecognition not available: {e}")
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Soundfile not available: {e}")
    SOUNDFILE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.whisper_model = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize speech recognition components"""
        try:
            # Initialize microphone (with fallback)
            if SPEECH_RECOGNITION_AVAILABLE:
                try:
                    self.recognizer = sr.Recognizer()
                    self.microphone = sr.Microphone()
                    logger.info("Microphone initialized successfully")
                except Exception as e:
                    logger.warning(f"Microphone initialization failed: {e}")
            
            # Load Whisper model (lightweight for demo)
            if WHISPER_AVAILABLE:
                try:
                    self.whisper_model = whisper.load_model("base")
                    logger.info("Whisper model loaded successfully")
                except Exception as e:
                    logger.warning(f"Whisper model loading failed: {e}")
                
        except Exception as e:
            logger.error(f"Speech processor initialization error: {e}")
    
    async def transcribe_file(self, audio_file_path: str) -> str:
        """Transcribe audio file using Whisper or SpeechRecognition"""
        if not SPEECH_RECOGNITION_AVAILABLE and not WHISPER_AVAILABLE:
            return "Speech recognition not available - compatibility issue"
            
        try:
            # Try Whisper first (more accurate)
            if self.whisper_model and os.path.exists(audio_file_path):
                result = self.whisper_model.transcribe(audio_file_path)
                transcription = result["text"].strip()
                logger.info(f"Whisper transcription: {transcription}")
                return transcription
            
            # Fallback to SpeechRecognition
            if SPEECH_RECOGNITION_AVAILABLE and self.recognizer:
                with sr.AudioFile(audio_file_path) as source:
                    audio = self.recognizer.record(source)
                    transcription = self.recognizer.recognize_google(audio)
                    logger.info(f"Google Speech Recognition transcription: {transcription}")
                    return transcription
            
            return "No speech recognition engines available"
                
        except Exception as e:
            if SPEECH_RECOGNITION_AVAILABLE:
                if hasattr(sr, 'UnknownValueError') and isinstance(e, sr.UnknownValueError):
                    logger.warning("Speech was unintelligible")
                    return "Could not understand audio"
                elif hasattr(sr, 'RequestError') and isinstance(e, sr.RequestError):
                    logger.error(f"Speech recognition service error: {e}")
                    return f"Speech recognition error: {e}"
            
            logger.error(f"Transcription error: {e}")
            return f"Transcription failed: {e}"
    
    async def transcribe_microphone(self, timeout: int = 5) -> str:
        """Transcribe from microphone input"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return "Speech recognition not available - compatibility issue"
            
        if not self.microphone or not self.recognizer:
            return "Microphone not available"
        
        try:
            with self.microphone as source:
                logger.info("Listening for speech...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                logger.info("Processing speech...")
                
                # Try Google Speech Recognition first
                try:
                    transcription = self.recognizer.recognize_google(audio)
                    logger.info(f"Microphone transcription: {transcription}")
                    return transcription
                except sr.UnknownValueError:
                    return "Could not understand speech"
                except sr.RequestError:
                    # Fallback to offline recognition if available
                    try:
                        transcription = self.recognizer.recognize_sphinx(audio)
                        logger.info(f"Offline transcription: {transcription}")
                        return transcription
                    except:
                        return "Speech recognition service unavailable"
                        
        except Exception as e:
            if hasattr(sr, 'WaitTimeoutError') and isinstance(e, sr.WaitTimeoutError):
                logger.warning("No speech detected within timeout")
                return "No speech detected"
            
            logger.error(f"Microphone transcription error: {e}")
            return f"Microphone error: {e}"
    
    async def process_audio_stream(self, audio_data: bytes) -> str:
        """Process audio stream data"""
        try:
            # Save temporary audio file
            temp_file = f"voice_logs/stream_temp_{int(asyncio.get_event_loop().time())}.wav"
            
            # Convert bytes to audio file
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transcribe the temporary file
            transcription = await self.transcribe_file(temp_file)
            
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return transcription
            
        except Exception as e:
            logger.error(f"Audio stream processing error: {e}")
            return f"Stream processing failed: {e}"
    
    def is_available(self) -> bool:
        """Check if speech processing is available"""
        return (WHISPER_AVAILABLE and self.whisper_model is not None) or (SPEECH_RECOGNITION_AVAILABLE and self.microphone is not None) 