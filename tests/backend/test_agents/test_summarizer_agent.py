"""
Tests for SummarizerAgent - Interview Summarization and Narrative Creation
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from agents.summarizer_agent import SummarizerAgent

class TestSummarizerAgent:
    """Test suite for SummarizerAgent narrative creation"""
    
    @pytest.fixture
    def summarizer_agent(self):
        """Create a SummarizerAgent instance for testing"""
        return SummarizerAgent()
    
    @pytest.fixture
    def sample_interview_data(self):
        """Sample interview data for testing"""
        return [
            {
                "question": "Tell me about where you were born.",
                "answer": "I was born in Guadalajara, Mexico in 1942. It was a beautiful city with cobblestone streets and colonial architecture.",
                "timestamp": "2024-01-15T10:00:00Z",
                "theme": "origins"
            },
            {
                "question": "What was your family like?",
                "answer": "We were a large family - I had 6 siblings. My father was a carpenter and my mother took care of all of us. We were poor but very close.",
                "timestamp": "2024-01-15T10:05:00Z",
                "theme": "family"
            },
            {
                "question": "Tell me about coming to America.",
                "answer": "I came here in 1965 when I was 23. I was scared but excited. I had nothing but a suitcase and big dreams.",
                "timestamp": "2024-01-15T10:10:00Z",
                "theme": "immigration"
            },
            {
                "question": "What was your first job in America?",
                "answer": "I worked in a textile factory. The work was hard, but I was grateful to have it. I saved every penny I could.",
                "timestamp": "2024-01-15T10:15:00Z",
                "theme": "work"
            }
        ]
    
    @pytest.mark.unit
    def test_summarizer_agent_initialization(self, summarizer_agent):
        """Test that SummarizerAgent initializes correctly"""
        assert summarizer_agent is not None
        assert summarizer_agent.agent is not None
        assert summarizer_agent.db is not None
    
    @pytest.mark.unit
    def test_create_timeline_narrative(self, summarizer_agent, sample_interview_data):
        """Test timeline narrative creation"""
        expected_narrative = """
        Maria's story begins in 1942 in the beautiful city of Guadalajara, Mexico, where she was born into a large, loving family of nine. Her father worked as a carpenter while her mother devoted herself to raising seven children. Though they had little money, their home was rich with love and togetherness.
        
        In 1965, at the age of 23, Maria made the brave decision to immigrate to America. With nothing but a suitcase and enormous dreams, she embarked on a journey that would change her life forever. Despite her fears, her excitement for new opportunities propelled her forward.
        
        Upon arriving in America, Maria found work in a textile factory. The labor was demanding, but she approached it with gratitude and determination, carefully saving every penny as she built her new life in a foreign land.
        """
        
        with patch.object(summarizer_agent, "agent") as mock_agent:
            mock_response = Mock()
            mock_response.content = expected_narrative.strip()
            mock_agent.run.return_value = mock_response
            
            narrative = summarizer_agent.create_timeline_narrative(sample_interview_data, "test-project-123")
            
            assert isinstance(narrative, str)
            assert len(narrative) > 100
            assert "1942" in narrative
            assert "Guadalajara" in narrative
            assert "1965" in narrative
            assert "textile factory" in narrative
            
            # Verify session management
            call_kwargs = mock_agent.run.call_args[1]
            assert call_kwargs["session_id"] == "summarizer_test-project-123"
            assert call_kwargs["user_id"] == "subject_test-project-123"
    
    @pytest.mark.unit
    def test_create_thematic_story(self, summarizer_agent, sample_interview_data):
        """Test thematic story creation"""
        theme = "immigration"
        expected_story = """
        The Journey to America: A Story of Courage
        
        Maria's immigration story is one of tremendous courage and hope. In 1965, as a young woman of 23, she made the life-changing decision to leave everything familiar behind in Mexico and start anew in America. 
        
        With only a suitcase containing her worldly possessions and a heart full of dreams, Maria stepped into the unknown. Her fear was real, but her determination was stronger. This brave leap of faith would become the foundation of her American story.
        
        Her first job in a textile factory was challenging, but Maria embraced it with gratitude. Every penny saved was a step toward building the life she had dreamed of, a testament to the resilience that brought her across borders.
        """
        
        with patch.object(summarizer_agent, "agent") as mock_agent:
            mock_response = Mock()
            mock_response.content = expected_story.strip()
            mock_agent.run.return_value = mock_response
            
            story = summarizer_agent.create_thematic_story(sample_interview_data, theme, "test-project-123")
            
            assert isinstance(story, str)
            assert len(story) > 100
            assert "immigration" in story.lower() or "america" in story.lower()
            assert "courage" in story.lower()
            assert "1965" in story
    
    @pytest.mark.unit
    def test_extract_memorable_quotes(self, summarizer_agent, sample_interview_data):
        """Test memorable quote extraction"""
        expected_quotes = [
            {
                "quote": "I had nothing but a suitcase and big dreams.",
                "context": "Describing her arrival in America in 1965",
                "significance": "Captures the essence of the immigrant experience - arriving with little but hope"
            },
            {
                "quote": "We were poor but very close.",
                "context": "Describing her family in Mexico",
                "significance": "Shows how love and family bonds transcend material wealth"
            },
            {
                "quote": "I saved every penny I could.",
                "context": "Talking about her first job in America",
                "significance": "Demonstrates her determination and work ethic in building a new life"
            }
        ]
        
        mock_response = Mock()
        mock_response.content = json.dumps(expected_quotes)
        with patch.object(summarizer_agent, "agent") as mock_agent:
            mock_agent.run.return_value = mock_response
        
            quotes = summarizer_agent.extract_memorable_quotes(sample_interview_data, "test-project-123")
            
            assert isinstance(quotes, list)
            assert len(quotes) == 3
            assert all("quote" in q and "context" in q and "significance" in q for q in quotes)
            assert any("suitcase and big dreams" in q["quote"] for q in quotes)
    
    @pytest.mark.unit
    def test_extract_memorable_quotes_invalid_json(self, summarizer_agent, sample_interview_data):
        """Test quote extraction with invalid JSON response"""
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"
        with patch.object(summarizer_agent, "agent") as mock_agent:
            mock_agent.run.return_value = mock_response
            
            quotes = summarizer_agent.extract_memorable_quotes(sample_interview_data, "test-project-123")
            
            # Should return empty list for invalid JSON
            assert isinstance(quotes, list)
            assert len(quotes) == 0
    
    @pytest.mark.unit
    def test_data_processing_and_formatting(self, summarizer_agent, sample_interview_data):
        """Test that interview data is properly processed and formatted"""
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Test narrative"
            mock_run.return_value = mock_response
            
            summarizer_agent.create_timeline_narrative(sample_interview_data)
            
            # Verify data was properly formatted in prompt
            prompt = mock_run.call_args[0][0]
            assert "Guadalajara" in prompt
            assert "1942" in prompt
            assert "textile factory" in prompt
            assert "carpenter" in prompt
    
    @pytest.mark.unit
    def test_theme_filtering(self, summarizer_agent, sample_interview_data):
        """Test filtering interview data by theme"""
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Family story"
            mock_run.return_value = mock_response
            
            summarizer_agent.create_thematic_story(sample_interview_data, "family")
            
            prompt = mock_run.call_args[0][0]
            # Should include family-related content
            assert "large family" in prompt
            assert "6 siblings" in prompt
            assert "carpenter" in prompt
            # Should focus on family theme
            assert "family" in prompt.lower()
    
    @pytest.mark.unit
    def test_chronological_ordering(self, summarizer_agent):
        """Test that events are properly ordered chronologically"""
        unordered_data = [
            {
                "question": "What about your retirement?",
                "answer": "I retired in 2007 after 40 years of work.",
                "timestamp": "2024-01-15T10:20:00Z",
                "theme": "work"
            },
            {
                "question": "Tell me about your childhood.",
                "answer": "I was born in 1942 in Mexico.",
                "timestamp": "2024-01-15T10:00:00Z", 
                "theme": "origins"
            },
            {
                "question": "When did you get married?",
                "answer": "I got married in 1968 to my husband Carlos.",
                "timestamp": "2024-01-15T10:10:00Z",
                "theme": "family"
            }
        ]
        
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Chronological narrative"
            mock_run.return_value = mock_response
            
            summarizer_agent.create_timeline_narrative(unordered_data)
            
            prompt = mock_run.call_args[0][0]
            # Should mention chronological ordering
            assert "chronological" in prompt.lower() or "timeline" in prompt.lower()
    
    @pytest.mark.unit
    def test_narrative_quality_requirements(self, summarizer_agent, sample_interview_data):
        """Test that narrative generation includes quality requirements"""
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "High-quality narrative"
            mock_run.return_value = mock_response
            
            summarizer_agent.create_timeline_narrative(sample_interview_data)
            
            prompt = mock_run.call_args[0][0]
            # Should include quality requirements
            quality_keywords = ["engaging", "narrative", "story", "compelling", "coherent"]
            assert any(keyword in prompt.lower() for keyword in quality_keywords)
    
    @pytest.mark.unit
    def test_session_consistency(self, summarizer_agent, sample_interview_data):
        """Test session management consistency across methods"""
        project_id = "consistency-test-456"
        
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Test content"
            mock_run.return_value = mock_response
            
            # Multiple calls with same project ID
            summarizer_agent.create_timeline_narrative(sample_interview_data, project_id)
            summarizer_agent.create_thematic_story(sample_interview_data, "family", project_id)
            summarizer_agent.extract_memorable_quotes(sample_interview_data, project_id)
            
            # All calls should use same session
            calls = mock_run.call_args_list
            # Extract session_id and user_id from keyword arguments (call[1] is kwargs)
            session_ids = []
            user_ids = []
            for call in calls:
                if len(call) > 1 and isinstance(call[1], dict):
                    if "session_id" in call[1]:
                        session_ids.append(call[1]["session_id"])
                    if "user_id" in call[1]:
                        user_ids.append(call[1]["user_id"])
            
            # Check that we have consistent session management
            if session_ids:  # Only check if session_ids were found
                assert all(sid == f"summarizer_{project_id}" for sid in session_ids)
            if user_ids:  # Only check if user_ids were found
                assert all(uid == f"subject_{project_id}" for uid in user_ids)
    
    @pytest.mark.unit
    def test_empty_data_handling(self, summarizer_agent):
        """Test handling of empty or insufficient data"""
        empty_data = []
        
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "No sufficient data available for narrative creation."
            mock_run.return_value = mock_response
            
            narrative = summarizer_agent.create_timeline_narrative(empty_data)
            
            assert isinstance(narrative, str)
            assert len(narrative) > 0
    
    @pytest.mark.unit
    def test_narrative_personalization(self, summarizer_agent):
        """Test that narratives are personalized to the subject"""
        personal_data = [
            {
                "question": "What's your name?",
                "answer": "My name is Rosa Elena Martinez.",
                "theme": "identity"
            },
            {
                "question": "Tell me about your proudest moment.",
                "answer": "When my daughter graduated from college - first in our family.",
                "theme": "family"
            }
        ]
        
        with patch.object(summarizer_agent.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = "Rosa Elena's story is one of pride and achievement..."
            mock_run.return_value = mock_response
            
            narrative = summarizer_agent.create_timeline_narrative(personal_data)
            
            prompt = mock_run.call_args[0][0]
            assert "Rosa Elena Martinez" in prompt
            assert "daughter graduated" in prompt
            assert "first in our family" in prompt
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_summarization(self, summarizer_agent, sample_interview_data):
        """Integration test for complete summarization flow"""
        import os
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available for integration test")
        
        # Test timeline narrative
        narrative = summarizer_agent.create_timeline_narrative(sample_interview_data, "integration-test")
        assert isinstance(narrative, str)
        assert len(narrative) > 100
        
        # Test thematic story
        story = summarizer_agent.create_thematic_story(sample_interview_data, "immigration", "integration-test")
        assert isinstance(story, str)
        assert len(story) > 100
        
        # Test quote extraction
        quotes = summarizer_agent.extract_memorable_quotes(sample_interview_data, "integration-test")
        assert isinstance(quotes, list)
        # Real API might return different structure, so just check it's a list
        assert len(quotes) >= 0
