import nltk
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class CommandInterpreter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.intent_patterns = self._load_intent_patterns()
        self._initialize_nltk()
    
    def _initialize_nltk(self):
        """Initialize NLTK components"""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('wordnet', quiet=True)
            
            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize
            from nltk.stem import WordNetLemmatizer
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
            logger.info("NLTK initialized successfully")
            
        except Exception as e:
            logger.error(f"NLTK initialization error: {e}")
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for intent recognition"""
        return {
            'book_appointment': [
                r'book.*appointment.*for\s+([a-zA-Z\s]+)',
                r'schedule.*appointment.*([a-zA-Z\s]+)',
                r'make.*appointment.*([a-zA-Z\s]+)',
                r'set.*appointment.*([a-zA-Z\s]+)',
                r'appointment.*([a-zA-Z\s]+).*at\s+(\d+)',
                r'book.*([a-zA-Z\s]+).*(\d+\s*(?:am|pm|AM|PM))',
                r'schedule.*([a-zA-Z\s]+).*(\d+\s*(?:am|pm|AM|PM))',
            ],
            'query_patient': [
                r'show.*(?:last\s+visit|history|info|information).*for\s+([a-zA-Z\s]+)',
                r'get.*(?:patient|info|information).*([a-zA-Z\s]+)',
                r'find.*patient.*([a-zA-Z\s]+)',
                r'look.*up.*([a-zA-Z\s]+)',
                r'tell.*me.*about.*([a-zA-Z\s]+)',
                r'what.*about.*([a-zA-Z\s]+)',
                r'([a-zA-Z\s]+).*patient.*information',
            ],
            'view_appointments': [
                r'show.*appointments',
                r'list.*appointments',
                r'what.*appointments',
                r'view.*appointments',
                r'appointments.*today',
                r'today.*appointments',
                r'schedule.*today',
            ],
            'view_patients': [
                r'show.*patients',
                r'list.*patients',
                r'all.*patients',
                r'view.*patients',
                r'patient.*list',
            ],
            'greeting': [
                r'hello', r'hi', r'hey', r'good morning', r'good afternoon', r'good evening'
            ],
            'help': [
                r'help', r'what.*can.*you.*do', r'commands', r'assistance'
            ]
        }
    
    async def interpret(self, command: str) -> Dict:
        """Interpret natural language command"""
        try:
            # Clean and preprocess command
            cleaned_command = self._preprocess_command(command)
            
            # Extract intent and entities
            intent, entities, confidence = self._extract_intent_and_entities(cleaned_command)
            
            # Process the command based on intent
            result = await self._process_intent(intent, entities, cleaned_command)
            
            # Log the interaction
            await self.db_manager.log_voice_interaction(
                transcription=command,
                command_type=intent,
                response=result["response"],
                confidence=confidence
            )
            
            return {
                "intent": intent,
                "response": result["response"],
                "data": result.get("data"),
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Command interpretation error: {e}")
            return {
                "intent": "error",
                "response": f"Sorry, I couldn't understand that command. Error: {str(e)}",
                "data": None,
                "confidence": 0.0
            }
    
    def _preprocess_command(self, command: str) -> str:
        """Clean and preprocess the command"""
        # Convert to lowercase
        command = command.lower().strip()
        
        # Remove extra whitespace
        command = re.sub(r'\s+', ' ', command)
        
        # Remove punctuation except for important ones
        command = re.sub(r'[^\w\s@.:,-]', '', command)
        
        return command
    
    def _extract_intent_and_entities(self, command: str) -> Tuple[str, Dict, float]:
        """Extract intent and entities from command"""
        best_intent = "unknown"
        best_confidence = 0.0
        entities = {}
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    confidence = len(match.group(0)) / len(command)
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
                        
                        # Extract entities based on groups
                        if match.groups():
                            if intent == 'book_appointment':
                                entities = self._extract_appointment_entities(command, match)
                            elif intent == 'query_patient':
                                entities = self._extract_patient_entities(command, match)
        
        return best_intent, entities, best_confidence
    
    def _extract_appointment_entities(self, command: str, match) -> Dict:
        """Extract appointment-related entities"""
        entities = {}
        
        # Extract patient name
        if match.groups():
            patient_name = match.group(1).strip()
            entities['patient_name'] = patient_name
        
        # Extract time information
        time_patterns = [
            r'(\d+)\s*(?:am|pm|AM|PM)',
            r'at\s+(\d+)',
            r'(\d+:\d+)',
            r'(tomorrow|today|next\s+\w+)',
            r'(\d+\s*(?:am|pm|AM|PM))'
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, command)
            if time_match:
                entities['time'] = time_match.group(1)
                break
        
        # Extract doctor name
        doctor_match = re.search(r'(?:with|doctor|dr\.?)\s+([a-zA-Z\s]+)', command)
        if doctor_match:
            entities['doctor'] = doctor_match.group(1).strip()
        else:
            entities['doctor'] = "Dr. Smith"  # Default doctor
        
        return entities
    
    def _extract_patient_entities(self, command: str, match) -> Dict:
        """Extract patient-related entities"""
        entities = {}
        
        if match.groups():
            patient_name = match.group(1).strip()
            entities['patient_name'] = patient_name
        
        return entities
    
    async def _process_intent(self, intent: str, entities: Dict, command: str) -> Dict:
        """Process the interpreted intent"""
        
        if intent == "book_appointment":
            return await self._handle_book_appointment(entities, command)
        
        elif intent == "query_patient":
            return await self._handle_query_patient(entities)
        
        elif intent == "view_appointments":
            return await self._handle_view_appointments()
        
        elif intent == "view_patients":
            return await self._handle_view_patients()
        
        elif intent == "greeting":
            return {
                "response": "Hello! I'm AssistX, your medical assistant. How can I help you today?",
                "data": None
            }
        
        elif intent == "help":
            return {
                "response": self._get_help_message(),
                "data": None
            }
        
        else:
            return {
                "response": "I'm sorry, I didn't understand that command. Try asking me to book an appointment, show patient information, or list appointments.",
                "data": None
            }
    
    async def _handle_book_appointment(self, entities: Dict, command: str) -> Dict:
        """Handle appointment booking"""
        try:
            patient_name = entities.get('patient_name', '').title()
            doctor_name = entities.get('doctor', 'Dr. Smith')
            time_str = entities.get('time', '')
            
            if not patient_name:
                return {
                    "response": "I need a patient name to book an appointment. Please specify who the appointment is for.",
                    "data": None
                }
            
            # Parse time
            appointment_time = self._parse_time(time_str, command)
            
            # Create appointment
            appointment_id = await self.db_manager.create_appointment(
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_time=appointment_time,
                notes=f"Booked via voice command: {command}"
            )
            
            response = f"Appointment booked successfully for {patient_name} with {doctor_name} on {appointment_time.strftime('%Y-%m-%d at %I:%M %p')}. Appointment ID: {appointment_id}"
            
            return {
                "response": response,
                "data": {
                    "appointment_id": appointment_id,
                    "patient_name": patient_name,
                    "doctor_name": doctor_name,
                    "appointment_time": appointment_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {
                "response": f"Sorry, I couldn't book the appointment. Please try again with more specific details.",
                "data": None
            }
    
    async def _handle_query_patient(self, entities: Dict) -> Dict:
        """Handle patient information queries"""
        try:
            patient_name = entities.get('patient_name', '').title()
            
            if not patient_name:
                return {
                    "response": "Please specify which patient you'd like information about.",
                    "data": None
                }
            
            patient_info = await self.db_manager.get_patient_info(patient_name)
            
            if "error" in patient_info:
                return {
                    "response": patient_info["error"],
                    "data": None
                }
            
            # Format response
            response = f"Patient: {patient_info['name']}\n"
            if patient_info.get('phone'):
                response += f"Phone: {patient_info['phone']}\n"
            
            if patient_info.get('recent_visits'):
                last_visit = patient_info['recent_visits'][0]
                response += f"Last visit: {last_visit['visit_date']} with {last_visit['doctor_name']}\n"
                if last_visit.get('diagnosis'):
                    response += f"Diagnosis: {last_visit['diagnosis']}\n"
            
            if patient_info.get('upcoming_appointments'):
                next_appointment = patient_info['upcoming_appointments'][0]
                response += f"Next appointment: {next_appointment['appointment_time']} with {next_appointment['doctor_name']}"
            
            return {
                "response": response,
                "data": patient_info
            }
            
        except Exception as e:
            logger.error(f"Error querying patient: {e}")
            return {
                "response": "Sorry, I couldn't retrieve the patient information.",
                "data": None
            }
    
    async def _handle_view_appointments(self) -> Dict:
        """Handle viewing appointments"""
        try:
            appointments = await self.db_manager.get_appointments()
            
            if not appointments:
                return {
                    "response": "No appointments scheduled.",
                    "data": []
                }
            
            # Format upcoming appointments
            upcoming = [apt for apt in appointments if 
                       datetime.fromisoformat(apt['appointment_time'].replace('Z', '+00:00')) > datetime.now()]
            
            response = f"You have {len(upcoming)} upcoming appointments:\n"
            for apt in upcoming[:5]:  # Show first 5
                apt_time = datetime.fromisoformat(apt['appointment_time'].replace('Z', '+00:00'))
                response += f"- {apt['patient_name']} with {apt['doctor_name']} on {apt_time.strftime('%Y-%m-%d at %I:%M %p')}\n"
            
            return {
                "response": response,
                "data": upcoming
            }
            
        except Exception as e:
            logger.error(f"Error viewing appointments: {e}")
            return {
                "response": "Sorry, I couldn't retrieve the appointments.",
                "data": None
            }
    
    async def _handle_view_patients(self) -> Dict:
        """Handle viewing patients"""
        try:
            patients = await self.db_manager.get_all_patients()
            
            if not patients:
                return {
                    "response": "No patients in the database.",
                    "data": []
                }
            
            response = f"You have {len(patients)} patients registered:\n"
            for patient in patients[:10]:  # Show first 10
                response += f"- {patient['name']}"
                if patient.get('phone'):
                    response += f" ({patient['phone']})"
                response += "\n"
            
            return {
                "response": response,
                "data": patients
            }
            
        except Exception as e:
            logger.error(f"Error viewing patients: {e}")
            return {
                "response": "Sorry, I couldn't retrieve the patient list.",
                "data": None
            }
    
    def _parse_time(self, time_str: str, full_command: str) -> datetime:
        """Parse time string into datetime object"""
        try:
            now = datetime.now()
            
            # Handle relative time expressions
            if "tomorrow" in full_command:
                base_date = now + timedelta(days=1)
            elif "today" in full_command:
                base_date = now
            elif "next week" in full_command:
                base_date = now + timedelta(weeks=1)
            else:
                base_date = now + timedelta(hours=1)  # Default to 1 hour from now
            
            # Parse specific time
            if time_str:
                try:
                    # Try to parse as time
                    parsed_time = date_parser.parse(time_str)
                    # Combine with base date
                    return base_date.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                        second=0,
                        microsecond=0
                    )
                except:
                    # If parsing fails, extract hour from string
                    hour_match = re.search(r'(\d+)', time_str)
                    if hour_match:
                        hour = int(hour_match.group(1))
                        if 'pm' in time_str.lower() and hour < 12:
                            hour += 12
                        elif 'am' in time_str.lower() and hour == 12:
                            hour = 0
                        
                        return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # Default to next hour
            return base_date.replace(minute=0, second=0, microsecond=0)
            
        except Exception as e:
            logger.error(f"Time parsing error: {e}")
            # Default to 1 hour from now
            return datetime.now() + timedelta(hours=1)
    
    def _get_help_message(self) -> str:
        """Get help message with available commands"""
        return """I can help you with the following commands:

1. Book appointments: "Book an appointment for John Doe at 3 PM tomorrow"
2. Query patients: "Show last visit for Ahmed Raza"
3. View appointments: "Show today's appointments"  
4. View patients: "List all patients"

You can speak naturally, and I'll understand your requests!""" 