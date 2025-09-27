"""
Tests for Memory and Session Management Functionality
"""
import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add backend and database to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
database_path = Path(__file__).parent.parent.parent.parent / "database"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(database_path))

from config import DatabaseConfig, DatabaseManager
from agents.subject_simulator_agent import SubjectSimulatorAgent

class TestMemoryFunctionality:
    """Test suite for memory and session management"""
    
    @pytest.fixture
    def test_project_id(self):
        """Generate a test project ID"""
        return str(uuid.uuid4())
    
    @pytest.fixture
    def mock_agent_with_memory(self):
        """Create a mock agent with memory capabilities"""
        mock_agent = Mock()
        mock_agent.get_messages_for_session.return_value = [
            Mock(role="user", content="Hello, my name is Rose"),
            Mock(role="assistant", content="Nice to meet you, Rose!"),
            Mock(role="user", content="I was born in Mexico"),
            Mock(role="assistant", content="Tell me more about Mexico")
        ]
        mock_agent.get_user_memories.return_value = [
            Mock(to_dict=lambda: {"memory": "User is named Rose", "created_at": "2024-01-01"})
        ]
        return mock_agent
    
    @pytest.mark.unit
    def test_subject_simulator_memory_setup(self, test_project_id):
        """Test that SubjectSimulatorAgent sets up memory correctly"""
        simulator = SubjectSimulatorAgent()
        
        # Test character profile setting
        subject_info = {
            "name": "Rose Martinez",
            "age": 82,
            "relation": "grandmother",
            "background": "Born in Mexico"
        }
        
        simulator.set_character_profile(subject_info)
        
        assert simulator.character_profile == subject_info
        assert simulator.established_facts["name"] == "Rose Martinez"
        assert simulator.established_facts["age"] == 82
        
    @pytest.mark.unit
    def test_memory_persistence_across_calls(self, test_project_id):
        """Test that memory persists across multiple agent calls"""
        simulator = SubjectSimulatorAgent()
        
        # Mock responses
        mock_response1 = Mock()
        mock_response1.content = "I remember growing up in Jalisco..."
        
        mock_response2 = Mock()
        mock_response2.content = "As I mentioned before, Jalisco was beautiful..."
        
        mock_agent.run.side_effect = [mock_response1, mock_response2]
        
        # First interaction
        response1 = simulator.generate_authentic_response(
            "Tell me about your childhood",
            project_id=test_project_id
        )
        
        # Second interaction
        response2 = simulator.generate_authentic_response(
            "What else do you remember?",
            project_id=test_project_id
        )
        
        # Verify session consistency
        assert mock_agent.run.call_count == 2
        
        # Both calls should use the same session_id
        call1_kwargs = mock_agent.run.call_args_list[0][1]
        call2_kwargs = mock_agent.run.call_args_list[1][1]
        
        assert call1_kwargs["session_id"] == f"interview_{test_project_id}"
        assert call2_kwargs["session_id"] == f"interview_{test_project_id}"
        assert call1_kwargs["user_id"] == "interview_subject"
        assert call2_kwargs["user_id"] == "interview_subject"
        
    @pytest.mark.unit
    def test_conversation_summary_retrieval(self, mock_agent_with_memory, test_project_id):
        """Test retrieving conversation summary from memory"""
        simulator = SubjectSimulatorAgent()
        simulator.agent = mock_agent_with_memory
        
        summary = simulator.get_conversation_summary(test_project_id)
        
        assert "conversation_messages" in summary
        assert "total_exchanges" in summary
        assert "memories" in summary
        
        # Should have 2 exchanges (4 messages / 2)
        assert summary["total_exchanges"] == 2
        
        # Should have conversation messages
        assert len(summary["conversation_messages"]) == 4
        assert summary["conversation_messages"][0]["role"] == "user"
        assert summary["conversation_messages"][0]["content"] == "Hello, my name is Rose"
        
    @pytest.mark.unit
    def test_session_isolation_between_projects(self):
        """Test that different projects have isolated sessions"""
        simulator = SubjectSimulatorAgent()
        
        project1_id = "project-123"
        project2_id = "project-456"
        
        with patch.object(simulator.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Test response"
            mock_run.return_value = mock_response
            
            # Generate responses for different projects
            simulator.generate_authentic_response("Question 1", project_id=project1_id)
            simulator.generate_authentic_response("Question 2", project_id=project2_id)
            
            # Verify different session IDs were used
            calls = mock_run.call_args_list
            assert calls[0][1]["session_id"] == "interview_project-123"
            assert calls[1][1]["session_id"] == "interview_project-456"
            
    @pytest.mark.unit
    def test_memory_error_handling(self, test_project_id):
        """Test graceful handling of memory system errors"""
        simulator = SubjectSimulatorAgent()
        
        # Mock agent that throws exceptions
        with patch.object(simulator.agent, 'get_messages_for_session') as mock_messages:
            mock_messages.side_effect = Exception("Database connection failed")
            
            # Should not raise exception, should return default structure
            summary = simulator.get_conversation_summary(test_project_id)
            
            assert summary["total_exchanges"] == 0
            assert summary["conversation_messages"] == []
            assert summary["memories"] == []
            assert "error" not in summary  # Error should be logged, not returned
            
    @pytest.mark.unit
    def test_character_consistency_across_responses(self, test_project_id):
        """Test that character profile influences response consistency"""
        simulator = SubjectSimulatorAgent()
        
        # Set character profile
        character_info = {
            "name": "Maria Santos",
            "age": 75,
            "relation": "grandmother",
            "background": "Grew up in rural Spain, moved to America in 1970s"
        }
        
        simulator.set_character_profile(character_info)
        
        with patch.object(simulator.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "In Spain, we had olive groves..."
            mock_run.return_value = mock_response
            
            response = simulator.generate_authentic_response(
                "Tell me about your childhood",
                project_id=test_project_id
            )
            
            # Verify character context was included in prompt
            prompt = mock_run.call_args[0][0]
            assert "Maria Santos" in prompt
            assert "Spain" in prompt
            assert "1970s" in prompt
            
    @pytest.mark.integration
    def test_database_session_management(self, test_db_config):
        """Integration test for database session management"""
        manager = DatabaseManager(test_db_config)
        
        # Test session creation and cleanup
        with manager.get_session() as session:
            assert session is not None
            assert session.is_active
            
            # Simulate some database operations
            result = session.execute("SELECT 1")
            assert result.scalar() == 1
            
        # Session should be properly closed
        assert not session.is_active
        
    @pytest.mark.integration
    def test_agno_database_integration(self, test_db_config):
        """Test integration with Agno's database system"""
        manager = DatabaseManager(test_db_config)
        agno_db = manager.agno_db
        
        # Test that Agno database is configured correctly
        assert agno_db is not None
        
        # Test table naming with environment prefixes
        expected_session_table = test_db_config.get_table_name("agent_sessions")
        # Note: We can't easily test the actual table names without mocking
        # because PostgresDb doesn't expose them publicly
        
    @pytest.mark.unit
    def test_memory_data_structures(self, test_project_id):
        """Test memory data structure consistency"""
        simulator = SubjectSimulatorAgent()
        
        # Test established facts structure
        simulator.established_facts = {
            "name": "Test Subject",
            "age": 80,
            "location": "California",
            "key_memories": ["childhood farm", "wedding day", "first child"]
        }
        
        # Test that facts are properly maintained
        assert simulator.established_facts["name"] == "Test Subject"
        assert isinstance(simulator.established_facts["key_memories"], list)
        
        # Test updating facts
        simulator.update_character_facts({"occupation": "teacher"})
        assert "occupation" in simulator.established_facts
        assert simulator.established_facts["occupation"] == "teacher"
        
    @pytest.mark.unit
    def test_conversation_reset_functionality(self, test_project_id):
        """Test conversation reset functionality"""
        simulator = SubjectSimulatorAgent()
        
        with patch.object(simulator.db, 'delete_session') as mock_delete:
            simulator.reset_conversation(test_project_id)
            
            # Should attempt to delete the session
            mock_delete.assert_called_once_with(
                session_id=f"interview_{test_project_id}",
                user_id="interview_subject"
            )
            
    @pytest.mark.unit
    def test_memory_context_building(self, test_project_id):
        """Test that memory context is properly built for AI prompts"""
        simulator = SubjectSimulatorAgent()
        
        # Set up character profile
        simulator.character_profile = {
            "name": "Elena Rodriguez",
            "age": 78,
            "background": "Immigrated from Cuba in 1962"
        }
        
        simulator.established_facts = {
            "name": "Elena Rodriguez",
            "age": 78,
            "birth_year": 1946,
            "generation": "Silent Generation",
            "background": "Immigrated from Cuba in 1962"
        }
        
        # Build character context
        context = simulator._build_character_context()
        
        assert "Elena Rodriguez" in context
        assert "78" in context
        assert "Cuba" in context
        assert "Silent Generation" in context
        
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_memory_flow(self, test_project_id):
        """End-to-end test of memory functionality"""
        # Skip if no OpenAI API key
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available for integration test")
            
        simulator = SubjectSimulatorAgent()
        
        # Set character profile
        character_info = {
            "name": "Integration Test Subject",
            "age": 70,
            "relation": "grandmother",
            "background": "Test background for integration"
        }
        
        simulator.set_character_profile(character_info)
        
        # Generate first response
        response1 = simulator.generate_authentic_response(
            "Tell me your name",
            project_id=test_project_id
        )
        
        # Generate second response (should reference first)
        response2 = simulator.generate_authentic_response(
            "What did you just tell me?",
            project_id=test_project_id
        )
        
        # Verify responses are strings
        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert len(response1) > 0
        assert len(response2) > 0
        
        # Get conversation summary
        summary = simulator.get_conversation_summary(test_project_id)
        
        # Verify summary structure
        assert "total_exchanges" in summary
        assert "conversation_messages" in summary
        assert summary["total_exchanges"] >= 2
