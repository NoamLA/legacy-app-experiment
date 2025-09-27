"""
Real Database Integration Tests
Tests that use actual PostgreSQL database for realistic scenarios
"""
import pytest
import os
import uuid
import json
from datetime import datetime
from sqlalchemy import text
import sys
from pathlib import Path

# Add backend and database to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
database_path = Path(__file__).parent.parent.parent.parent / "database"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(database_path))

from config import DatabaseConfig, DatabaseManager
from services.database_service import DatabaseService
from database_models import Project, InterviewResponse, InterviewTheme, Base
from agents.planner_agent import PlannerAgent
from agents.prober_agent import ProberAgent
from agents.subject_simulator_agent import SubjectSimulatorAgent

class TestRealDatabaseIntegration:
    """Integration tests using real PostgreSQL database"""
    
    @pytest.fixture(scope="class")
    def test_db_config(self):
        """Create test database configuration for real PostgreSQL"""
        # Use test database on port 5434 (from docker-compose.test.yml)
        return DatabaseConfig(environment="test")
    
    @pytest.fixture(scope="class")
    def test_db_manager(self, test_db_config):
        """Create database manager with real PostgreSQL connection"""
        # Override with test database settings
        test_db_config.host = os.getenv("TEST_DB_HOST", "localhost")
        test_db_config.port = os.getenv("TEST_DB_PORT", "5434")
        test_db_config.database = os.getenv("TEST_DB_NAME", "legacy_interview_test")
        test_db_config.username = os.getenv("TEST_DB_USER", "legacy_test_user")
        test_db_config.password = os.getenv("TEST_DB_PASS", "legacy_test_pass")
        
        return DatabaseManager(test_db_config)
    
    @pytest.fixture(scope="function")
    def clean_db_session(self, test_db_manager):
        """Provide a clean database session for each test"""
        # Create tables
        Base.metadata.create_all(bind=test_db_manager.engine)
        
        with test_db_manager.get_session() as session:
            # Clean all tables before test
            session.execute(text("TRUNCATE TABLE interview_responses CASCADE"))
            session.execute(text("TRUNCATE TABLE interview_themes CASCADE"))
            session.execute(text("TRUNCATE TABLE projects CASCADE"))
            session.execute(text("TRUNCATE TABLE knowledge_documents CASCADE"))
            session.execute(text("TRUNCATE TABLE agent_sessions CASCADE"))
            session.execute(text("TRUNCATE TABLE agent_messages CASCADE"))
            session.execute(text("TRUNCATE TABLE user_memories CASCADE"))
            session.commit()
            
            yield session
            
            # Clean up after test
            session.execute(text("TRUNCATE TABLE interview_responses CASCADE"))
            session.execute(text("TRUNCATE TABLE interview_themes CASCADE"))
            session.execute(text("TRUNCATE TABLE projects CASCADE"))
            session.execute(text("TRUNCATE TABLE knowledge_documents CASCADE"))
            session.execute(text("TRUNCATE TABLE agent_sessions CASCADE"))
            session.execute(text("TRUNCATE TABLE agent_messages CASCADE"))
            session.execute(text("TRUNCATE TABLE user_memories CASCADE"))
            session.commit()
    
    @pytest.fixture
    def database_service(self, test_db_manager):
        """Create database service with real database"""
        service = DatabaseService()
        # Override database settings for testing
        service.use_database = True
        service.engine = test_db_manager.engine
        service.SessionLocal = test_db_manager.session_factory
        return service
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing"""
        return {
            "id": str(uuid.uuid4()),
            "name": "Integration Test Project",
            "subject_info": {
                "name": "Maria Santos",
                "age": 78,
                "relation": "grandmother",
                "background": "Born in Spain, immigrated to US in 1970s",
                "language": "English"
            },
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": None,
            "seed_questions": [],
            "created_at": datetime.now()
        }
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_project_crud_operations(self, database_service, sample_project_data, clean_db_session):
        """Test full CRUD operations on projects with real database"""
        project_id = sample_project_data["id"]
        
        # CREATE: Save project
        result = database_service.save_project(sample_project_data)
        assert result == True
        
        # READ: Load project
        loaded_project = database_service.load_project(project_id)
        assert loaded_project is not None
        assert loaded_project["name"] == sample_project_data["name"]
        assert loaded_project["subject_info"]["name"] == "Maria Santos"
        assert loaded_project["subject_info"]["age"] == 78
        
        # UPDATE: Modify project
        sample_project_data["status"] = "seed_questions"
        sample_project_data["seed_questions"] = [
            "Tell me about your childhood in Spain",
            "What was it like immigrating to America?"
        ]
        
        result = database_service.save_project(sample_project_data)
        assert result == True
        
        # Verify update
        updated_project = database_service.load_project(project_id)
        assert updated_project["status"] == "seed_questions"
        assert len(updated_project["seed_questions"]) == 2
        
        # LIST: Get all projects
        all_projects = database_service.list_projects()
        assert project_id in all_projects
        assert len(all_projects) >= 1
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_interview_response_persistence(self, clean_db_session, sample_project_data):
        """Test saving and retrieving interview responses"""
        # First create a project
        project = Project(
            id=sample_project_data["id"],
            name=sample_project_data["name"],
            subject_info=sample_project_data["subject_info"],
            interview_mode=sample_project_data["interview_mode"],
            language=sample_project_data["language"],
            status=sample_project_data["status"]
        )
        clean_db_session.add(project)
        clean_db_session.commit()
        
        # Create interview response
        response = InterviewResponse(
            project_id=project.id,
            question="Tell me about your childhood in Spain",
            answer="I grew up in a small village near Barcelona. My father was a farmer and my mother took care of the house and children.",
            question_type="seed",
            followup_questions=[
                "What crops did your father grow?",
                "How many siblings did you have?"
            ],
            extra_metadata={"emotion_detected": "nostalgic", "key_themes": ["family", "rural_life"]}
        )
        
        clean_db_session.add(response)
        clean_db_session.commit()
        
        # Retrieve and verify
        saved_response = clean_db_session.query(InterviewResponse).filter_by(project_id=project.id).first()
        assert saved_response is not None
        assert saved_response.question == "Tell me about your childhood in Spain"
        assert "Barcelona" in saved_response.answer
        assert len(saved_response.followup_questions) == 2
        assert saved_response.extra_metadata["emotion_detected"] == "nostalgic"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_theme_identification_and_storage(self, clean_db_session, sample_project_data):
        """Test theme creation and relationship with responses"""
        # Create project
        project = Project(
            id=sample_project_data["id"],
            name=sample_project_data["name"],
            subject_info=sample_project_data["subject_info"],
            interview_mode=sample_project_data["interview_mode"],
            language=sample_project_data["language"],
            status="themes_identified"
        )
        clean_db_session.add(project)
        clean_db_session.commit()
        
        # Create theme
        theme = InterviewTheme(
            project_id=project.id,
            name="Immigration Journey",
            description="Stories about coming to America and adapting to new culture",
            questions=[
                "What was your first impression of America?",
                "What did you miss most about Spain?",
                "How did you learn English?"
            ],
            suggested_interviewer="family member",
            extra_metadata={"priority": "high", "estimated_duration": "45 minutes"}
        )
        clean_db_session.add(theme)
        clean_db_session.commit()
        
        # Create response linked to theme
        response = InterviewResponse(
            project_id=project.id,
            theme_id=theme.id,
            question="What was your first impression of America?",
            answer="Everything was so big and fast! The cities were much larger than anything in Spain.",
            question_type="theme"
        )
        clean_db_session.add(response)
        clean_db_session.commit()
        
        # Verify relationships
        saved_theme = clean_db_session.query(InterviewTheme).filter_by(project_id=project.id).first()
        assert saved_theme is not None
        assert saved_theme.name == "Immigration Journey"
        assert len(saved_theme.questions) == 3
        
        theme_responses = clean_db_session.query(InterviewResponse).filter_by(theme_id=theme.id).all()
        assert len(theme_responses) == 1
        assert theme_responses[0].question_type == "theme"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_database_connection_resilience(self, test_db_manager):
        """Test database connection handling and recovery"""
        # Test connection
        assert test_db_manager.test_connection() == True
        
        # Test session management
        with test_db_manager.get_session() as session:
            result = session.execute(text("SELECT 1 as test_value"))
            assert result.scalar() == 1
        
        # Test multiple concurrent sessions
        sessions = []
        try:
            for i in range(5):
                session = test_db_manager.session_factory()
                result = session.execute(text(f"SELECT {i} as value"))
                assert result.scalar() == i
                sessions.append(session)
        finally:
            for session in sessions:
                session.close()
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_agno_database_integration(self, test_db_manager):
        """Test integration with Agno's PostgresDb"""
        agno_db = test_db_manager.agno_db
        assert agno_db is not None
        
        # Test session creation (this should work with real database)
        test_session_id = f"test_session_{uuid.uuid4()}"
        test_user_id = "test_user"
        
        # Note: We can't easily test Agno's internal operations without
        # actually running agents, but we can verify the database connection works
        # The actual agent session testing is done in agent-specific tests
    
    @pytest.mark.database
    @pytest.mark.integration  
    def test_complex_project_workflow(self, database_service, clean_db_session):
        """Test complete project workflow with real database"""
        # 1. Create project
        project_data = {
            "id": str(uuid.uuid4()),
            "name": "Complete Workflow Test",
            "subject_info": {
                "name": "Carlos Rodriguez",
                "age": 82,
                "relation": "grandfather",
                "background": "Worked as mechanic for 40 years",
                "language": "English"
            },
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": "admin_123",
            "seed_questions": []
        }
        
        # Save initial project
        assert database_service.save_project(project_data) == True
        
        # 2. Add seed questions
        project_data["seed_questions"] = [
            "Tell me about your work as a mechanic",
            "What was your favorite car to work on?",
            "How did the automotive industry change during your career?"
        ]
        project_data["status"] = "seed_questions"
        assert database_service.save_project(project_data) == True
        
        # 3. Add participants
        project_data["participants"] = [
            {
                "id": "participant_1",
                "name": "Son Carlos Jr",
                "role": "interviewer",
                "assigned_themes": []
            },
            {
                "id": "participant_2", 
                "name": "Granddaughter Maria",
                "role": "interviewer",
                "assigned_themes": []
            }
        ]
        assert database_service.save_project(project_data) == True
        
        # 4. Add themes
        project_data["enhanced_themes"] = [
            {
                "id": str(uuid.uuid4()),
                "name": "Automotive Career",
                "description": "Stories about working as a mechanic",
                "questions": [
                    "What was your first job as a mechanic?",
                    "Tell me about the most challenging repair you ever did"
                ],
                "suggested_interviewer": "family member",
                "assigned_to": "participant_1",
                "custom": False,
                "status": "pending"
            }
        ]
        project_data["status"] = "themes_identified"
        assert database_service.save_project(project_data) == True
        
        # 5. Verify complete project
        final_project = database_service.load_project(project_data["id"])
        assert final_project is not None
        assert final_project["status"] == "themes_identified"
        assert len(final_project["seed_questions"]) == 3
        assert len(final_project["participants"]) == 2
        assert len(final_project["enhanced_themes"]) == 1
        assert final_project["admin_id"] == "admin_123"
        
        # 6. Test project listing
        all_projects = database_service.list_projects()
        assert project_data["id"] in all_projects
        assert all_projects[project_data["id"]]["name"] == "Complete Workflow Test"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_data_integrity_and_constraints(self, clean_db_session):
        """Test database constraints and data integrity"""
        # Test UUID constraints
        project = Project(
            id=str(uuid.uuid4()),
            name="Constraint Test Project",
            subject_info={"name": "Test Subject", "age": 75},
            interview_mode="family",
            language="en",
            status="created"
        )
        clean_db_session.add(project)
        clean_db_session.commit()
        
        # Test foreign key constraints
        response = InterviewResponse(
            project_id=project.id,  # Valid foreign key
            question="Test question",
            answer="Test answer",
            question_type="seed"
        )
        clean_db_session.add(response)
        clean_db_session.commit()
        
        # Verify cascade delete
        clean_db_session.delete(project)
        clean_db_session.commit()
        
        # Response should be deleted due to CASCADE
        remaining_responses = clean_db_session.query(InterviewResponse).filter_by(project_id=project.id).all()
        assert len(remaining_responses) == 0
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_json_field_operations(self, clean_db_session, sample_project_data):
        """Test JSONB field operations and queries"""
        project = Project(
            id=sample_project_data["id"],
            name=sample_project_data["name"],
            subject_info=sample_project_data["subject_info"],
            interview_mode=sample_project_data["interview_mode"],
            language=sample_project_data["language"],
            status=sample_project_data["status"],
            themes=[
                {"id": "theme1", "name": "Family", "questions": ["Q1", "Q2"]},
                {"id": "theme2", "name": "Career", "questions": ["Q3", "Q4", "Q5"]}
            ],
            enhanced_themes=[
                {
                    "id": str(uuid.uuid4()),
                    "name": "Enhanced Family Theme",
                    "custom": True,
                    "metadata": {"priority": "high", "duration": 30}
                }
            ]
        )
        clean_db_session.add(project)
        clean_db_session.commit()
        
        # Test JSON queries
        # Query by subject info
        projects_by_name = clean_db_session.query(Project).filter(
            Project.subject_info['name'].astext == 'Maria Santos'
        ).all()
        assert len(projects_by_name) == 1
        
        # Query by age using simpler approach (as done in real application)
        all_projects = clean_db_session.query(Project).all()
        projects_by_age = [p for p in all_projects if p.subject_info.get('age', 0) > 70]
        assert len(projects_by_age) == 1
        
        # Verify JSON data integrity
        saved_project = clean_db_session.query(Project).filter_by(id=project.id).first()
        assert len(saved_project.themes) == 2
        assert len(saved_project.enhanced_themes) == 1
        assert saved_project.subject_info["name"] == "Maria Santos"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_performance_with_large_dataset(self, clean_db_session):
        """Test database performance with larger dataset"""
        # Create multiple projects (let database generate UUIDs)
        projects = []
        for i in range(5):  # Reduced to 5 for faster testing
            project = Project(
                name=f"Performance Test Project {i}",
                subject_info={
                    "name": f"Test Subject {i}",
                    "age": 70 + i,
                    "relation": "grandparent",
                    "background": f"Background story {i}"
                },
                interview_mode="family",
                language="en",
                status="created"
            )
            clean_db_session.add(project)
            clean_db_session.flush()  # Get the ID immediately
            projects.append(project)
        
        clean_db_session.commit()
        
        # Create responses for each project
        for project in projects:
            for j in range(3):  # 3 responses per project
                response = InterviewResponse(
                    project_id=project.id,
                    question=f"Question {j} for {project.name}",
                    answer=f"Answer {j} with some detailed content about the subject's life and experiences.",
                    question_type="seed",
                    followup_questions=[f"Followup {j}.1", f"Followup {j}.2"]
                )
                clean_db_session.add(response)
        
        clean_db_session.commit()
        
        # Test query performance
        import time
        
        # Query all projects
        start_time = time.time()
        all_projects = clean_db_session.query(Project).all()
        query_time = time.time() - start_time
        
        assert len(all_projects) == 5
        assert query_time < 1.0  # Should be fast
        
        # Query with joins
        start_time = time.time()
        projects_with_responses = clean_db_session.query(Project).join(InterviewResponse).all()
        join_query_time = time.time() - start_time
        
        assert len(projects_with_responses) >= 5  # 5 projects with responses
        assert join_query_time < 2.0  # Should still be reasonable
        
        # Test pagination
        page_1 = clean_db_session.query(Project).limit(3).offset(0).all()
        page_2 = clean_db_session.query(Project).limit(3).offset(3).all()
        
        assert len(page_1) == 3
        assert len(page_2) == 2  # Remaining 2 projects
        assert page_1[0].id != page_2[0].id  # Different results
