"""
Database Service - Handles data persistence for Legacy Interview App
Provides a bridge between in-memory operations and PostgreSQL persistence
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from backend.database_models import Project as DBProject, Base

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Database service that handles persistence while maintaining compatibility
    with the current in-memory API
    """
    
    def __init__(self):
        self.use_database = os.getenv("USE_DATABASE", "false").lower() == "true"
        
        if self.use_database:
            self._setup_database()
        else:
            logger.info("🗄️ Using in-memory storage (set USE_DATABASE=true to enable PostgreSQL)")
            
        # In-memory fallback storage
        self._memory_projects = {}
        self._memory_responses = {}
    
    def _setup_database(self):
        """Setup PostgreSQL database connection"""
        try:
            # Use port 5433 as confirmed by user
            db_url = os.getenv(
                "DATABASE_URL", 
                "postgresql://legacy_user:legacy_pass@localhost:5433/legacy_interview_dev"
            )
            
            self.engine = create_engine(db_url, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ PostgreSQL database connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.info("🔄 Falling back to in-memory storage")
            self.use_database = False
    
    @contextmanager
    def get_db_session(self):
        """Get database session with automatic cleanup"""
        if not self.use_database:
            yield None
            return
            
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def save_project(self, project_data: Dict[str, Any]) -> bool:
        """Save project to database or memory"""
        project_id = project_data["id"]
        
        # Always update memory storage for compatibility
        self._memory_projects[project_id] = project_data
        
        if not self.use_database:
            return True
            
        try:
            with self.get_db_session() as session:
                if session is None:
                    return True
                    
                # Check if project exists
                existing = session.query(DBProject).filter_by(id=project_id).first()
                
                if existing:
                    # Update existing project
                    existing.name = project_data["name"]
                    existing.subject_info = project_data["subject_info"]
                    existing.interview_mode = project_data["interview_mode"]
                    existing.language = project_data["language"]
                    existing.status = project_data["status"]
                    existing.themes = project_data.get("themes", [])
                    existing.enhanced_themes = project_data.get("enhanced_themes", [])
                    existing.participants = project_data.get("participants", [])
                    existing.admin_id = project_data.get("admin_id")
                    existing.seed_questions = project_data.get("seed_questions", [])
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new project
                    db_project = DBProject(
                        id=project_id,
                        name=project_data["name"],
                        subject_info=project_data["subject_info"],
                        interview_mode=project_data["interview_mode"],
                        language=project_data["language"],
                        status=project_data["status"],
                        themes=project_data.get("themes", []),
                        enhanced_themes=project_data.get("enhanced_themes", []),
                        participants=project_data.get("participants", []),
                        admin_id=project_data.get("admin_id"),
                        seed_questions=project_data.get("seed_questions", []),
                        created_at=project_data.get("created_at", datetime.utcnow()),
                        updated_at=datetime.utcnow()
                    )
                    session.add(db_project)
                
                logger.info(f"💾 Saved project {project_id} to database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save project {project_id}: {e}")
            return False
    
    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load project from database or memory"""
        # Try memory first for compatibility
        if project_id in self._memory_projects:
            return self._memory_projects[project_id]
        
        if not self.use_database:
            return None
            
        try:
            with self.get_db_session() as session:
                if session is None:
                    return None
                    
                db_project = session.query(DBProject).filter_by(id=project_id).first()
                
                if not db_project:
                    return None
                
                # Convert database model to dictionary
                project_data = {
                    "id": str(db_project.id),  # Convert UUID to string
                    "name": db_project.name,
                    "subject_info": db_project.subject_info,
                    "interview_mode": db_project.interview_mode,
                    "language": db_project.language,
                    "status": db_project.status,
                    "themes": db_project.themes or [],
                    "enhanced_themes": db_project.enhanced_themes or [],
                    "participants": db_project.participants or [],
                    "admin_id": str(db_project.admin_id) if db_project.admin_id else None,  # Convert UUID to string
                    "seed_questions": db_project.seed_questions or [],
                    "created_at": db_project.created_at,
                    "responses": []  # Load separately if needed
                }
                
                # Cache in memory for performance
                self._memory_projects[project_id] = project_data
                
                logger.info(f"📂 Loaded project {project_id} from database")
                return project_data
                
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {e}")
            return None
    
    def list_projects(self) -> Dict[str, Dict[str, Any]]:
        """List all projects from database and memory"""
        all_projects = dict(self._memory_projects)
        
        if not self.use_database:
            return all_projects
            
        try:
            with self.get_db_session() as session:
                if session is None:
                    return all_projects
                    
                db_projects = session.query(DBProject).all()
                
                for db_project in db_projects:
                    project_id_str = str(db_project.id)  # Convert UUID to string
                    if project_id_str not in all_projects:
                        project_data = {
                            "id": project_id_str,  # Use string version
                            "name": db_project.name,
                            "subject_info": db_project.subject_info,
                            "interview_mode": db_project.interview_mode,
                            "language": db_project.language,
                            "status": db_project.status,
                            "themes": db_project.themes or [],
                            "enhanced_themes": db_project.enhanced_themes or [],
                            "participants": db_project.participants or [],
                            "admin_id": str(db_project.admin_id) if db_project.admin_id else None,  # Convert UUID to string
                            "seed_questions": db_project.seed_questions or [],
                            "created_at": db_project.created_at,
                            "responses": []
                        }
                        all_projects[project_id_str] = project_data
                        # Cache in memory
                        self._memory_projects[project_id_str] = project_data
                
                return all_projects
                
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return all_projects

# Global database service instance
db_service = DatabaseService()
