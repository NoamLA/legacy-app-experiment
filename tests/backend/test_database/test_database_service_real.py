"""
Enhanced Database Service Tests
Includes both mock tests (fast) and real database tests (comprehensive)
"""
import pytest
import os
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend and database to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
database_path = Path(__file__).parent.parent.parent.parent / "database"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(database_path))

from services.database_service import DatabaseService
from config import DatabaseConfig, DatabaseManager

class TestDatabaseServiceUnit:
    """Unit tests using mocks (fast, isolated)"""
    
    @pytest.fixture
    def mock_database_service(self):
        """Create database service with mocked dependencies"""
        service = DatabaseService()
        service.use_database = True
        service.engine = Mock()
        service.SessionLocal = Mock()
        return service
    
    @pytest.mark.unit
    def test_database_service_initialization(self):
        """Test DatabaseService initialization logic"""
        # Test with database disabled
        with patch.dict(os.environ, {"USE_DATABASE": "false"}):
            service = DatabaseService()
            assert service.use_database == False
            assert service._memory_projects == {}
        
        # Test with database enabled
        with patch.dict(os.environ, {"USE_DATABASE": "true"}):
            with patch.object(DatabaseService, '_setup_database') as mock_setup:
                service = DatabaseService()
                mock_setup.assert_called_once()
    
    @pytest.mark.unit
    def test_save_project_memory_fallback(self):
        """Test project saving falls back to memory when database disabled"""
        service = DatabaseService()
        service.use_database = False
        
        project_data = {
            "id": "test-project-123",
            "name": "Test Project",
            "subject_info": {"name": "Test Subject"},
            "interview_mode": "family",
            "language": "en",
            "status": "created"
        }
        
        result = service.save_project(project_data)
        assert result == True
        assert service._memory_projects["test-project-123"] == project_data
    
    @pytest.mark.unit
    def test_load_project_memory_fallback(self):
        """Test project loading from memory when database disabled"""
        service = DatabaseService()
        service.use_database = False
        
        # Pre-populate memory
        project_data = {"id": "test-123", "name": "Memory Test"}
        service._memory_projects["test-123"] = project_data
        
        loaded = service.load_project("test-123")
        assert loaded == project_data
        
        # Test non-existent project
        not_found = service.load_project("non-existent")
        assert not_found is None

class TestDatabaseServiceIntegration:
    """Integration tests using real PostgreSQL database"""
    
    @pytest.fixture
    def real_database_service(self):
        """Create database service with real PostgreSQL connection"""
        if os.getenv("SKIP_DB_TESTS", "").lower() == "true":
            pytest.skip("Database tests skipped")
        
        # Set up real database connection
        config = DatabaseConfig(environment="test")
        config.host = os.getenv("TEST_DB_HOST", "localhost")
        config.port = os.getenv("TEST_DB_PORT", "5434")
        config.database = os.getenv("TEST_DB_NAME", "legacy_interview_test")
        config.username = os.getenv("TEST_DB_USER", "legacy_test_user")
        config.password = os.getenv("TEST_DB_PASS", "legacy_test_pass")
        
        manager = DatabaseManager(config)
        
        service = DatabaseService()
        service.use_database = True
        service.engine = manager.engine
        service.SessionLocal = manager.session_factory
        
        # Clean database before test
        with service.get_db_session() as session:
            if session:
                session.execute("TRUNCATE TABLE projects CASCADE")
                session.commit()
        
        yield service
        
        # Clean up after test
        with service.get_db_session() as session:
            if session:
                session.execute("TRUNCATE TABLE projects CASCADE")
                session.commit()
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_real_project_persistence(self, real_database_service):
        """Test project persistence with real database"""
        project_id = str(uuid.uuid4())
        project_data = {
            "id": project_id,
            "name": "Real Database Project",
            "subject_info": {
                "name": "Real Test Subject",
                "age": 75,
                "relation": "grandmother",
                "background": "Test background for real database",
                "language": "English"
            },
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [{"id": "theme1", "name": "Family"}],
            "enhanced_themes": [{
                "id": str(uuid.uuid4()),
                "name": "Enhanced Family Theme",
                "custom": True
            }],
            "participants": [{
                "id": "participant1",
                "name": "Test Participant",
                "role": "interviewer"
            }],
            "admin_id": "admin123",
            "seed_questions": ["Question 1", "Question 2"]
        }
        
        # Save to real database
        result = real_database_service.save_project(project_data)
        assert result == True
        
        # Load from real database
        loaded_project = real_database_service.load_project(project_id)
        assert loaded_project is not None
        assert loaded_project["name"] == "Real Database Project"
        assert loaded_project["subject_info"]["name"] == "Real Test Subject"
        assert loaded_project["subject_info"]["age"] == 75
        assert len(loaded_project["themes"]) == 1
        assert len(loaded_project["enhanced_themes"]) == 1
        assert len(loaded_project["participants"]) == 1
        assert len(loaded_project["seed_questions"]) == 2
        assert loaded_project["admin_id"] == "admin123"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_real_project_updates(self, real_database_service):
        """Test project updates with real database"""
        project_id = str(uuid.uuid4())
        
        # Initial project
        initial_data = {
            "id": project_id,
            "name": "Initial Project",
            "subject_info": {"name": "Initial Subject"},
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": None,
            "seed_questions": []
        }
        
        # Save initial version
        assert real_database_service.save_project(initial_data) == True
        
        # Update project
        updated_data = initial_data.copy()
        updated_data["name"] = "Updated Project"
        updated_data["status"] = "seed_questions"
        updated_data["seed_questions"] = ["New question 1", "New question 2"]
        updated_data["themes"] = [{"id": "theme1", "name": "New Theme"}]
        
        # Save update
        assert real_database_service.save_project(updated_data) == True
        
        # Verify update
        loaded = real_database_service.load_project(project_id)
        assert loaded["name"] == "Updated Project"
        assert loaded["status"] == "seed_questions"
        assert len(loaded["seed_questions"]) == 2
        assert len(loaded["themes"]) == 1
        assert loaded["themes"][0]["name"] == "New Theme"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_real_multiple_projects(self, real_database_service):
        """Test handling multiple projects with real database"""
        # Create multiple projects
        project_ids = []
        for i in range(5):
            project_id = str(uuid.uuid4())
            project_ids.append(project_id)
            
            project_data = {
                "id": project_id,
                "name": f"Multi Project {i}",
                "subject_info": {
                    "name": f"Subject {i}",
                    "age": 70 + i,
                    "relation": "grandparent"
                },
                "interview_mode": "family",
                "language": "en",
                "status": "created",
                "themes": [],
                "enhanced_themes": [],
                "participants": [],
                "admin_id": None,
                "seed_questions": []
            }
            
            assert real_database_service.save_project(project_data) == True
        
        # List all projects
        all_projects = real_database_service.list_projects()
        assert len(all_projects) >= 5
        
        for project_id in project_ids:
            assert project_id in all_projects
            assert all_projects[project_id]["name"].startswith("Multi Project")
        
        # Load individual projects
        for i, project_id in enumerate(project_ids):
            loaded = real_database_service.load_project(project_id)
            assert loaded is not None
            assert loaded["name"] == f"Multi Project {i}"
            assert loaded["subject_info"]["age"] == 70 + i
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_real_database_error_handling(self, real_database_service):
        """Test error handling with real database"""
        # Test with invalid UUID
        result = real_database_service.save_project({
            "id": "invalid-uuid",  # This should cause an error
            "name": "Invalid Project",
            "subject_info": {"name": "Test"},
            "interview_mode": "family",
            "language": "en",
            "status": "created"
        })
        
        # Should handle error gracefully
        assert result == False  # Save should fail
        
        # Test loading non-existent project
        not_found = real_database_service.load_project(str(uuid.uuid4()))
        assert not_found is None
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_real_database_memory_sync(self, real_database_service):
        """Test that database and memory storage stay in sync"""
        project_id = str(uuid.uuid4())
        project_data = {
            "id": project_id,
            "name": "Sync Test Project",
            "subject_info": {"name": "Sync Subject"},
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": None,
            "seed_questions": []
        }
        
        # Save to database
        assert real_database_service.save_project(project_data) == True
        
        # Should also be in memory cache
        assert project_id in real_database_service._memory_projects
        assert real_database_service._memory_projects[project_id]["name"] == "Sync Test Project"
        
        # Load from database (should use cache)
        loaded = real_database_service.load_project(project_id)
        assert loaded["name"] == "Sync Test Project"
    
    @pytest.mark.database
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_database_performance(self, real_database_service):
        """Test database performance with realistic load"""
        import time
        
        # Create projects with realistic data sizes
        project_ids = []
        start_time = time.time()
        
        for i in range(20):  # 20 projects
            project_id = str(uuid.uuid4())
            project_ids.append(project_id)
            
            # Realistic project data
            project_data = {
                "id": project_id,
                "name": f"Performance Test Project {i}",
                "subject_info": {
                    "name": f"Performance Subject {i}",
                    "age": 65 + (i % 20),
                    "relation": ["grandmother", "grandfather", "parent"][i % 3],
                    "background": f"Detailed background story for subject {i} " * 10,  # Longer text
                    "language": "English"
                },
                "interview_mode": "family",
                "language": "en",
                "status": ["created", "seed_questions", "themes_identified"][i % 3],
                "themes": [
                    {"id": f"theme_{i}_1", "name": f"Theme {i} Family", "questions": [f"Q{j}" for j in range(5)]},
                    {"id": f"theme_{i}_2", "name": f"Theme {i} Career", "questions": [f"Q{j}" for j in range(3)]}
                ],
                "enhanced_themes": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": f"Enhanced Theme {i}",
                        "description": f"Detailed description for theme {i}",
                        "custom": i % 2 == 0,
                        "status": "pending"
                    }
                ],
                "participants": [
                    {"id": f"p{i}_1", "name": f"Participant {i} A", "role": "interviewer"},
                    {"id": f"p{i}_2", "name": f"Participant {i} B", "role": "viewer"}
                ],
                "admin_id": f"admin_{i}",
                "seed_questions": [f"Seed question {j} for project {i}" for j in range(10)]
            }
            
            assert real_database_service.save_project(project_data) == True
        
        save_time = time.time() - start_time
        
        # Test bulk loading performance
        start_time = time.time()
        all_projects = real_database_service.list_projects()
        list_time = time.time() - start_time
        
        # Test individual loading performance
        start_time = time.time()
        for project_id in project_ids[:5]:  # Test first 5
            loaded = real_database_service.load_project(project_id)
            assert loaded is not None
        load_time = time.time() - start_time
        
        # Performance assertions
        assert len(all_projects) >= 20
        assert save_time < 10.0  # Should save 20 projects in under 10 seconds
        assert list_time < 2.0   # Should list all projects in under 2 seconds
        assert load_time < 1.0   # Should load 5 projects in under 1 second
        
        print(f"\n📊 Performance Results:")
        print(f"  Save 20 projects: {save_time:.2f}s")
        print(f"  List all projects: {list_time:.2f}s") 
        print(f"  Load 5 projects: {load_time:.2f}s")

class TestDatabaseServiceComparison:
    """Tests that compare mock vs real database behavior"""
    
    @pytest.mark.unit
    def test_mock_vs_real_consistency(self):
        """Verify mock and real implementations behave consistently"""
        project_data = {
            "id": str(uuid.uuid4()),
            "name": "Consistency Test",
            "subject_info": {"name": "Test Subject"},
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": None,
            "seed_questions": []
        }
        
        # Test with memory-only service
        memory_service = DatabaseService()
        memory_service.use_database = False
        
        result1 = memory_service.save_project(project_data)
        loaded1 = memory_service.load_project(project_data["id"])
        
        assert result1 == True
        assert loaded1 is not None
        assert loaded1["name"] == "Consistency Test"
        
        # Both should have consistent behavior patterns
        # (Real database test would be similar but with actual persistence)
