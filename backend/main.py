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
    if sample_project_id not in projects:
        projects[sample_project_id] = Project(
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

class Project(BaseModel):
    id: str
    name: str
    subject_info: Dict[str, Any]
    interview_mode: str
    language: str
    status: str  # "created", "seed_questions", "themes_identified", "deep_dive", "completed"
    created_at: datetime
    themes: List[Dict[str, Any]] = []
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

# Initialize sample data after all classes are defined
initialize_sample_data()

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Legacy Interview API", "status": "running"}

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
    
    return project

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project details"""
    if project_id not in projects:
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
    themes = planner_agent.identify_themes(response_data)
    
    # Add theme IDs
    for theme in themes:
        theme["id"] = str(uuid.uuid4())
    
    # Update project with themes
    projects[project_id].themes = themes
    projects[project_id].status = "themes_identified"
    
    return {"themes": themes}

@app.get("/projects/{project_id}/themes/{theme_id}/questions")
async def get_theme_questions(project_id: str, theme_id: str):
    """Get deep-dive questions for a specific theme"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    theme = next((t for t in project.themes if t["id"] == theme_id), None)
    
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
