// AssistX Dashboard JavaScript

class AssistXDashboard {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.recentCommands = [];
        
        this.initializeEventListeners();
        this.loadInitialData();
        this.checkVoiceStatus();
    }
    
    initializeEventListeners() {
        // Voice recording buttons
        document.getElementById('record-btn').addEventListener('click', () => this.startRecording());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopRecording());
        
        // Text command submission
        document.getElementById('submit-text-btn').addEventListener('click', () => this.submitTextCommand());
        document.getElementById('text-command').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitTextCommand();
        });
        
        // Refresh buttons
        window.refreshAppointments = () => this.loadAppointments();
        window.refreshPatients = () => this.loadPatients();
        
        // Patient info modal
        window.showPatientInfo = (patientName) => this.showPatientInfo(patientName);
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadAppointments(),
            this.loadPatients(),
            this.updateStatusCards()
        ]);
    }
    
    async checkVoiceStatus() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            
            const statusCard = document.getElementById('voice-status-card');
            const statusText = document.getElementById('voice-status');
            
            if (health.status === 'healthy') {
                statusCard.className = 'card bg-success text-white';
                statusText.textContent = 'Voice Ready';
            } else {
                statusCard.className = 'card bg-warning text-white';
                statusText.textContent = 'Voice Limited';
            }
        } catch (error) {
            const statusCard = document.getElementById('voice-status-card');
            const statusText = document.getElementById('voice-status');
            statusCard.className = 'card bg-danger text-white';
            statusText.textContent = 'Voice Offline';
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.recordedChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateRecordingUI(true);
            
            this.showFeedback('Listening... Speak your command now.');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showErrorFeedback('Microphone access denied or not available.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
            this.showFeedback('Processing your voice command...');
            
            // Stop all audio tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
    
    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('record-btn');
        const stopBtn = document.getElementById('stop-btn');
        
        if (recording) {
            recordBtn.disabled = true;
            recordBtn.classList.add('recording');
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Recording...';
            stopBtn.disabled = false;
        } else {
            recordBtn.disabled = false;
            recordBtn.classList.remove('recording');
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
            stopBtn.disabled = true;
        }
    }
    
    async processRecording() {
        try {
            const audioBlob = new Blob(this.recordedChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            
            // Transcribe audio
            const transcribeResponse = await fetch('/api/voice/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const transcriptionResult = await transcribeResponse.json();
            
            if (transcriptionResult.transcription) {
                // Process the command
                await this.processCommand(transcriptionResult.transcription);
            } else {
                this.showErrorFeedback('Could not understand audio. Please try again.');
            }
            
        } catch (error) {
            console.error('Error processing recording:', error);
            this.showErrorFeedback('Error processing audio. Please try again.');
        } finally {
            this.hideFeedback();
        }
    }
    
    async submitTextCommand() {
        const commandInput = document.getElementById('text-command');
        const command = commandInput.value.trim();
        
        if (!command) return;
        
        this.showFeedback('Processing your command...');
        await this.processCommand(command);
        commandInput.value = '';
        this.hideFeedback();
    }
    
    async processCommand(commandText) {
        try {
            const audioResponse = document.getElementById('audio-response-toggle').checked;
            
            const response = await fetch('/api/voice/process-command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: commandText,
                    generate_audio_response: audioResponse
                })
            });
            
            const result = await response.json();
            
            // Display response
            this.displayResponse(result.response);
            
            // Add to recent commands
            this.addRecentCommand(commandText, result.interpretation);
            
            // Refresh data if needed
            if (result.interpretation === 'book_appointment') {
                await this.loadAppointments();
                await this.updateStatusCards();
            } else if (result.interpretation === 'query_patient') {
                // Show patient info if data is available
                if (result.data && !result.data.error) {
                    this.showPatientModal(result.data);
                }
            }
            
            // Play audio response if available
            if (result.audio_response && audioResponse) {
                this.playAudioResponse(result.audio_response);
            }
            
        } catch (error) {
            console.error('Error processing command:', error);
            this.displayResponse('Sorry, there was an error processing your command.');
        }
    }
    
    displayResponse(responseText) {
        const responseArea = document.getElementById('response-text');
        responseArea.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${responseText}</pre>`;
    }
    
    addRecentCommand(command, intent) {
        const now = new Date();
        this.recentCommands.unshift({
            command: command,
            intent: intent,
            timestamp: now.toLocaleTimeString()
        });
        
        // Keep only last 10 commands
        if (this.recentCommands.length > 10) {
            this.recentCommands = this.recentCommands.slice(0, 10);
        }
        
        this.updateRecentCommandsDisplay();
    }
    
    updateRecentCommandsDisplay() {
        const container = document.getElementById('recent-commands');
        
        if (this.recentCommands.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent commands</p>';
            return;
        }
        
        const commandsHTML = this.recentCommands.map(cmd => `
            <div class="command-item">
                <div class="command-text">${cmd.command}</div>
                <div class="command-time">
                    <small><i class="fas fa-clock me-1"></i>${cmd.timestamp} - ${cmd.intent}</small>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = commandsHTML;
    }
    
    async loadAppointments() {
        try {
            const response = await fetch('/api/appointments');
            const data = await response.json();
            
            const tableBody = document.getElementById('appointments-table');
            
            if (data.appointments && data.appointments.length > 0) {
                const appointmentsHTML = data.appointments.map(apt => {
                    const date = new Date(apt.appointment_time);
                    const statusClass = apt.status === 'scheduled' ? 'bg-success' : 
                                       apt.status === 'completed' ? 'bg-primary' : 'bg-warning';
                    
                    return `
                        <tr>
                            <td><strong>${apt.patient_name}</strong></td>
                            <td>${apt.doctor_name}</td>
                            <td>${date.toLocaleDateString()} ${date.toLocaleTimeString()}</td>
                            <td><span class="badge ${statusClass}">${apt.status}</span></td>
                            <td>${apt.notes || '-'}</td>
                        </tr>
                    `;
                }).join('');
                
                tableBody.innerHTML = appointmentsHTML;
            } else {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No appointments found</td></tr>';
            }
            
        } catch (error) {
            console.error('Error loading appointments:', error);
            document.getElementById('appointments-table').innerHTML = 
                '<tr><td colspan="5" class="text-center text-danger">Error loading appointments</td></tr>';
        }
    }
    
    async loadPatients() {
        try {
            const response = await fetch('/api/patients');
            const data = await response.json();
            
            const tableBody = document.getElementById('patients-table');
            
            if (data.patients && data.patients.length > 0) {
                const patientsHTML = data.patients.map(patient => {
                    const dob = patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : '-';
                    
                    return `
                        <tr>
                            <td><strong>${patient.name}</strong></td>
                            <td>${patient.phone || '-'}</td>
                            <td>${patient.email || '-'}</td>
                            <td>${dob}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="showPatientInfo('${patient.name}')">
                                    <i class="fas fa-eye"></i> View
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
                
                tableBody.innerHTML = patientsHTML;
            } else {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No patients found</td></tr>';
            }
            
        } catch (error) {
            console.error('Error loading patients:', error);
            document.getElementById('patients-table').innerHTML = 
                '<tr><td colspan="5" class="text-center text-danger">Error loading patients</td></tr>';
        }
    }
    
    async showPatientInfo(patientName) {
        try {
            const response = await fetch('/api/patients/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ patient_name: patientName })
            });
            
            const data = await response.json();
            
            if (data.patient && !data.patient.error) {
                this.showPatientModal(data.patient);
            } else {
                alert('Patient information not found.');
            }
            
        } catch (error) {
            console.error('Error loading patient info:', error);
            alert('Error loading patient information.');
        }
    }
    
    showPatientModal(patientData) {
        const modalBody = document.getElementById('patient-modal-body');
        
        let visitsHTML = '';
        if (patientData.recent_visits && patientData.recent_visits.length > 0) {
            visitsHTML = patientData.recent_visits.map(visit => `
                <div class="card mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title">${new Date(visit.visit_date).toLocaleDateString()} - ${visit.doctor_name}</h6>
                        <p class="card-text mb-1"><strong>Diagnosis:</strong> ${visit.diagnosis || 'N/A'}</p>
                        <p class="card-text mb-1"><strong>Treatment:</strong> ${visit.treatment || 'N/A'}</p>
                        <p class="card-text mb-0"><strong>Notes:</strong> ${visit.notes || 'N/A'}</p>
                    </div>
                </div>
            `).join('');
        } else {
            visitsHTML = '<p class="text-muted">No recent visits</p>';
        }
        
        let appointmentsHTML = '';
        if (patientData.upcoming_appointments && patientData.upcoming_appointments.length > 0) {
            appointmentsHTML = patientData.upcoming_appointments.map(apt => `
                <div class="card mb-2">
                    <div class="card-body p-3">
                        <h6 class="card-title">${new Date(apt.appointment_time).toLocaleDateString()} - ${apt.doctor_name}</h6>
                        <p class="card-text mb-0"><strong>Notes:</strong> ${apt.notes || 'N/A'}</p>
                    </div>
                </div>
            `).join('');
        } else {
            appointmentsHTML = '<p class="text-muted">No upcoming appointments</p>';
        }
        
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Patient Details</h6>
                    <p><strong>Name:</strong> ${patientData.name}</p>
                    <p><strong>Phone:</strong> ${patientData.phone || 'N/A'}</p>
                    <p><strong>Email:</strong> ${patientData.email || 'N/A'}</p>
                    <p><strong>Date of Birth:</strong> ${patientData.date_of_birth ? new Date(patientData.date_of_birth).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div class="col-md-6">
                    <h6>Recent Visits</h6>
                    ${visitsHTML}
                </div>
            </div>
            <div class="mt-3">
                <h6>Upcoming Appointments</h6>
                ${appointmentsHTML}
            </div>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('patientModal'));
        modal.show();
    }
    
    async updateStatusCards() {
        try {
            const [appointmentsResponse, patientsResponse] = await Promise.all([
                fetch('/api/appointments'),
                fetch('/api/patients')
            ]);
            
            const appointmentsData = await appointmentsResponse.json();
            const patientsData = await patientsResponse.json();
            
            // Update patient count
            document.getElementById('total-patients').textContent = patientsData.patients ? patientsData.patients.length : 0;
            
            // Update appointment counts
            const appointments = appointmentsData.appointments || [];
            document.getElementById('total-appointments').textContent = appointments.length;
            
            // Count today's appointments
            const today = new Date().toDateString();
            const todayAppointments = appointments.filter(apt => {
                const aptDate = new Date(apt.appointment_time).toDateString();
                return aptDate === today;
            });
            document.getElementById('today-appointments').textContent = todayAppointments.length;
            
        } catch (error) {
            console.error('Error updating status cards:', error);
        }
    }
    
    showFeedback(message) {
        const feedback = document.getElementById('voice-feedback');
        const feedbackText = document.getElementById('feedback-text');
        
        feedbackText.textContent = message;
        feedback.classList.remove('d-none');
    }
    
    showErrorFeedback(message) {
        const feedback = document.getElementById('voice-feedback');
        const feedbackText = document.getElementById('feedback-text');
        
        feedback.className = 'alert alert-danger';
        feedbackText.textContent = message;
        feedback.classList.remove('d-none');
        
        setTimeout(() => {
            feedback.className = 'alert alert-info d-none';
        }, 3000);
    }
    
    hideFeedback() {
        const feedback = document.getElementById('voice-feedback');
        feedback.classList.add('d-none');
    }
    
    playAudioResponse(audioPath) {
        // This would need to be implemented based on how audio files are served
        console.log('Audio response available:', audioPath);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AssistXDashboard();
}); 