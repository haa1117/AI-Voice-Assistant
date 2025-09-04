from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os
from datetime import datetime
import logging

from database.db_manager import DatabaseManager
from voice.speech_processor import SpeechProcessor
from voice.voice_synthesizer import VoiceSynthesizer
from nlp.command_interpreter import CommandInterpreter
from models.schemas import AppointmentCreate, PatientQuery, VoiceCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/assistx.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AssistX - AI Voice Assistant for Medical Clinics",
    description="Privacy-compliant voice assistant for medical professionals",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
db_manager = DatabaseManager()
speech_processor = SpeechProcessor()
voice_synthesizer = VoiceSynthesizer()
command_interpreter = CommandInterpreter(db_manager)

@app.on_event("startup")
async def startup_event():
    """Initialize database and components on startup"""
    try:
        await db_manager.initialize()
        await db_manager.populate_demo_data()
        logger.info("AssistX started successfully")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "title": "AssistX Dashboard"}
    )

@app.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file"""
    try:
        # Save uploaded file temporarily
        temp_path = f"voice_logs/temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        # Transcribe audio
        transcription = await speech_processor.transcribe_file(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Log transcription
        logger.info(f"Transcribed: {transcription}")
        
        return {"transcription": transcription, "timestamp": datetime.now().isoformat()}
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/process-command")
async def process_voice_command(command: VoiceCommand):
    """Process natural language voice command"""
    try:
        # Interpret the command
        result = await command_interpreter.interpret(command.text)
        
        # Generate voice response if requested
        audio_response = None
        if command.generate_audio_response:
            audio_path = await voice_synthesizer.generate_response(result["response"])
            audio_response = audio_path
        
        return {
            "command": command.text,
            "interpretation": result["intent"],
            "response": result["response"],
            "data": result.get("data"),
            "audio_response": audio_response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Command processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/appointments/create")
async def create_appointment(appointment: AppointmentCreate):
    """Create new appointment"""
    try:
        appointment_id = await db_manager.create_appointment(
            patient_name=appointment.patient_name,
            doctor_name=appointment.doctor_name,
            appointment_time=appointment.appointment_time,
            notes=appointment.notes
        )
        return {"appointment_id": appointment_id, "status": "created"}
    
    except Exception as e:
        logger.error(f"Appointment creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/appointments")
async def get_appointments():
    """Get all appointments"""
    try:
        appointments = await db_manager.get_appointments()
        return {"appointments": appointments}
    
    except Exception as e:
        logger.error(f"Appointment retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patients/query")
async def query_patient(query: PatientQuery):
    """Query patient information"""
    try:
        patient_info = await db_manager.get_patient_info(query.patient_name)
        return {"patient": patient_info}
    
    except Exception as e:
        logger.error(f"Patient query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patients")
async def get_all_patients():
    """Get all patients"""
    try:
        patients = await db_manager.get_all_patients()
        return {"patients": patients}
    
    except Exception as e:
        logger.error(f"Patient retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/logs")
async def get_logs():
    """Get recent system logs"""
    try:
        with open("logs/assistx.log", "r") as f:
            lines = f.readlines()
            recent_logs = lines[-50:]  # Last 50 lines
        
        return {"logs": recent_logs}
    
    except Exception as e:
        logger.error(f"Log retrieval error: {e}")
        return {"logs": ["No logs available"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 