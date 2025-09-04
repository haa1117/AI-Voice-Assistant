import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "database/assistx.db"):
        self.db_path = db_path
        
    async def initialize(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create patients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    date_of_birth DATE,
                    medical_history TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create appointments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT NOT NULL,
                    doctor_name TEXT NOT NULL,
                    appointment_time TIMESTAMP NOT NULL,
                    notes TEXT,
                    status TEXT DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create visits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT NOT NULL,
                    doctor_name TEXT NOT NULL,
                    visit_date TIMESTAMP NOT NULL,
                    diagnosis TEXT,
                    treatment TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create voice_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcription TEXT NOT NULL,
                    command_type TEXT,
                    response TEXT,
                    confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    async def create_appointment(self, patient_name: str, doctor_name: str, 
                               appointment_time: datetime, notes: str = None) -> int:
        """Create a new appointment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO appointments (patient_name, doctor_name, appointment_time, notes)
                VALUES (?, ?, ?, ?)
            ''', (patient_name, doctor_name, appointment_time, notes))
            
            appointment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created appointment {appointment_id} for {patient_name}")
            return appointment_id
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise
    
    async def get_appointments(self) -> List[Dict]:
        """Get all appointments"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM appointments 
                ORDER BY appointment_time ASC
            ''')
            
            appointments = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return appointments
            
        except Exception as e:
            logger.error(f"Error fetching appointments: {e}")
            raise
    
    async def get_patient_info(self, patient_name: str) -> Dict:
        """Get patient information and history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get patient basic info
            cursor.execute('''
                SELECT * FROM patients WHERE name LIKE ?
            ''', (f"%{patient_name}%",))
            
            patient = cursor.fetchone()
            
            if not patient:
                return {"error": f"Patient {patient_name} not found"}
            
            patient_dict = dict(patient)
            
            # Get recent visits
            cursor.execute('''
                SELECT * FROM visits 
                WHERE patient_name LIKE ? 
                ORDER BY visit_date DESC LIMIT 5
            ''', (f"%{patient_name}%",))
            
            visits = [dict(row) for row in cursor.fetchall()]
            patient_dict["recent_visits"] = visits
            
            # Get upcoming appointments
            cursor.execute('''
                SELECT * FROM appointments 
                WHERE patient_name LIKE ? AND appointment_time > ?
                ORDER BY appointment_time ASC
            ''', (f"%{patient_name}%", datetime.now()))
            
            appointments = [dict(row) for row in cursor.fetchall()]
            patient_dict["upcoming_appointments"] = appointments
            
            conn.close()
            return patient_dict
            
        except Exception as e:
            logger.error(f"Error fetching patient info: {e}")
            raise
    
    async def get_all_patients(self) -> List[Dict]:
        """Get all patients"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM patients ORDER BY name')
            patients = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return patients
            
        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            raise
    
    async def log_voice_interaction(self, transcription: str, command_type: str = None, 
                                  response: str = None, confidence: float = None):
        """Log voice interaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO voice_logs (transcription, command_type, response, confidence)
                VALUES (?, ?, ?, ?)
            ''', (transcription, command_type, response, confidence))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error logging voice interaction: {e}")
    
    async def populate_demo_data(self):
        """Populate database with demo data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute('SELECT COUNT(*) FROM patients')
            if cursor.fetchone()[0] > 0:
                conn.close()
                return
            
            # Demo patients
            demo_patients = [
                ("Ahmed Raza", "555-0101", "ahmed.raza@email.com", "1985-03-15", 
                 '["Hypertension", "Diabetes Type 2"]'),
                ("Fatima Ali", "555-0102", "fatima.ali@email.com", "1992-07-22", 
                 '["Asthma", "Allergies"]'),
                ("Omar Khan", "555-0103", "omar.khan@email.com", "1978-11-08", 
                 '["Back Pain", "Arthritis"]'),
                ("Zara Ahmed", "555-0104", "zara.ahmed@email.com", "1990-05-30", 
                 '["Migraine", "Anxiety"]'),
                ("Hassan Shah", "555-0105", "hassan.shah@email.com", "1982-12-12", 
                 '["High Cholesterol"]')
            ]
            
            cursor.executemany('''
                INSERT INTO patients (name, phone, email, date_of_birth, medical_history)
                VALUES (?, ?, ?, ?, ?)
            ''', demo_patients)
            
            # Demo visits
            demo_visits = [
                ("Ahmed Raza", "Dr. Smith", datetime.now() - timedelta(days=30), 
                 "Hypertension checkup", "Medication adjustment", "Blood pressure stable"),
                ("Fatima Ali", "Dr. Johnson", datetime.now() - timedelta(days=15), 
                 "Asthma follow-up", "Inhaler prescription", "Symptoms improved"),
                ("Omar Khan", "Dr. Brown", datetime.now() - timedelta(days=7), 
                 "Back pain evaluation", "Physical therapy recommended", "MRI scheduled"),
            ]
            
            cursor.executemany('''
                INSERT INTO visits (patient_name, doctor_name, visit_date, diagnosis, treatment, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', demo_visits)
            
            # Demo appointments
            demo_appointments = [
                ("Zara Ahmed", "Dr. Wilson", datetime.now() + timedelta(hours=2), 
                 "Migraine consultation", "scheduled"),
                ("Hassan Shah", "Dr. Davis", datetime.now() + timedelta(days=1), 
                 "Cholesterol follow-up", "scheduled"),
                ("Ahmed Raza", "Dr. Smith", datetime.now() + timedelta(days=3), 
                 "Regular checkup", "scheduled"),
            ]
            
            cursor.executemany('''
                INSERT INTO appointments (patient_name, doctor_name, appointment_time, notes, status)
                VALUES (?, ?, ?, ?, ?)
            ''', demo_appointments)
            
            conn.commit()
            conn.close()
            logger.info("Demo data populated successfully")
            
        except Exception as e:
            logger.error(f"Error populating demo data: {e}")
            raise 