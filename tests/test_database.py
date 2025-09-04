import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

@pytest.fixture
async def test_db():
    """Create test database"""
    test_db_path = "test_db.db"
    db_manager = DatabaseManager(test_db_path)
    await db_manager.initialize()
    
    yield db_manager
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.mark.asyncio
async def test_database_initialization(test_db):
    """Test database initialization"""
    # Database should be created and accessible
    assert test_db is not None

@pytest.mark.asyncio
async def test_create_appointment(test_db):
    """Test creating appointments"""
    appointment_time = datetime.now() + timedelta(hours=2)
    
    appointment_id = await test_db.create_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Test",
        appointment_time=appointment_time,
        notes="Test appointment"
    )
    
    assert appointment_id > 0

@pytest.mark.asyncio
async def test_get_appointments(test_db):
    """Test getting appointments"""
    # Create test appointment
    appointment_time = datetime.now() + timedelta(hours=2)
    await test_db.create_appointment(
        patient_name="Test Patient",
        doctor_name="Dr. Test",
        appointment_time=appointment_time
    )
    
    appointments = await test_db.get_appointments()
    assert len(appointments) > 0
    assert appointments[0]["patient_name"] == "Test Patient"

@pytest.mark.asyncio
async def test_get_all_patients(test_db):
    """Test getting all patients"""
    # Populate with demo data first
    await test_db.populate_demo_data()
    
    patients = await test_db.get_all_patients()
    assert len(patients) > 0

@pytest.mark.asyncio
async def test_get_patient_info(test_db):
    """Test getting patient information"""
    # Populate with demo data first
    await test_db.populate_demo_data()
    
    patient_info = await test_db.get_patient_info("Ahmed Raza")
    assert "name" in patient_info
    assert patient_info["name"] == "Ahmed Raza"

@pytest.mark.asyncio
async def test_get_nonexistent_patient(test_db):
    """Test getting info for non-existent patient"""
    patient_info = await test_db.get_patient_info("Non Existent Patient")
    assert "error" in patient_info

@pytest.mark.asyncio
async def test_log_voice_interaction(test_db):
    """Test logging voice interactions"""
    await test_db.log_voice_interaction(
        transcription="Test command",
        command_type="test",
        response="Test response",
        confidence=0.95
    )
    
    # Should not raise any exceptions

@pytest.mark.asyncio
async def test_demo_data_population(test_db):
    """Test demo data population"""
    await test_db.populate_demo_data()
    
    patients = await test_db.get_all_patients()
    appointments = await test_db.get_appointments()
    
    # Should have demo data
    assert len(patients) > 0
    assert len(appointments) > 0

@pytest.mark.asyncio
async def test_duplicate_demo_data(test_db):
    """Test that demo data is not duplicated"""
    await test_db.populate_demo_data()
    patients_count_1 = len(await test_db.get_all_patients())
    
    # Try to populate again
    await test_db.populate_demo_data()
    patients_count_2 = len(await test_db.get_all_patients())
    
    # Should be the same count (no duplicates)
    assert patients_count_1 == patients_count_2

@pytest.mark.asyncio
async def test_appointment_time_handling(test_db):
    """Test proper handling of appointment times"""
    future_time = datetime.now() + timedelta(days=1, hours=3)
    
    appointment_id = await test_db.create_appointment(
        patient_name="Time Test Patient",
        doctor_name="Dr. Time",
        appointment_time=future_time
    )
    
    appointments = await test_db.get_appointments()
    created_appointment = next(apt for apt in appointments if apt["id"] == appointment_id)
    
    assert created_appointment is not None
    assert created_appointment["patient_name"] == "Time Test Patient"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 