from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AppointmentCreate(BaseModel):
    patient_name: str
    doctor_name: str
    appointment_time: datetime
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    patient_name: str
    doctor_name: str
    appointment_time: datetime
    notes: Optional[str]
    status: str
    created_at: datetime

class PatientQuery(BaseModel):
    patient_name: str

class PatientInfo(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    date_of_birth: Optional[datetime]
    last_visit: Optional[datetime]
    medical_history: List[str]

class VoiceCommand(BaseModel):
    text: str
    generate_audio_response: bool = False

class TranscriptionResult(BaseModel):
    transcription: str
    confidence: float
    timestamp: datetime

class CommandResult(BaseModel):
    intent: str
    response: str
    data: Optional[dict] = None
    confidence: float 