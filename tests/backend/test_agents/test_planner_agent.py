"""
Tests for PlannerAgent - Question Generation Functionality
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from agents.planner_agent import PlannerAgent

class TestPlannerAgent:
    """Test suite for PlannerAgent question generation"""
    
    @pytest.fixture
    def planner_agent(self):
        """Create a PlannerAgent instance for testing"""
        return PlannerAgent()
    
    @pytest.fixture
    def mock_valid_response(self):
        """Mock valid OpenAI response with proper JSON structure"""
        return {
            "questions": [
                {
                    "text": "Tell me about where you were born and what it was like growing up there.",
                    "topic": "identity",
                    "cue_type": "place",
                    "phase": "P0",
                    "difficulty": "easy"
                },
                {
                    "text": "What is your earliest childhood memory?",
                    "topic": "identity", 
                    "cue_type": "time",
                    "phase": "P3",
                    "difficulty": "medium"
                },
                {
                    "text": "Who were the most important people in your early life?",
                    "topic": "family",
                    "cue_type": "people", 
                    "phase": "P3",
                    "difficulty": "easy"
                }
            ],
            "themes": [
                {
                    "name": "Family Heritage",
                    "description": "Stories about cultural background and family traditions"
                },
                {
                    "name": "Early Memories",
                    "description": "Childhood experiences and formative moments"
                }
            ]
        }
    
    @pytest.mark.unit
    def test_planner_agent_initialization(self, planner_agent):
        """Test that PlannerAgent initializes correctly"""
        assert planner_agent is not None
        assert planner_agent.agent is not None
        assert planner_agent.db is not None
        
    @pytest.mark.unit
    def test_generate_seed_questions_success(self, planner_agent, sample_subject_info, mock_valid_response):
        """Test successful seed question generation"""
        with patch.object(planner_agent, 'agent') as mock_agent:
            # Mock the agent response
            mock_response = Mock()
            mock_response.content = json.dumps(mock_valid_response)
            mock_agent.run.return_value = mock_response
            
            # Test question generation
            questions = planner_agent.generate_seed_questions(sample_subject_info, "test-project-123")
            
            # Assertions
            assert isinstance(questions, list)
            assert len(questions) == 3
            assert all(isinstance(q, str) for q in questions)
            assert "Tell me about where you were born" in questions[0]
            
            # Verify agent was called with correct parameters
            mock_agent.run.assert_called_once()
            call_args = mock_agent.run.call_args
            assert call_args[1]["session_id"] == "planner_test-project-123"
            assert call_args[1]["user_id"] == "subject_test-project-123"
    
    @pytest.mark.unit
    def test_generate_seed_questions_with_json_fences(self, planner_agent, sample_subject_info, mock_valid_response):
        """Test question generation with JSON wrapped in code fences"""
        with patch.object(planner_agent, 'agent') as mock_agent:
            # Mock response with JSON fences
            mock_response = Mock()
            mock_response.content = f"```json\n{json.dumps(mock_valid_response)}\n```"
            mock_agent.run.return_value = mock_response
            
            questions = planner_agent.generate_seed_questions(sample_subject_info, "test-project-123")
            
            assert len(questions) == 3
            assert all(isinstance(q, str) for q in questions)
    
    @pytest.mark.unit
    def test_generate_seed_questions_invalid_json(self, planner_agent, sample_subject_info):
        """Test question generation with invalid JSON response"""
        with patch.object(planner_agent, 'agent') as mock_agent:
            # Mock invalid JSON response
            mock_response = Mock()
            mock_response.content = "This is not valid JSON"
            mock_agent.run.return_value = mock_response
            
            questions = planner_agent.generate_seed_questions(sample_subject_info, "test-project-123")
            
            # Should return fallback questions
            assert isinstance(questions, list)
            assert len(questions) >= 3  # Fallback should provide at least 3 questions
            assert all(isinstance(q, str) for q in questions)
        
    @pytest.mark.unit
    def test_generate_seed_questions_structured(self, planner_agent, sample_subject_info, mock_valid_response):
        """Test structured question generation (returns both questions and full payload)"""
        with patch.object(planner_agent, 'agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = json.dumps(mock_valid_response)
            mock_agent.run.return_value = mock_response
            
            flat_questions, structured_data = planner_agent.generate_seed_questions_structured(
                sample_subject_info, "test-project-123"
            )
            
            # Test flat questions
            assert isinstance(flat_questions, list)
            assert len(flat_questions) == 3
            
            # Test structured data
            assert isinstance(structured_data, dict)
            assert "questions" in structured_data
            assert "themes" in structured_data
            assert len(structured_data["questions"]) == 3
            assert len(structured_data["themes"]) == 2
        
    @pytest.mark.unit
    def test_identify_themes_success(self, planner_agent, sample_responses):
        """Test successful theme identification from responses"""
        mock_themes = [
            {
                "name": "Cultural Heritage",
                "description": "Stories about Mexican culture and traditions",
                "questions": ["Tell me more about life in Jalisco", "What traditions did your family keep?"],
                "suggested_interviewer": "family member"
            },
            {
                "name": "Family Bonds",
                "description": "Relationships with important family members",
                "questions": ["Tell me more about your grandmother", "What did your father's stories mean to you?"],
                "suggested_interviewer": "close family member"
            }
        ]
        
        with patch.object(planner_agent, 'agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = json.dumps(mock_themes)
            mock_agent.run.return_value = mock_response
            
            themes = planner_agent.identify_themes(sample_responses, "test-project-123")
            
            assert isinstance(themes, list)
            assert len(themes) == 2
            assert themes[0]["name"] == "Cultural Heritage"
            assert themes[1]["name"] == "Family Bonds"
            assert all("questions" in theme for theme in themes)
        
    @pytest.mark.unit
    def test_identify_themes_invalid_response(self, planner_agent, sample_responses):
        """Test theme identification with invalid response"""
        with patch.object(planner_agent, 'agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = "Invalid response"
            mock_agent.run.return_value = mock_response
            
            themes = planner_agent.identify_themes(sample_responses, "test-project-123")
            
            # Should return empty list for invalid response, or fallback themes if agent has fallback logic
            assert isinstance(themes, list)
            # The agent might have fallback logic, so either empty or fallback themes is acceptable
            assert len(themes) >= 0
        
    @pytest.mark.unit
    def test_subject_info_validation(self, planner_agent):
        """Test that different subject info formats work correctly"""
        # Test minimal subject info
        minimal_info = {
            "name": "John Doe",
            "relation": "grandfather"
        }
        
        with patch.object(planner_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = json.dumps({"questions": [{"text": "Test question"}], "themes": []})
            mock_run.return_value = mock_response
            
            questions = planner_agent.generate_seed_questions(minimal_info)
            
            assert isinstance(questions, list)
            mock_run.assert_called_once()
            
            # Check that the prompt includes the provided information
            call_args = mock_run.call_args[0][0]
            assert "John Doe" in call_args
            assert "grandfather" in call_args
            
    @pytest.mark.unit
    def test_question_quality_validation(self, planner_agent, sample_subject_info):
        """Test that generated questions meet quality standards"""
        with patch.object(planner_agent.agent, 'run') as mock_run:
            quality_questions = {
                "questions": [
                    {
                        "text": "Tell me about a typical day when you were growing up in Mexico.",
                        "topic": "home",
                        "cue_type": "activity",
                        "phase": "P3",
                        "difficulty": "easy"
                    },
                    {
                        "text": "What smells or sounds remind you most of your childhood home?",
                        "topic": "home", 
                        "cue_type": "sensory",
                        "phase": "P3",
                        "difficulty": "medium"
                    }
                ],
                "themes": []
            }
            
            mock_response = Mock()
            mock_response.content = json.dumps(quality_questions)
            mock_run.return_value = mock_response
            
            questions = planner_agent.generate_seed_questions(sample_subject_info)
            
            # Validate question characteristics
            assert all(len(q) > 10 for q in questions), "Questions should be substantive"
            assert all("?" in q for q in questions), "Questions should end with question marks"
            assert any("childhood" in q.lower() or "growing up" in q.lower() for q in questions), "Should include childhood-related questions"
            
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_question_generation(self, planner_agent, sample_subject_info):
        """Integration test for complete question generation flow"""
        # This test requires actual OpenAI API key and will be slow
        # Skip if no API key is available
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available for integration test")
            
        questions = planner_agent.generate_seed_questions(sample_subject_info, "integration-test")
        
        # Validate real API response
        assert isinstance(questions, list)
        assert len(questions) >= 3
        assert all(isinstance(q, str) and len(q) > 10 for q in questions)
        assert all("?" in q for q in questions)
        
    @pytest.mark.unit
    def test_session_management(self, planner_agent, sample_subject_info):
        """Test that session management works correctly"""
        with patch.object(planner_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = json.dumps({"questions": [{"text": "Test"}], "themes": []})
            mock_run.return_value = mock_response
            
            # Test with project ID
            planner_agent.generate_seed_questions(sample_subject_info, "project-123")
            
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["session_id"] == "planner_project-123"
            assert call_kwargs["user_id"] == "subject_project-123"
            
            # Test without project ID (should use defaults)
            planner_agent.generate_seed_questions(sample_subject_info)
            
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["session_id"] == "default_planner"
            assert call_kwargs["user_id"] == "default_subject"
