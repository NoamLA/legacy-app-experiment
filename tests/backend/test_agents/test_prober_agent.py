"""
Tests for ProberAgent - Follow-up Question Generation
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from agents.prober_agent import ProberAgent

class TestProberAgent:
    """Test suite for ProberAgent follow-up question generation"""
    
    @pytest.fixture
    def prober_agent(self):
        """Create a ProberAgent instance for testing"""
        return ProberAgent()
    
    @pytest.fixture
    def sample_conversation_context(self):
        """Sample conversation context for testing"""
        return {
            "previous_questions": [
                "Tell me about where you were born.",
                "What was your childhood like?"
            ],
            "previous_answers": [
                "I was born in a small village in Mexico.",
                "My childhood was simple but happy. We didn't have much money."
            ],
            "identified_themes": ["family", "heritage", "hardship"],
            "subject_profile": {
                "name": "Maria",
                "age": 75,
                "relation": "grandmother"
            }
        }
    
    @pytest.mark.unit
    def test_prober_agent_initialization(self, prober_agent):
        """Test that ProberAgent initializes correctly"""
        assert prober_agent is not None
        assert prober_agent.agent is not None
        assert prober_agent.db is not None
    
    @pytest.mark.unit
    def test_generate_followup_questions_success(self, prober_agent, sample_conversation_context):
        """Test successful follow-up question generation"""
        original_question = "Tell me about your childhood."
        response = "My childhood was simple but happy. We didn't have much money but we had love."
        
        mock_followups = [
            "What are some specific happy memories from your childhood?",
            "How did your family manage during difficult financial times?",
            "What did 'having love' mean to your family?"
        ]
        
        with patch.object(prober_agent, 'agent') as mock_agent:
            mock_response = Mock()
            mock_response.content = json.dumps(mock_followups)
            mock_agent.run.return_value = mock_response
            
            questions = prober_agent.generate_followup_questions(
                original_question, 
                response, 
                sample_conversation_context,
                "test-project-123"
            )
            
            assert isinstance(questions, list)
            assert len(questions) == 3
            assert all(isinstance(q, str) for q in questions)
            assert "specific happy memories" in questions[0]
            
            # Verify session management
            call_kwargs = mock_agent.run.call_args[1]
            assert call_kwargs["session_id"] == "prober_test-project-123"
            assert call_kwargs["user_id"] == "subject_test-project-123"
    
    @pytest.mark.unit
    def test_generate_followup_questions_invalid_json(self, prober_agent):
        """Test handling of invalid JSON response"""
        with patch.object(prober_agent, "agent") as mock_agent:
            mock_response = Mock()
            mock_response.content = "This is not valid JSON"
            mock_agent.run.return_value = mock_response
            
            questions = prober_agent.generate_followup_questions(
                "Test question",
                "Test response"
            )
            
            # Should return empty list for invalid JSON
            assert isinstance(questions, list)
            assert len(questions) == 0
    
    @pytest.mark.unit
    def test_suggest_reflection_questions(self, prober_agent, sample_conversation_context):
        """Test reflection question generation"""
        mock_reflections = [
            "Looking back on everything we've discussed, what stands out most to you?",
            "How do you think these experiences shaped who you are today?",
            "What would you want your grandchildren to know about these times?"
        ]
        
        with patch.object(prober_agent, "agent") as mock_agent:
            mock_response = Mock()
            mock_response.content = json.dumps(mock_reflections)
            mock_agent.run.return_value = mock_response
            
            questions = prober_agent.suggest_reflection_questions(
            sample_conversation_context,
            "test-project-123"
            )
        
            assert isinstance(questions, list)
            assert len(questions) == 3
            assert any("shaped who you are" in q for q in questions)
            assert any("grandchildren" in q for q in questions)
    
    @pytest.mark.unit
    def test_adapt_question_style(self, prober_agent):
        """Test question style adaptation"""
        mock_adapted = {
            "adapted_questions": [
                "Can you tell me more about that time when you felt really happy?",
                "What was it like when money was tight for your family?"
            ],
            "style_notes": "Questions adapted for elderly subject, using simpler language and emotional cues"
        }
        
        mock_response = Mock()
        mock_response.content = json.dumps(mock_adapted)
        with patch.object(prober_agent, "agent") as mock_agent:
        mock_agent.run.return_value = mock_response
        
        original_questions = [
            "Elaborate on the emotional significance of that period",
            "Describe the socioeconomic challenges your family faced"
            ]
        
            result = prober_agent.adapt_question_style(
            original_questions,
            {"age": 85, "education": "elementary"},
            "test-project-123"
            )
        
            assert "adapted_questions" in result
            assert "style_notes" in result
            assert len(result["adapted_questions"]) == 2
            assert "simpler language" in result["style_notes"]
    
    @pytest.mark.unit
    def test_context_analysis(self, prober_agent, sample_conversation_context):
        """Test conversation context analysis"""
        with patch.object(prober_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = json.dumps(["test question"])
            mock_run.return_value = mock_response
            
            prober_agent.generate_followup_questions(
                "Tell me about your family",
                "We were very close",
                sample_conversation_context
            )
            
            # Verify context was included in prompt
            prompt = mock_run.call_args[0][0]
            assert "Previous topics covered" in prompt
            assert "Interview theme" in prompt
            assert "Subject age" in prompt
    
    @pytest.mark.unit
    def test_question_depth_progression(self, prober_agent):
        """Test that questions progress from surface to deep"""
        with patch.object(prober_agent.agent, 'run') as mock_run:
            # Mock progressive depth responses
            responses = [
                ["What did you enjoy most about that?"],  # Surface
                ["How did that experience change you?"],  # Medium
                ["What does that mean to you now, looking back?"]  # Deep
            ]
            
            mock_responses = [Mock(content=json.dumps(resp)) for resp in responses]
            mock_run.side_effect = mock_responses
            
            # Test progression
            context = {"conversation_depth": "surface"}
            surface_q = prober_agent.generate_followup_questions("Test", "Answer", context)
            
            context = {"conversation_depth": "medium"}
            medium_q = prober_agent.generate_followup_questions("Test", "Answer", context)
            
            context = {"conversation_depth": "deep"}
            deep_q = prober_agent.generate_followup_questions("Test", "Answer", context)
            
            assert "enjoy" in surface_q[0]  # Surface level
            assert "change" in medium_q[0]  # Deeper exploration
            assert "looking back" in deep_q[0]  # Reflection
    
    @pytest.mark.unit
    def test_emotional_cue_detection(self, prober_agent):
        """Test detection of emotional cues in responses"""
        emotional_responses = [
            ("I was so happy that day", ["happiness", "joy"]),
            ("It was really difficult for us", ["hardship", "struggle"]),
            ("I still miss her every day", ["grief", "loss"]),
            ("We were so proud of him", ["pride", "accomplishment"])
        ]
        
        with patch.object(prober_agent.agent, 'run') as mock_run:
            for response_text, expected_emotions in emotional_responses:
                mock_questions = [f"Tell me more about that {expected_emotions[0]}"]
                mock_response = Mock()
                mock_response.content = json.dumps(mock_questions)
                mock_run.return_value = mock_response
                
                questions = prober_agent.generate_followup_questions(
                    "Test question",
                    response_text
                )
                
                # Verify emotional context was considered
                prompt = mock_run.call_args[0][0]
                assert response_text in prompt
    
    @pytest.mark.unit
    def test_session_consistency(self, prober_agent):
        """Test session management consistency"""
        project_id = "consistency-test-123"
        
        with patch.object(prober_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = json.dumps(["test question"])
            mock_run.return_value = mock_response
            
            # Multiple calls with same project ID
            prober_agent.generate_followup_questions("Q1", "A1", project_id=project_id)
            prober_agent.generate_followup_questions("Q2", "A2", project_id=project_id)
            prober_agent.suggest_reflection_questions({}, project_id=project_id)
            
            # All calls should use same session
            calls = mock_run.call_args_list
            session_ids = [call[1]["session_id"] for call in calls]
            user_ids = [call[1]["user_id"] for call in calls]
            
            assert all(sid == f"prober_{project_id}" for sid in session_ids)
            assert all(uid == f"subject_{project_id}" for uid in user_ids)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_followup_generation(self, prober_agent, sample_conversation_context):
        """Integration test for complete follow-up generation flow"""
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available for integration test")
        
        questions = prober_agent.generate_followup_questions(
            "What was your childhood like?",
            "My childhood was wonderful. We lived on a farm and I helped my parents with the animals.",
            sample_conversation_context,
            "integration-test"
        )
        
        # Validate real API response
        assert isinstance(questions, list)
        assert len(questions) >= 1
        assert all(isinstance(q, str) and len(q) > 10 for q in questions)
        assert all("?" in q for q in questions)
    
    @pytest.mark.unit
    def test_question_quality_validation(self, prober_agent):
        """Test that generated follow-up questions meet quality standards"""
        with patch.object(prober_agent.agent, 'run') as mock_run:
            high_quality_questions = [
                "What specific animals did you help care for on the farm?",
                "Can you describe a typical day helping your parents?",
                "What did you learn from working with animals at such a young age?"
            ]
            
            mock_response = Mock()
            mock_response.content = json.dumps(high_quality_questions)
            mock_run.return_value = mock_response
            
            questions = prober_agent.generate_followup_questions(
                "Tell me about the farm",
                "We had cows, chickens, and pigs. I loved feeding them."
            )
            
            # Quality checks
            assert all(len(q) > 15 for q in questions), "Questions should be detailed"
            assert all("?" in q for q in questions), "Questions should be interrogative"
            assert any("specific" in q.lower() for q in questions), "Should ask for specifics"
            assert any("describe" in q.lower() or "tell me" in q.lower() for q in questions), "Should encourage storytelling"
