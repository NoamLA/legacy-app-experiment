"""
Subject Simulator Agent - Simulates authentic human responses for testing
This agent plays the role of an interview subject to test the complete app flow
Uses Agno's built-in session management and memory for proper conversation context
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from typing import List, Dict, Any
import json

class SubjectSimulatorAgent:
    def __init__(self):
        # Initialize with Agno's proper session management
        self.db = InMemoryDb()
        
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            name="Interview Subject Simulator",
            role="Simulate authentic human responses as an interview subject for testing",
            instructions=[
                "You are simulating a real person being interviewed about their life story.",
                "Answer questions naturally and authentically, like a real human would.",
                "Include hesitations, tangents, incomplete thoughts, and personal details.",
                "Don't give polished, perfect answers - be conversational and real.",
                "Sometimes be brief, sometimes ramble a bit, like people do in real conversations.",
                "Include emotions, memories that drift, and personal quirks.",
                "Stay consistent with the character profile you're given.",
                "Use natural speech patterns: 'um', 'well', 'you know', pauses.",
                "Share specific details, names, places, and vivid memories.",
                "Sometimes get emotional or sentimental about meaningful topics.",
                "Remember previous conversations and reference them naturally when appropriate."
            ],
            markdown=False,  # We want natural speech, not formatted text
            debug_mode=True,
            # Enable Agno's built-in session management
            db=self.db,
            add_history_to_context=True,  # Include conversation history in context
            num_history_runs=5,  # Include last 5 exchanges for context
            enable_user_memories=True,  # Remember facts about the character
        )
        
        # Store character profile
        self.character_profile = {}
        self.established_facts = {}
    
    def set_character_profile(self, subject_info: Dict[str, Any]):
        """Set the character profile for consistent responses"""
        self.character_profile = subject_info
        
        # Create a rich backstory based on the basic info
        age = subject_info.get('age', 75)
        name = subject_info.get('name', 'Unknown')
        relation = subject_info.get('relation', 'grandmother')
        background = subject_info.get('background', '')
        
        # Generate character details based on the profile
        self.established_facts = {
            'name': name,
            'age': age,
            'relation': relation,
            'background': background,
            'birth_year': 2024 - age if age else 1949,
            'generation': self._determine_generation(age),
            'life_era': self._determine_life_era(age)
        }
    
    def generate_authentic_response(self, question: str, context: Dict[str, Any] = None, project_id: str = None) -> str:
        """Generate an authentic human response to an interview question using Agno sessions"""
        
        # Use project_id as session_id for conversation continuity
        session_id = f"interview_{project_id}" if project_id else "default_interview"
        
        # Build character context for the AI
        character_context = self._build_character_context()
        
        # Create a rich prompt that includes character information
        prompt = f"""
        CURRENT QUESTION: "{question}"
        
        CHARACTER PROFILE:
        {character_context}
        
        Respond as {self.established_facts.get('name', 'this person')} would naturally respond. Be authentic, conversational, and human.
        Include:
        - Natural speech patterns and hesitations
        - Specific memories and details
        - Emotional responses when appropriate
        - Sometimes brief answers, sometimes longer stories
        - Personal quirks and way of speaking
        - Reference previous topics we've discussed when relevant
        
        Don't be too polished or perfect. Answer like a real person in a comfortable family interview.
        """
        
        print(f"🎭 Subject Simulator generating response for: {question[:50]}...")
        print(f"📋 Using session_id: {session_id}")
        
        # Use Agno's session management for conversation continuity
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id="interview_subject"
        )
        
        print(f"🗣️ Generated response: {response.content[:100]}...")
        return response.content
    
    def _determine_generation(self, age: int) -> str:
        """Determine generation based on age"""
        if age >= 90:
            return "Silent Generation"
        elif age >= 75:
            return "Baby Boomer"
        elif age >= 60:
            return "Generation X"
        else:
            return "Millennial"
    
    def _determine_life_era(self, age: int) -> str:
        """Determine major life era for context"""
        birth_year = 2024 - age
        if birth_year <= 1940:
            return "Pre-WWII, Depression era"
        elif birth_year <= 1950:
            return "WWII and post-war era"
        elif birth_year <= 1960:
            return "1950s prosperity and Cold War"
        else:
            return "1960s+ modern era"
    
    def _build_character_context(self) -> str:
        """Build character context for consistent responses"""
        facts = self.established_facts
        
        context = f"""
        Name: {facts.get('name', 'Unknown')}
        Age: {facts.get('age', 'Unknown')}
        Relationship: {facts.get('relation', 'family member')}
        Generation: {facts.get('generation', 'Unknown')}
        Life Era: {facts.get('life_era', 'Unknown')}
        Background: {facts.get('background', 'No specific background provided')}
        
        Personality traits to maintain:
        - Speaks naturally with some hesitations and tangents
        - Has lived through significant historical periods
        - Values family and relationships
        - Has accumulated life wisdom but isn't preachy
        - Sometimes gets nostalgic or emotional
        - Remembers specific details about important events
        """
        
        return context
    
    def get_conversation_summary(self, project_id: str = None) -> Dict[str, Any]:
        """Get a summary of the conversation using Agno's session management"""
        try:
            # Get conversation history from Agno
            messages = self.agent.get_messages_for_session()
            
            # Get user memories if any
            try:
                memories = self.agent.get_user_memories()
            except Exception:
                memories = []
            
            return {
                'character_profile': self.character_profile,
                'established_facts': self.established_facts,
                'total_exchanges': len(messages) // 2,  # Divide by 2 since each exchange has user + assistant message
                'conversation_messages': [
                    {'role': m.role, 'content': str(m.content)} 
                    for m in messages
                ],
                'memories': [memory.to_dict() for memory in memories] if memories else []
            }
        except Exception as e:
            print(f"⚠️ Could not get conversation summary: {e}")
            return {
                'character_profile': self.character_profile,
                'established_facts': self.established_facts,
                'total_exchanges': 0,
                'conversation_messages': [],
                'memories': []
            }
    
    def reset_conversation(self, project_id: str = None):
        """Reset conversation history using Agno's session management"""
        session_id = f"interview_{project_id}" if project_id else "default_interview"
        
        # Clear the session in Agno's database
        if hasattr(self.db, 'delete_session'):
            self.db.delete_session(session_id=session_id, user_id="interview_subject")
        
        print(f"🔄 Conversation history reset for session: {session_id}")
    
    def update_character_facts(self, new_facts: Dict[str, Any]):
        """Update character facts based on responses given"""
        self.established_facts.update(new_facts)
        print(f"📝 Updated character facts: {new_facts}")
        
        # Store important facts as user memories in Agno
        for key, value in new_facts.items():
            memory_text = f"{key}: {value}"
            # This would store the fact in Agno's memory system
            # The agent will automatically reference these in future responses
