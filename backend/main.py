"""
Legacy Interview App - Agno Backend
Main FastAPI application with multi-agent system
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
os.environ['AGNO_LOG_LEVEL'] = 'DEBUG'

import sys
import os
# Add the parent directory to Python path so we can import from database/
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime

from agents.planner_agent import PlannerAgent
from agents.prober_agent import ProberAgent
from agents.summarizer_agent import SummarizerAgent
from agents.subject_simulator_agent import SubjectSimulatorAgent
from services.conversation_recording_service import conversation_recording_service
from services.database_service import db_service

# Initialize FastAPI app
app = FastAPI(
    title="Legacy Interview API",
    description="AI-powered interview system for preserving family legacies",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
planner_agent = PlannerAgent()
prober_agent = ProberAgent()
summarizer_agent = SummarizerAgent()
subject_simulator = SubjectSimulatorAgent()  # For testing only

# In-memory storage (replace with database in production)
projects = {}
interviews = {}
responses = {}

# Sample data initialization function (defined here, called later after classes are defined)
def initialize_sample_data():
    """Initialize sample project data for development testing"""
    sample_project_id = "4bc45289-0948-4c14-8be9-f4b91ce50428"
    
    # Check if project exists in database or memory
    existing_project = db_service.load_project(sample_project_id)
    if existing_project:
        projects[sample_project_id] = Project(**existing_project)
        print(f"📂 Loaded existing sample project: {sample_project_id}")
        return
    
    # Create new sample project
    sample_project = Project(
        id=sample_project_id,
        name="Grandma Rose's Story",
        subject_info={
            "name": "Rose Martinez",
            "age": 82,
            "relation": "grandmother",
            "background": "Born in Mexico, immigrated to California in the 1960s. Raised 5 children while working as a seamstress.",
            "language": "English"
        },
        interview_mode="family",
        language="en",
        status="created",
        created_at=datetime.now(),
        themes=[],
        responses=[]
    )
    
    # Save to database and memory
    projects[sample_project_id] = sample_project
    db_service.save_project(sample_project.model_dump())
    print(f"✅ Initialized sample project: {sample_project_id}")

# Pydantic models
class ProjectCreate(BaseModel):
    name: str
    subject_name: str
    subject_age: Optional[int] = None
    relation: str
    background: Optional[str] = ""
    interview_mode: str  # "self", "family", "hybrid"
    language: str = "en"

class Participant(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    role: str = "interviewer"  # "admin", "interviewer", "viewer"
    assigned_themes: List[str] = []  # theme IDs assigned by admin
    self_assigned_themes: List[str] = []  # theme IDs self-assigned by participant

class EnhancedTheme(BaseModel):
    id: str
    name: str
    description: str
    questions: List[str] = []  # 10-15 questions per theme
    suggested_interviewer: str = "family member"
    assigned_to: Optional[str] = None  # participant ID assigned by admin
    self_assigned_by: List[str] = []  # participant IDs who self-assigned
    custom: bool = False  # True if manually added, False if AI-generated
    status: str = "pending"  # "pending", "in_progress", "completed"

class Project(BaseModel):
    id: str
    name: str
    subject_info: Dict[str, Any]
    interview_mode: str
    language: str
    status: str  # "created", "seed_questions", "themes_identified", "deep_dive", "completed"
    created_at: datetime
    themes: List[Dict[str, Any]] = []  # Legacy format - will migrate to enhanced_themes
    enhanced_themes: List[EnhancedTheme] = []  # New enhanced theme format
    participants: List[Participant] = []  # Project participants
    admin_id: Optional[str] = None  # ID of project administrator
    responses: List[Dict[str, str]] = []  # Store interview responses
    seed_questions: List[str] = []  # Cache generated seed questions

class ResponseSubmit(BaseModel):
    project_id: str
    question: str
    answer: str
    question_type: str = "seed"  # "seed", "followup", "theme"
    theme_id: Optional[str] = None

class InterviewResponse(BaseModel):
    id: str
    project_id: str
    question: str
    answer: str
    question_type: str
    theme_id: Optional[str]
    timestamp: datetime
    followup_questions: List[str] = []

class SimulatorRequest(BaseModel):
    project_id: str
    question: str
    context: Optional[Dict[str, Any]] = {}

class ConversationSessionRequest(BaseModel):
    project_id: str
    session_name: str
    participants: Optional[List[Dict[str, str]]] = None

class AudioChunkRequest(BaseModel):
    session_id: str
    audio_data: str  # Base64 encoded audio data
    sample_rate: int = 16000

class TranscriptionRequest(BaseModel):
    session_id: str
    utterance_id: str
    transcription_service: str = "openai"

# Initialize sample data after all classes are defined
initialize_sample_data()

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Legacy Interview API", "status": "running"}

@app.get("/api/projects/list")
async def list_projects():
    """List all projects"""
    try:
        all_projects = db_service.list_projects()
        projects_list = []
        
        for project_id, project_data in all_projects.items():
            # Get response count for this project
            project_responses = responses.get(project_id, [])
            
            # Add response count to project data
            project_info = {
                **project_data,
                "responses": project_responses
            }
            projects_list.append(project_info)
        
        # Sort by created_at (newest first)
        projects_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {"projects": projects_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@app.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate):
    """Create a new interview project"""
    project_id = str(uuid.uuid4())
    
    project = Project(
        id=project_id,
        name=project_data.name,
        subject_info={
            "name": project_data.subject_name,
            "age": project_data.subject_age,
            "relation": project_data.relation,
            "background": project_data.background
        },
        interview_mode=project_data.interview_mode,
        language=project_data.language,
        status="created",
        created_at=datetime.now()
    )
    
    projects[project_id] = project
    responses[project_id] = []
    
    # Save to database
    db_service.save_project(project.model_dump())
    
    return project

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects:
        # Try to load from database
        project_data = db_service.load_project(project_id)
        if project_data:
            projects[project_id] = Project(**project_data)
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    return projects[project_id]

@app.get("/projects/{project_id}/seed-questions")
async def get_seed_questions(project_id: str):
    """Get or generate seed questions for a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    
    # Check if questions are already cached for this project
    if hasattr(project, 'seed_questions') and project.seed_questions:
        questions = project.seed_questions
        print(f"Using cached {len(questions)} questions for project {project_id}")
    else:
        # Generate seed questions using Planner Agent (only first time)
        questions = planner_agent.generate_seed_questions(project.subject_info, project_id)
        
        # Cache the questions in the project
        project.seed_questions = questions
        
        # Debug logging
        print(f"Generated and cached {len(questions)} questions for project {project_id}")
        if questions:
            print(f"First question: {questions[0]}")
        else:
            print("No questions generated!")
    
    # Update project status
    projects[project_id].status = "seed_questions"
    
    # Save to database
    db_service.save_project(projects[project_id].model_dump())
    
    return {"questions": questions, "total": len(questions)}

@app.post("/projects/{project_id}/seed-questions/regenerate")
async def regenerate_seed_questions(project_id: str):
    """Force regeneration of seed questions for a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    
    # Clear cached questions and regenerate
    project.seed_questions = []
    questions = planner_agent.generate_seed_questions(project.subject_info, project_id)
    project.seed_questions = questions
    
    print(f"Regenerated {len(questions)} questions for project {project_id}")
    
    return {"questions": questions, "total": len(questions), "regenerated": True}

# Participant Management Endpoints
@app.post("/projects/{project_id}/participants")
async def add_participant(project_id: str, participant_data: dict):
    """Add a participant to the project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    participant = Participant(
        id=str(uuid.uuid4()),
        name=participant_data["name"],
        email=participant_data.get("email"),
        role=participant_data.get("role", "interviewer")
    )
    
    projects[project_id].participants.append(participant)
    return {"participant": participant, "message": "Participant added successfully"}

@app.get("/projects/{project_id}/participants")
async def get_participants(project_id: str):
    """Get all participants for a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"participants": projects[project_id].participants}

@app.put("/projects/{project_id}/participants/{participant_id}/assign-theme")
async def assign_theme_to_participant(project_id: str, participant_id: str, assignment_data: dict):
    """Admin assigns a theme to a participant"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    theme_id = assignment_data["theme_id"]
    
    # Find participant
    participant = next((p for p in project.participants if p.id == participant_id), None)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Add theme to participant's assigned themes
    if theme_id not in participant.assigned_themes:
        participant.assigned_themes.append(theme_id)
    
    # Update theme assignment in enhanced_themes if it exists
    for theme in project.enhanced_themes:
        if theme.id == theme_id:
            theme.assigned_to = participant_id
            break
    
    return {"message": "Theme assigned successfully"}

@app.put("/projects/{project_id}/participants/{participant_id}/self-assign-theme")
async def self_assign_theme(project_id: str, participant_id: str, assignment_data: dict):
    """Participant self-assigns to a theme"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    theme_id = assignment_data["theme_id"]
    
    # Find participant
    participant = next((p for p in project.participants if p.id == participant_id), None)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Add theme to participant's self-assigned themes
    if theme_id not in participant.self_assigned_themes:
        participant.self_assigned_themes.append(theme_id)
    
    # Update theme self-assignment in enhanced_themes if it exists
    for theme in project.enhanced_themes:
        if theme.id == theme_id:
            if participant_id not in theme.self_assigned_by:
                theme.self_assigned_by.append(participant_id)
            break
    
    return {"message": "Self-assigned to theme successfully"}

@app.post("/projects/{project_id}/themes/custom")
async def add_custom_theme(project_id: str, theme_data: dict):
    """Add a custom theme to the project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create enhanced theme
    enhanced_theme = EnhancedTheme(
        id=str(uuid.uuid4()),
        name=theme_data["name"],
        description=theme_data.get("description", ""),
        questions=theme_data.get("questions", []),
        suggested_interviewer=theme_data.get("suggested_interviewer", "family member"),
        custom=True,  # User-created
        status="pending"
    )
    
    # Add to project
    projects[project_id].enhanced_themes.append(enhanced_theme)
    
    # Also add to legacy format for backward compatibility
    legacy_theme = {
        "id": enhanced_theme.id,
        "name": enhanced_theme.name,
        "description": enhanced_theme.description,
        "questions": enhanced_theme.questions,
        "suggested_interviewer": enhanced_theme.suggested_interviewer
    }
    projects[project_id].themes.append(legacy_theme)
    
    return {"theme": enhanced_theme, "message": "Custom theme added successfully"}

@app.get("/projects/{project_id}/themes/{theme_id}/preview")
async def preview_theme_questions(project_id: str, theme_id: str):
    """Preview questions for a theme before starting interview"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    
    # Look in enhanced themes first
    theme = next((t for t in project.enhanced_themes if t.id == theme_id), None)
    
    if not theme:
        # Fallback to legacy themes
        legacy_theme = next((t for t in project.themes if t["id"] == theme_id), None)
        if not legacy_theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        return {
            "theme_id": theme_id,
            "name": legacy_theme["name"],
            "description": legacy_theme["description"],
            "questions": legacy_theme["questions"],
            "total_questions": len(legacy_theme["questions"]),
            "suggested_interviewer": legacy_theme["suggested_interviewer"],
            "assignment_info": "No assignment info available (legacy theme)"
        }
    
    # Get assignment information
    assigned_participants = []
    self_assigned_participants = []
    
    for participant in project.participants:
        if theme_id in participant.assigned_themes:
            assigned_participants.append({"id": participant.id, "name": participant.name})
        if theme_id in participant.self_assigned_themes:
            self_assigned_participants.append({"id": participant.id, "name": participant.name})
    
    return {
        "theme_id": theme_id,
        "name": theme.name,
        "description": theme.description,
        "questions": theme.questions,
        "total_questions": len(theme.questions),
        "suggested_interviewer": theme.suggested_interviewer,
        "custom": theme.custom,
        "status": theme.status,
        "assigned_participants": assigned_participants,
        "self_assigned_participants": self_assigned_participants
    }

@app.post("/responses", response_model=InterviewResponse)
async def submit_response(response_data: ResponseSubmit):
    """Submit an interview response"""
    if response_data.project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    response_id = str(uuid.uuid4())
    
    # Create response record
    interview_response = InterviewResponse(
        id=response_id,
        project_id=response_data.project_id,
        question=response_data.question,
        answer=response_data.answer,
        question_type=response_data.question_type,
        theme_id=response_data.theme_id,
        timestamp=datetime.now()
    )
    
    # Generate follow-up questions using Prober Agent
    if response_data.answer.strip():  # Only if there's a meaningful answer
        followup_questions = prober_agent.generate_followup_questions(
            response_data.question,
            response_data.answer,
            {"theme": response_data.theme_id or "General"}
        )
        interview_response.followup_questions = followup_questions
    
    # Store response
    responses[response_data.project_id].append(interview_response)
    
    return interview_response

@app.get("/projects/{project_id}/responses")
async def get_project_responses(project_id: str):
    """Get all responses for a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_responses = responses.get(project_id, [])
    return {"responses": project_responses, "total": len(project_responses)}

@app.post("/projects/{project_id}/identify-themes")
async def identify_themes(project_id: str):
    """Analyze responses and identify themes for deep-dive interviews"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_responses = responses.get(project_id, [])
    if not project_responses:
        raise HTTPException(status_code=400, detail="No responses to analyze")
    
    # Convert responses to format expected by planner agent
    response_data = [
        {"question": r.question, "answer": r.answer}
        for r in project_responses
        if r.question_type == "seed"  # Only analyze seed questions
    ]
    
    # Identify themes using Planner Agent
    themes = planner_agent.identify_themes(response_data, project_id)
    
    # Create enhanced themes with new format
    enhanced_themes = []
    for theme in themes:
        enhanced_theme = EnhancedTheme(
            id=str(uuid.uuid4()),
            name=theme.get("name", "Untitled Theme"),
            description=theme.get("description", ""),
            questions=theme.get("questions", []),
            suggested_interviewer=theme.get("suggested_interviewer", "family member"),
            custom=False,  # AI-generated
            status="pending"
        )
        enhanced_themes.append(enhanced_theme)
    
    # Update project with both legacy and enhanced themes for backward compatibility
    legacy_themes = []
    for theme in enhanced_themes:
        legacy_themes.append({
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "questions": theme.questions,
            "suggested_interviewer": theme.suggested_interviewer
        })
    
    projects[project_id].themes = legacy_themes  # Keep for backward compatibility
    projects[project_id].enhanced_themes = enhanced_themes  # New enhanced format
    projects[project_id].status = "themes_identified"
    
    # Save to database
    db_service.save_project(projects[project_id].model_dump())
    
    return {"themes": legacy_themes, "enhanced_themes": enhanced_themes}

@app.get("/projects/{project_id}/themes/{theme_id}/questions")
async def get_theme_questions(project_id: str, theme_id: str):
    """Get deep-dive questions for a specific theme"""
    print(f"🎯 Getting theme questions for project_id: {project_id}, theme_id: {theme_id}")
    
    if project_id not in projects:
        print(f"❌ Project {project_id} not found in projects")
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    print(f"📋 Project has {len(project.themes)} themes")
    
    # Debug: Print all theme IDs
    for i, t in enumerate(project.themes):
        print(f"  Theme {i}: id={t.get('id', 'NO_ID')}, name={t.get('name', 'NO_NAME')}")
    
    theme = next((t for t in project.themes if t.get("id") == theme_id), None)
    
    if not theme:
        print(f"❌ Theme {theme_id} not found in project themes")
        raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
    
    print(f"✅ Found theme: {theme['name']}")
    return {
        "theme": theme["name"],
        "description": theme["description"],
        "questions": theme["questions"],
        "suggested_interviewer": theme["suggested_interviewer"]
    }

@app.post("/projects/{project_id}/summarize")
async def create_summary(project_id: str, output_type: str = "timeline"):
    """Generate summary/export for completed interviews"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_responses = responses.get(project_id, [])
    if not project_responses:
        raise HTTPException(status_code=400, detail="No responses to summarize")
    
    # Convert responses to format expected by summarizer
    response_data = [
        {"question": r.question, "answer": r.answer, "theme": r.theme_id}
        for r in project_responses
    ]
    
    if output_type == "timeline":
        summary = summarizer_agent.create_timeline_narrative(response_data)
        return {"type": "timeline", "content": summary}
    
    elif output_type == "quotes":
        quotes = summarizer_agent.extract_memorable_quotes(response_data)
        return {"type": "quotes", "content": quotes}
    
    elif output_type == "podcast":
        script = summarizer_agent.create_podcast_script(response_data)
        return {"type": "podcast", "content": script}
    
    elif output_type == "webpage":
        web_content = summarizer_agent.create_web_page_content(response_data)
        return {"type": "webpage", "content": web_content}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid output type")

@app.get("/projects/{project_id}/export/{export_type}")
async def export_project(project_id: str, export_type: str):
    """Export project data in various formats"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    project_responses = responses.get(project_id, [])
    
    export_data = {
        "project": project.dict(),
        "responses": [r.dict() for r in project_responses],
        "export_timestamp": datetime.now().isoformat(),
        "export_type": export_type
    }
    
    return export_data

# Testing endpoints - Subject Simulator
@app.post("/simulator/generate-response")
async def generate_simulator_response(request: SimulatorRequest):
    """Generate an authentic response from the subject simulator (for testing)"""
    if request.project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[request.project_id]
    
    # Set up the character profile for the simulator
    subject_simulator.set_character_profile(project.subject_info)
    
    # Generate authentic response using Agno's session management
    response = subject_simulator.generate_authentic_response(
        request.question, 
        request.context,
        project_id=request.project_id
    )
    
    # Get conversation count from Agno's session management
    try:
        messages = subject_simulator.agent.get_messages_for_session()
        conversation_count = len(messages) // 2  # Divide by 2 since each exchange has user + assistant message
    except Exception as e:
        print(f"⚠️ Could not get message count: {e}")
        conversation_count = 0
    
    return {
        "generated_answer": response,
        "character_profile": subject_simulator.established_facts,
        "conversation_count": conversation_count
    }

@app.get("/simulator/conversation-summary/{project_id}")
async def get_simulator_conversation_summary(project_id: str):
    """Get conversation summary from the simulator using Agno sessions"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return subject_simulator.get_conversation_summary(project_id=project_id)

@app.post("/simulator/reset/{project_id}")
async def reset_simulator_conversation(project_id: str):
    """Reset the simulator's conversation history using Agno sessions"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    subject_simulator.reset_conversation(project_id=project_id)
    return {"message": f"Simulator conversation reset for project {project_id}"}

# Conversation Recording Endpoints

@app.post("/conversation/start")
async def start_conversation_recording(request: ConversationSessionRequest):
    """Start a new conversation recording session with speaker separation"""
    try:
        session_id = await conversation_recording_service.start_recording_session(
            project_id=request.project_id,
            session_name=request.session_name,
            participants=request.participants
        )
        
        return {
            "session_id": session_id,
            "status": "started",
            "message": "Conversation recording session started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

@app.post("/conversation/audio-chunk")
async def process_audio_chunk(request: AudioChunkRequest):
    """Process audio chunk and extract speaker-separated utterances"""
    try:
        import base64
        
        # Decode base64 audio data
        audio_data = base64.b64decode(request.audio_data)
        
        result = await conversation_recording_service.process_audio_chunk(
            session_id=request.session_id,
            audio_data=audio_data,
            sample_rate=request.sample_rate
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

@app.post("/conversation/transcribe")
async def transcribe_utterance(request: TranscriptionRequest):
    """Transcribe a specific utterance with speaker identification"""
    try:
        result = await conversation_recording_service.transcribe_utterance(
            session_id=request.session_id,
            utterance_id=request.utterance_id,
            transcription_service=request.transcription_service
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transcribe: {str(e)}")

@app.post("/conversation/end/{session_id}")
async def end_conversation_recording(session_id: str):
    """End conversation recording session and save all data"""
    try:
        result = await conversation_recording_service.end_recording_session(session_id)
        
        return {
            "session_id": session_id,
            "status": "completed",
            "audio_file_path": result.get('audio_file_path'),
            "transcription_file_path": result.get('transcription_file_path'),
            "utterance_count": len(result.get('utterances', [])),
            "message": "Conversation recording session ended and saved"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end recording: {str(e)}")

@app.get("/conversation/sessions/{project_id}")
async def get_conversation_sessions(project_id: str):
    """Get all conversation sessions for a project"""
    try:
        # This would query the database for conversation sessions
        # For now, return mock data
        return {
            "project_id": project_id,
            "sessions": [
                {
                    "id": "session_1",
                    "session_name": "Initial Interview",
                    "status": "completed",
                    "started_at": "2024-01-01T10:00:00Z",
                    "ended_at": "2024-01-01T11:00:00Z",
                    "utterance_count": 45,
                    "participants": ["Interviewer", "Subject"]
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@app.get("/conversation/session/{session_id}/transcript")
async def get_conversation_transcript(session_id: str):
    """Get full conversation transcript with speaker separation"""
    try:
        # This would load the transcription from the database
        # For now, return mock data
        return {
            "session_id": session_id,
            "transcript": [
                {
                    "speaker": "Interviewer",
                    "text": "Hello, thank you for agreeing to this interview.",
                    "timestamp": "00:00:00",
                    "confidence": "0.95"
                },
                {
                    "speaker": "Subject",
                    "text": "You're welcome, I'm happy to share my story.",
                    "timestamp": "00:00:05",
                    "confidence": "0.92"
                }
            ],
            "participants": ["Interviewer", "Subject"],
            "duration": "01:00:00"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
