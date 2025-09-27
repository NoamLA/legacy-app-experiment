"""
Summarizer Agent - Compiles interviews into narratives and outputs
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from typing import List, Dict, Any
import json

class SummarizerAgent:
    def __init__(self):
        # Initialize with Agno's proper session management
        self.db = InMemoryDb()
        
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            name="Interview Summarizer",
            role="Transform interview content into engaging narratives and summaries",
            instructions=[
                "You are an expert biographer and storyteller.",
                "Transform raw interview content into engaging, readable narratives.",
                "Preserve the subject's voice and personality in your writing.",
                "Create different types of outputs: timelines, thematic stories, and highlight quotes.",
                "Focus on the human story, not just facts and dates.",
                "Write with warmth, respect, and authenticity.",
                "Consider the full context of all previous conversations when creating summaries."
            ],
            markdown=True,
            # Enable Agno's built-in session management
            db=self.db,
            add_history_to_context=True,  # Include conversation history in context
            num_history_runs=10,  # Include more history for comprehensive summaries
            enable_user_memories=True,  # Remember facts about subjects
        )
    
    def create_timeline_narrative(self, interview_data: List[Dict[str, Any]], project_id: str = None) -> str:
        """Create a chronological life story from interview responses"""
        
        # Organize responses by life periods
        responses_text = self._format_responses_for_analysis(interview_data)
        
        prompt = f"""
        Create a chronological timeline narrative from these interview responses:
        
        {responses_text}
        
        Structure the narrative as a life story with these sections:
        1. Early Life & Childhood
        2. Youth & Education  
        3. Career & Achievements
        4. Family & Relationships
        5. Later Years & Reflections
        
        Write in a warm, biographical style that:
        - Preserves the subject's voice and personality
        - Flows naturally between time periods
        - Highlights key moments and turning points
        - Includes specific details and stories mentioned
        - Feels like a story someone would want to read
        
        Use third person narrative style.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"summarizer_{project_id}" if project_id else "default_summarizer"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🎨 Creating thematic story using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        return response.content
    
    def create_thematic_story(self, theme: str, related_responses: List[Dict[str, Any]], project_id: str = None) -> str:
        """Create a focused story around a specific theme"""
        
        responses_text = self._format_responses_for_analysis(related_responses)
        
        prompt = f"""
        Create a thematic story focused on "{theme}" using these interview responses:
        
        {responses_text}
        
        Write a cohesive narrative that:
        - Explores this theme deeply across the subject's life
        - Connects different experiences and time periods
        - Shows how this theme shaped the person
        - Includes specific stories and examples
        - Reveals insights and wisdom gained
        
        Write in an engaging, story-like format that could stand alone as a chapter.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"summarizer_{project_id}" if project_id else "default_summarizer"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🎨 Creating thematic story using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        return response.content
    
    def extract_memorable_quotes(self, interview_data: List[Dict[str, Any]], project_id: str = None) -> List[Dict[str, str]]:
        """Extract the most memorable and meaningful quotes from interviews"""
        
        responses_text = self._format_responses_for_analysis(interview_data)
        
        prompt = f"""
        Extract 8-12 of the most memorable, meaningful, or characteristic quotes from these interviews:
        
        {responses_text}
        
        Select quotes that:
        - Capture the subject's personality and voice
        - Express important values or wisdom
        - Tell a story in just a few words
        - Are emotionally resonant
        - Show humor, insight, or character
        
        Return as JSON with this structure:
        [
            {{
                "quote": "The exact words spoken",
                "context": "Brief context about when/why this was said",
                "category": "wisdom|humor|values|memory|insight"
            }}
        ]
        """
        
        response = self.agent.run(prompt)
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            quotes = json.loads(json_str)
            return quotes if isinstance(quotes, list) else []
        except:
            # Return empty list if parsing fails
            return []
    
    def create_podcast_script(self, interview_data: List[Dict[str, Any]]) -> str:
        """Generate a podcast script from interview content"""
        
        responses_text = self._format_responses_for_analysis(interview_data)
        
        prompt = f"""
        Create a podcast script based on these interview responses:
        
        {responses_text}
        
        Format as a conversational podcast with:
        - Engaging introduction that sets the scene
        - Natural flow between topics
        - The subject's actual words preserved as much as possible
        - Smooth transitions between themes
        - A meaningful conclusion
        
        Use this format:
        [INTRO MUSIC]
        
        HOST: Welcome to Legacy Stories...
        
        [SUBJECT NAME]: [Their actual words from interviews]
        
        HOST: [Contextual narration and transitions]
        
        Structure it as a 15-20 minute podcast episode.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"summarizer_{project_id}" if project_id else "default_summarizer"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🎨 Creating thematic story using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        return response.content
    
    def create_web_page_content(self, interview_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate structured content for a web page memorial"""
        
        responses_text = self._format_responses_for_analysis(interview_data)
        
        prompt = f"""
        Create content for a memorial web page based on these interviews:
        
        {responses_text}
        
        Generate content for these sections:
        1. Hero section (brief, compelling summary)
        2. Life story (condensed biographical narrative)
        3. Values & wisdom (key principles and lessons)
        4. Favorite memories (3-4 standout stories)
        5. Family reflections (what made them special)
        
        Return as JSON with keys: hero, life_story, values, memories, reflections
        Each value should be well-formatted HTML-ready text.
        """
        
        response = self.agent.run(prompt)
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            web_content = json.loads(json_str)
            return web_content if isinstance(web_content, dict) else {}
        except:
            return {
                "hero": "A life well lived, stories worth sharing.",
                "life_story": "This is the story of a remarkable person...",
                "values": "Family, kindness, and perseverance were central values.",
                "memories": "Every day brought new adventures and joy.",
                "reflections": "A legacy of love and wisdom that continues to inspire."
            }
    
    def _format_responses_for_analysis(self, interview_data: List[Dict[str, Any]]) -> str:
        """Format interview responses for agent analysis"""
        
        formatted = []
        for item in interview_data:
            if isinstance(item, dict):
                question = item.get('question', 'Unknown question')
                answer = item.get('answer', 'No answer provided')
                formatted.append(f"Q: {question}\nA: {answer}\n")
        
        return "\n".join(formatted)
