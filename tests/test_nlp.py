import pytest
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.command_interpreter import CommandInterpreter
from database.db_manager import DatabaseManager

@pytest.fixture
async def test_interpreter():
    """Create test command interpreter"""
    test_db_path = "test_nlp_db.db"
    db_manager = DatabaseManager(test_db_path)
    await db_manager.initialize()
    await db_manager.populate_demo_data()
    
    interpreter = CommandInterpreter(db_manager)
    
    yield interpreter
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.mark.asyncio
async def test_greeting_intent(test_interpreter):
    """Test greeting intent recognition"""
    result = await test_interpreter.interpret("Hello")
    assert result["intent"] == "greeting"
    assert "AssistX" in result["response"]

@pytest.mark.asyncio
async def test_help_intent(test_interpreter):
    """Test help intent recognition"""
    result = await test_interpreter.interpret("help")
    assert result["intent"] == "help"
    assert "commands" in result["response"].lower()

@pytest.mark.asyncio
async def test_book_appointment_intent(test_interpreter):
    """Test appointment booking intent"""
    result = await test_interpreter.interpret("Book an appointment for John Doe at 3 PM tomorrow")
    assert result["intent"] == "book_appointment"
    assert "appointment_id" in result.get("data", {})

@pytest.mark.asyncio
async def test_book_appointment_variations(test_interpreter):
    """Test various appointment booking phrases"""
    commands = [
        "Schedule an appointment for Jane Smith at 2 PM",
        "Make an appointment for Bob Johnson tomorrow at 10 AM",
        "Set up an appointment for Alice Brown with Dr. Wilson"
    ]
    
    for command in commands:
        result = await test_interpreter.interpret(command)
        assert result["intent"] == "book_appointment"

@pytest.mark.asyncio
async def test_query_patient_intent(test_interpreter):
    """Test patient query intent"""
    result = await test_interpreter.interpret("Show last visit for Ahmed Raza")
    assert result["intent"] == "query_patient"
    assert "Ahmed Raza" in result["response"]

@pytest.mark.asyncio
async def test_query_patient_variations(test_interpreter):
    """Test various patient query phrases"""
    commands = [
        "Get patient information for Fatima Ali",
        "Find patient Ahmed Raza",
        "Tell me about Omar Khan",
        "What about Zara Ahmed"
    ]
    
    for command in commands:
        result = await test_interpreter.interpret(command)
        assert result["intent"] == "query_patient"

@pytest.mark.asyncio
async def test_view_appointments_intent(test_interpreter):
    """Test view appointments intent"""
    result = await test_interpreter.interpret("Show appointments")
    assert result["intent"] == "view_appointments"

@pytest.mark.asyncio
async def test_view_patients_intent(test_interpreter):
    """Test view patients intent"""
    result = await test_interpreter.interpret("List all patients")
    assert result["intent"] == "view_patients"

@pytest.mark.asyncio
async def test_unknown_intent(test_interpreter):
    """Test handling of unknown intents"""
    result = await test_interpreter.interpret("xyz random command abc")
    assert result["intent"] == "unknown"
    assert "didn't understand" in result["response"].lower()

@pytest.mark.asyncio
async def test_case_insensitive_commands(test_interpreter):
    """Test case insensitive command processing"""
    commands = [
        "SHOW APPOINTMENTS",
        "book appointment for test patient",
        "Help Me Please"
    ]
    
    for command in commands:
        result = await test_interpreter.interpret(command)
        assert result["intent"] != "unknown"

@pytest.mark.asyncio
async def test_appointment_time_parsing(test_interpreter):
    """Test appointment time parsing"""
    result = await test_interpreter.interpret("Book appointment for Test Patient at 5 PM tomorrow")
    assert result["intent"] == "book_appointment"
    
    # Check if appointment was created with proper time
    assert "data" in result
    assert "appointment_time" in result["data"]

@pytest.mark.asyncio
async def test_patient_name_extraction(test_interpreter):
    """Test patient name extraction from commands"""
    result = await test_interpreter.interpret("Show information for John Doe Smith")
    assert result["intent"] == "query_patient"

@pytest.mark.asyncio
async def test_doctor_name_extraction(test_interpreter):
    """Test doctor name extraction from appointment commands"""
    result = await test_interpreter.interpret("Book appointment for Test Patient with Dr. Johnson")
    assert result["intent"] == "book_appointment"
    
    if "data" in result:
        assert "doctor_name" in result["data"]

@pytest.mark.asyncio
async def test_command_confidence_scoring(test_interpreter):
    """Test confidence scoring for commands"""
    # Clear command should have high confidence
    result = await test_interpreter.interpret("Show appointments")
    assert result["confidence"] > 0.1
    
    # Unclear command should have lower confidence
    result = await test_interpreter.interpret("maybe show something")
    # Should still process but with lower confidence

@pytest.mark.asyncio
async def test_multiple_intents_in_command(test_interpreter):
    """Test handling commands with multiple possible intents"""
    result = await test_interpreter.interpret("Show patient John and book appointment")
    # Should pick the strongest intent
    assert result["intent"] in ["query_patient", "book_appointment"]

@pytest.mark.asyncio
async def test_empty_command(test_interpreter):
    """Test handling of empty commands"""
    result = await test_interpreter.interpret("")
    assert result["intent"] == "unknown"

@pytest.mark.asyncio
async def test_very_long_command(test_interpreter):
    """Test handling of very long commands"""
    long_command = "Please " * 50 + "show appointments"
    result = await test_interpreter.interpret(long_command)
    # Should still be processed
    assert result is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 