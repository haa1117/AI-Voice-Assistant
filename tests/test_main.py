import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database.db_manager import DatabaseManager

@pytest.fixture
async def async_client():
    """Create async client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_db():
    """Create test database"""
    test_db_path = "test_assistx.db"
    db_manager = DatabaseManager(test_db_path)
    await db_manager.initialize()
    await db_manager.populate_demo_data()
    
    yield db_manager
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Test health check endpoint"""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

@pytest.mark.asyncio
async def test_dashboard_route(async_client):
    """Test main dashboard route"""
    response = await async_client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_appointments(async_client):
    """Test getting appointments"""
    response = await async_client.get("/api/appointments")
    assert response.status_code == 200
    
    data = response.json()
    assert "appointments" in data
    assert isinstance(data["appointments"], list)

@pytest.mark.asyncio
async def test_get_patients(async_client):
    """Test getting patients"""
    response = await async_client.get("/api/patients")
    assert response.status_code == 200
    
    data = response.json()
    assert "patients" in data
    assert isinstance(data["patients"], list)

@pytest.mark.asyncio
async def test_create_appointment(async_client):
    """Test creating appointment"""
    appointment_data = {
        "patient_name": "Test Patient",
        "doctor_name": "Dr. Test",
        "appointment_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "notes": "Test appointment"
    }
    
    response = await async_client.post("/api/appointments/create", json=appointment_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "appointment_id" in data
    assert data["status"] == "created"

@pytest.mark.asyncio
async def test_query_patient(async_client):
    """Test querying patient information"""
    query_data = {"patient_name": "Ahmed Raza"}
    
    response = await async_client.post("/api/patients/query", json=query_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "patient" in data

@pytest.mark.asyncio
async def test_process_voice_command(async_client):
    """Test processing voice commands"""
    command_data = {
        "text": "Show appointments",
        "generate_audio_response": False
    }
    
    response = await async_client.post("/api/voice/process-command", json=command_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "command" in data
    assert "interpretation" in data
    assert "response" in data

@pytest.mark.asyncio
async def test_voice_command_book_appointment(async_client):
    """Test booking appointment via voice command"""
    command_data = {
        "text": "Book an appointment for John Doe at 3 PM tomorrow",
        "generate_audio_response": False
    }
    
    response = await async_client.post("/api/voice/process-command", json=command_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["interpretation"] == "book_appointment"
    assert "appointment_id" in data.get("data", {})

@pytest.mark.asyncio
async def test_voice_command_query_patient(async_client):
    """Test patient query via voice command"""
    command_data = {
        "text": "Show last visit for Ahmed Raza",
        "generate_audio_response": False
    }
    
    response = await async_client.post("/api/voice/process-command", json=command_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["interpretation"] == "query_patient"

@pytest.mark.asyncio
async def test_invalid_voice_command(async_client):
    """Test handling of invalid voice commands"""
    command_data = {
        "text": "xyz invalid command abc",
        "generate_audio_response": False
    }
    
    response = await async_client.post("/api/voice/process-command", json=command_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data

@pytest.mark.asyncio
async def test_get_logs(async_client):
    """Test getting system logs"""
    response = await async_client.get("/api/logs")
    assert response.status_code == 200
    
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)

@pytest.mark.asyncio
async def test_missing_patient_query(async_client):
    """Test querying non-existent patient"""
    query_data = {"patient_name": "Non Existent Patient"}
    
    response = await async_client.post("/api/patients/query", json=query_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "patient" in data

# Performance tests
@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """Test handling concurrent requests"""
    tasks = []
    
    for i in range(10):
        task = async_client.get("/api/health")
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    
    for response in responses:
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 