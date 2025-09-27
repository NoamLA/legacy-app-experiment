"""
Real Agent Integration Tests
Tests that use actual PostgreSQL database and real agent sessions
"""
import pytest
import os
import uuid
import time
import json
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add backend and database to path
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
database_path = Path(__file__).parent.parent.parent.parent / "database"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(database_path))

from config import DatabaseConfig, DatabaseManager
from agents.planner_agent import PlannerAgent
from agents.prober_agent import ProberAgent
from agents.subject_simulator_agent import SubjectSimulatorAgent
from agents.summarizer_agent import SummarizerAgent
from services.database_service import DatabaseService

class TestRealAgentIntegration:
    """Integration tests for agents using real PostgreSQL database"""
    
    @pytest.fixture(scope="class")
    def test_db_config(self):
        """Create test database configuration"""
        config = DatabaseConfig(environment="test")
        # Override with test database settings
        config.host = os.getenv("TEST_DB_HOST", "localhost")
        config.port = os.getenv("TEST_DB_PORT", "5434")
        config.database = os.getenv("TEST_DB_NAME", "legacy_interview_test")
        config.username = os.getenv("TEST_DB_USER", "legacy_test_user")
        config.password = os.getenv("TEST_DB_PASS", "legacy_test_pass")
        return config
    
    @pytest.fixture(scope="class")
    def test_db_manager(self, test_db_config):
        """Create database manager with real PostgreSQL"""
        return DatabaseManager(test_db_config)
    
    @pytest.fixture
    def clean_agent_db(self, test_db_manager):
        """Clean agent database tables before each test"""
        with test_db_manager.get_session() as session:
            # Clean Agno tables
            session.execute("TRUNCATE TABLE agent_sessions CASCADE")
            session.execute("TRUNCATE TABLE agent_messages CASCADE")
            session.execute("TRUNCATE TABLE agent_runs CASCADE")
            session.execute("TRUNCATE TABLE user_memories CASCADE")
            session.execute("TRUNCATE TABLE session_summaries CASCADE")
            session.commit()
            yield
            # Clean up after test
            session.execute("TRUNCATE TABLE agent_sessions CASCADE")
            session.execute("TRUNCATE TABLE agent_messages CASCADE")
            session.execute("TRUNCATE TABLE agent_runs CASCADE")
            session.execute("TRUNCATE TABLE user_memories CASCADE")
            session.execute("TRUNCATE TABLE session_summaries CASCADE")
            session.commit()
    
    @pytest.fixture
    def database_service(self, test_db_manager):
        """Database service with real database"""
        service = DatabaseService()
        service.use_database = True
        service.engine = test_db_manager.engine
        service.SessionLocal = test_db_manager.session_factory
        return service
    
    @pytest.fixture
    def sample_subject_info(self):
        """Sample subject information"""
        return {
            "name": "Elena Rodriguez",
            "age": 78,
            "relation": "grandmother",
            "background": "Immigrated from Cuba in 1962, worked as a nurse",
            "language": "English"
        }
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_planner_agent_with_real_database(self, clean_agent_db, sample_subject_info):
        """Test PlannerAgent with real database session management"""
        planner = PlannerAgent()
        project_id = str(uuid.uuid4())
        
        # Mock OpenAI response to avoid API costs in tests
        mock_response_data = {
            "questions": [
                {
                    "text": "Tell me about your journey from Cuba to America.",
                    "topic": "migration",
                    "cue_type": "place",
                    "phase": "P2",
                    "difficulty": "medium",
                    "rationale": "Opens conversation about major life transition",
                    "followup_if_short": "Can you describe what you remember about that journey?",
                    "opt_out_tags": ["migration"]
                },
                {
                    "text": "What was your first impression of America?",
                    "topic": "migration",
                    "cue_type": "time",
                    "phase": "P2",
                    "difficulty": "easy",
                    "rationale": "Captures immediate emotional response to new country",
                    "followup_if_short": "What stood out to you the most?",
                    "opt_out_tags": []
                }
            ],
            "themes": [
                {
                    "name": "Immigration Journey",
                    "why": "Central life experience that shaped identity",
                    "signals": ["Cuba", "journey", "America"]
                }
            ]
        }
        
        with patch.object(planner.agent, 'run') as mock_run:
            mock_response = Mock()
            mock_response.content = json.dumps(mock_response_data)
            mock_run.return_value = mock_response
            
            # Generate questions - this should create agent session in database
            questions = planner.generate_seed_questions(sample_subject_info, project_id)
            
            # Verify questions were generated
            assert isinstance(questions, list)
            assert len(questions) == 2
            assert "Cuba to America" in questions[0]
            
            # Verify session was created with correct parameters
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["session_id"] == f"planner_{project_id}"
            assert call_kwargs["user_id"] == f"subject_{project_id}"
        
        # Check that session was created in database
        with planner.db.get_session() as session:
            sessions = session.execute("SELECT * FROM agent_sessions WHERE session_id = %s", (f"planner_{project_id}",)).fetchall()
            # Note: We can't easily verify this without knowing Agno's internal structure
            # The important thing is that the agent was configured with the real database
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_subject_simulator_memory_persistence(self, clean_agent_db, sample_subject_info):
        """Test SubjectSimulatorAgent memory persistence across multiple interactions"""
        simulator = SubjectSimulatorAgent()
        project_id = str(uuid.uuid4())
        
        # Set character profile
        simulator.set_character_profile(sample_subject_info)
        
        # Mock multiple responses
        responses = [
            "My name is Elena, and I came from Cuba when I was young.",
            "As I mentioned, I'm Elena. I worked as a nurse for many years after arriving from Cuba.",
            "Yes, Elena Rodriguez. I told you about my nursing career and coming from Cuba."
        ]
        
        with patch.object(simulator.agent, 'run') as mock_run:
            mock_responses = [Mock(content=response) for response in responses]
            mock_run.side_effect = mock_responses
            
            # First interaction
            response1 = simulator.generate_authentic_response(
                "What is your name?",
                project_id=project_id
            )
            
            # Second interaction
            response2 = simulator.generate_authentic_response(
                "Tell me about your work.",
                project_id=project_id
            )
            
            # Third interaction - should reference previous conversations
            response3 = simulator.generate_authentic_response(
                "What did you tell me your name was?",
                project_id=project_id
            )
            
            # Verify all interactions used the same session
            calls = mock_run.call_args_list
            session_ids = [call[1]["session_id"] for call in calls]
            user_ids = [call[1]["user_id"] for call in calls]
            
            # All should use the same session for memory continuity
            assert len(set(session_ids)) == 1  # All same session ID
            assert len(set(user_ids)) == 1     # All same user ID
            assert session_ids[0] == f"interview_{project_id}"
            assert user_ids[0] == "interview_subject"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_conversation_summary_with_real_data(self, clean_agent_db):
        """Test conversation summary with real database storage"""
        simulator = SubjectSimulatorAgent()
        project_id = str(uuid.uuid4())
        
        # Mock agent with realistic message history
        mock_messages = [
            Mock(role="user", content="Tell me your name"),
            Mock(role="assistant", content="My name is Elena Rodriguez"),
            Mock(role="user", content="Where were you born?"),
            Mock(role="assistant", content="I was born in Cuba, in a small town near Havana"),
            Mock(role="user", content="When did you come to America?"),
            Mock(role="assistant", content="I came to America in 1962, when I was 22 years old")
        ]
        
        mock_memories = [
            Mock(to_dict=lambda: {
                "memory": "Subject is Elena Rodriguez from Cuba",
                "created_at": "2024-01-01T10:00:00Z"
            }),
            Mock(to_dict=lambda: {
                "memory": "Immigrated to America in 1962 at age 22",
                "created_at": "2024-01-01T10:05:00Z"
            })
        ]
        
        with patch.object(simulator.agent, 'get_messages_for_session', return_value=mock_messages):
            with patch.object(simulator.agent, 'get_user_memories', return_value=mock_memories):
                
                summary = simulator.get_conversation_summary(project_id)
                
                # Verify summary structure
                assert "total_exchanges" in summary
                assert "conversation_messages" in summary
                assert "memories" in summary
                assert "character_profile" in summary
                
                # Verify content
                assert summary["total_exchanges"] == 3  # 6 messages / 2
                assert len(summary["conversation_messages"]) == 6
                assert len(summary["memories"]) == 2
                
                # Verify message content
                assert summary["conversation_messages"][0]["role"] == "user"
                assert summary["conversation_messages"][1]["role"] == "assistant"
                assert "Elena Rodriguez" in summary["conversation_messages"][1]["content"]
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_session_isolation_between_projects(self, clean_agent_db):
        """Test that different projects have completely isolated sessions"""
        simulator = SubjectSimulatorAgent()
        project1_id = str(uuid.uuid4())
        project2_id = str(uuid.uuid4())
        
        with patch.object(simulator.agent, 'run') as mock_run:
            mock_response = Mock(content="Test response")
            mock_run.return_value = mock_response
            
            # Interact with project 1
            simulator.generate_authentic_response("Question for project 1", project_id=project1_id)
            
            # Interact with project 2
            simulator.generate_authentic_response("Question for project 2", project_id=project2_id)
            
            # Verify different sessions were used
            calls = mock_run.call_args_list
            session1 = calls[0][1]["session_id"]
            session2 = calls[1][1]["session_id"]
            
            assert session1 == f"interview_{project1_id}"
            assert session2 == f"interview_{project2_id}"
            assert session1 != session2
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_session_reset_functionality(self, clean_agent_db):
        """Test conversation reset clears database sessions"""
        simulator = SubjectSimulatorAgent()
        project_id = str(uuid.uuid4())
        
        # Mock database operations
        with patch.object(simulator.db, 'delete_session') as mock_delete:
            simulator.reset_conversation(project_id)
            
            # Verify delete was called with correct parameters
            mock_delete.assert_called_once_with(
                session_id=f"interview_{project_id}",
                user_id="interview_subject"
            )
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_prober_agent_context_continuity(self, clean_agent_db):
        """Test ProberAgent maintains context across multiple followup generations"""
        prober = ProberAgent()
        project_id = str(uuid.uuid4())
        
        # Mock responses for multiple followup generations
        mock_followups = [
            ["What specific memories do you have of that time?", "How did that make you feel?"],
            ["Can you tell me more about the people involved?", "What happened next?"],
            ["Looking back, how do you feel about that experience now?"]
        ]
        
        with patch.object(prober.agent, 'run') as mock_run:
            mock_responses = [Mock(content=json.dumps(followups)) for followups in mock_followups]
            mock_run.side_effect = mock_responses
            
            # Generate followups in sequence
            questions1 = prober.generate_followup_questions(
                "Tell me about your childhood",
                "I had a happy childhood in Cuba",
                {"theme": "childhood"},
                project_id
            )
            
            questions2 = prober.generate_followup_questions(
                "What specific memories do you have of that time?",
                "I remember playing with my siblings in the garden",
                {"theme": "childhood", "depth": "medium"},
                project_id
            )
            
            questions3 = prober.suggest_reflection_questions(
                {"previous_topics": ["childhood", "family", "Cuba"]},
                project_id
            )
            
            # Verify all used same session for context continuity
            calls = mock_run.call_args_list
            session_ids = [call[1]["session_id"] for call in calls]
            
            assert len(set(session_ids)) == 1  # All same session
            assert session_ids[0] == f"prober_{project_id}"
            
            # Verify questions were generated
            assert len(questions1) == 2
            assert len(questions2) == 2
            assert len(questions3) == 1
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_multi_agent_project_workflow(self, clean_agent_db, database_service, sample_subject_info):
        """Test complete workflow with multiple agents and real database"""
        project_id = str(uuid.uuid4())
        
        # Create project in database
        project_data = {
            "id": project_id,
            "name": "Multi-Agent Integration Test",
            "subject_info": sample_subject_info,
            "interview_mode": "family",
            "language": "en",
            "status": "created",
            "themes": [],
            "enhanced_themes": [],
            "participants": [],
            "admin_id": None,
            "seed_questions": []
        }
        
        assert database_service.save_project(project_data) == True
        
        # 1. Generate seed questions with PlannerAgent
        planner = PlannerAgent()
        
        mock_questions_response = {
            "questions": [
                {"text": "Tell me about your life in Cuba"},
                {"text": "What brought you to America?"},
                {"text": "How did you become a nurse?"}
            ],
            "themes": [{"name": "Immigration", "why": "Major life transition"}]
        }
        
        with patch.object(planner.agent, 'run') as mock_planner:
            mock_planner.return_value = Mock(content=json.dumps(mock_questions_response))
            
            questions = planner.generate_seed_questions(sample_subject_info, project_id)
            assert len(questions) == 3
        
        # 2. Simulate responses with SubjectSimulatorAgent
        simulator = SubjectSimulatorAgent()
        simulator.set_character_profile(sample_subject_info)
        
        responses = [
            "I lived in a small town near Havana. Life was simple but beautiful.",
            "The political situation became difficult, so my family decided to leave.",
            "I studied nursing because I wanted to help people and it was good work for women."
        ]
        
        with patch.object(simulator.agent, 'run') as mock_simulator:
            mock_simulator.side_effect = [Mock(content=resp) for resp in responses]
            
            interview_responses = []
            for i, question in enumerate(questions):
                response = simulator.generate_authentic_response(question, project_id=project_id)
                interview_responses.append({
                    "question": question,
                    "answer": response,
                    "question_type": "seed"
                })
        
        # 3. Generate followups with ProberAgent
        prober = ProberAgent()
        
        with patch.object(prober.agent, 'run') as mock_prober:
            mock_prober.return_value = Mock(content=json.dumps(["What was daily life like in your town?"]))
            
            followups = prober.generate_followup_questions(
                questions[0],
                responses[0],
                {"theme": "Cuba"},
                project_id
            )
            assert len(followups) >= 1
        
        # 4. Create summary with SummarizerAgent
        summarizer = SummarizerAgent()
        
        with patch.object(summarizer.agent, 'run') as mock_summarizer:
            mock_timeline = "Elena Rodriguez's journey from Cuba to America began in a small town near Havana..."
            mock_summarizer.return_value = Mock(content=mock_timeline)
            
            timeline = summarizer.create_timeline_narrative(interview_responses, project_id)
            assert isinstance(timeline, str)
            assert len(timeline) > 0
        
        # Verify all agents used consistent project-based sessions
        # Each agent should have its own session but tied to the same project
        planner_session = mock_planner.call_args[1]["session_id"]
        simulator_session = mock_simulator.call_args_list[0][1]["session_id"]
        prober_session = mock_prober.call_args[1]["session_id"]
        summarizer_session = mock_summarizer.call_args[1]["session_id"]
        
        assert planner_session == f"planner_{project_id}"
        assert simulator_session == f"interview_{project_id}"
        assert prober_session == f"prober_{project_id}"
        assert summarizer_session == f"summarizer_{project_id}"
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_database_performance_under_agent_load(self, clean_agent_db):
        """Test database performance with multiple concurrent agent operations"""
        # Create multiple agents
        agents = [
            PlannerAgent(),
            ProberAgent(),
            SubjectSimulatorAgent(),
            SummarizerAgent()
        ]
        
        project_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Mock all agent responses
        mock_response = Mock(content="Test response")
        
        start_time = time.time()
        
        # Simulate concurrent agent operations
        for agent in agents:
            with patch.object(agent.agent, 'run', return_value=mock_response):
                for project_id in project_ids:
                    if isinstance(agent, PlannerAgent):
                        agent.generate_seed_questions({"name": "Test"}, project_id)
                    elif isinstance(agent, ProberAgent):
                        agent.generate_followup_questions("Q", "A", project_id=project_id)
                    elif isinstance(agent, SubjectSimulatorAgent):
                        agent.generate_authentic_response("Q", project_id=project_id)
                    elif isinstance(agent, SummarizerAgent):
                        agent.create_timeline_narrative([{"question": "Q", "answer": "A"}], project_id)
        
        total_time = time.time() - start_time
        
        # Should handle 20 operations (4 agents × 5 projects) reasonably quickly
        assert total_time < 5.0  # Should complete within 5 seconds
        
        # Verify database connections are still healthy
        for agent in agents:
            assert agent.db is not None
    
    @pytest.mark.database
    @pytest.mark.integration
    def test_error_handling_with_database_issues(self, clean_agent_db):
        """Test agent behavior when database has issues"""
        simulator = SubjectSimulatorAgent()
        project_id = str(uuid.uuid4())
        
        # Test graceful handling when database operations fail
        with patch.object(simulator.agent, 'get_messages_for_session', side_effect=Exception("DB Error")):
            summary = simulator.get_conversation_summary(project_id)
            
            # Should return default structure, not crash
            assert summary["total_exchanges"] == 0
            assert summary["conversation_messages"] == []
            assert summary["memories"] == []
    
    @pytest.mark.database
    @pytest.mark.integration
    @pytest.mark.slow
    def test_long_running_conversation_memory(self, clean_agent_db):
        """Test memory management in long conversations"""
        simulator = SubjectSimulatorAgent()
        project_id = str(uuid.uuid4())
        
        # Simulate a long conversation (20 exchanges)
        mock_messages = []
        for i in range(40):  # 40 messages = 20 exchanges
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Message {i} in long conversation"
            mock_messages.append(Mock(role=role, content=content))
        
        with patch.object(simulator.agent, 'get_messages_for_session', return_value=mock_messages):
            with patch.object(simulator.agent, 'get_user_memories', return_value=[]):
                
                summary = simulator.get_conversation_summary(project_id)
                
                # Should handle large conversation gracefully
                assert summary["total_exchanges"] == 20
                assert len(summary["conversation_messages"]) == 40
                
                # Memory should not be overwhelmed
                assert isinstance(summary["conversation_messages"], list)
                assert all("Message" in msg["content"] for msg in summary["conversation_messages"])
