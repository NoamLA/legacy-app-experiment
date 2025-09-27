"""
Prober Agent - Generates adaptive follow-up questions during interviews
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb
from typing import List, Dict, Any
import json

class ProberAgent:
    def __init__(self):
        # Initialize with Agno's proper session management
        self.db = InMemoryDb()
        
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            name="Interview Prober",
            role="Generate thoughtful follow-up questions that deepen the conversation",
            instructions=[
                "You are an expert interviewer skilled in drawing out meaningful stories.",
                "Generate follow-up questions that probe deeper into responses without being intrusive.",
                "Balance factual details with emotional reflection.",
                "Maintain a warm, curious tone that encourages sharing.",
                "Occasionally inject playful or lighter questions to keep the conversation comfortable.",
                "Help subjects reflect on the significance of their experiences.",
                "Consider the full context of previous questions and responses when generating follow-ups."
            ],
            markdown=True,
            # Enable Agno's built-in session management
            db=self.db,
            add_history_to_context=True,  # Include conversation history in context
            num_history_runs=5,  # Include last 5 exchanges for context
            enable_user_memories=True,  # Remember facts about subjects
        )
    
    def generate_followup_questions(
        self, 
        original_question: str, 
        response: str, 
        context: Dict[str, Any] = None,
        project_id: str = None
    ) -> List[str]:
        """Generate 2-3 follow-up questions based on the response"""
        
        context_info = ""
        if context:
            context_info = f"""
            Context:
            - Interview theme: {context.get('theme', 'General')}
            - Subject age: {context.get('age', 'Unknown')}
            - Previous topics covered: {', '.join(context.get('previous_topics', []))}
            """
        
        prompt = f"""
        Generate 2-3 thoughtful follow-up questions based on this interview exchange:
        
        Original Question: {original_question}
        Response: {response}
        
        {context_info}
        
        The follow-up questions should:
        1. Dig deeper into interesting details mentioned
        2. Explore emotional or meaningful aspects
        3. Connect to broader life themes
        4. Be gentle and respectful
        5. Encourage storytelling
        
        Avoid:
        - Questions that are too personal or invasive
        - Repetitive questions
        - Yes/no questions
        
        Return as a JSON array of strings.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"prober_{project_id}" if project_id else "default_prober"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🔍 Generating follow-up questions using session_id: {session_id}")
        
        response_obj = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        try:
            content = response_obj.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            questions = json.loads(json_str)
            return questions if isinstance(questions, list) else []
        except:
            # Fallback questions based on simple analysis
            return self._generate_fallback_questions(response)
    
    def _generate_fallback_questions(self, response: str) -> List[str]:
        """Generate simple follow-up questions when parsing fails"""
        
        fallback_questions = []
        
        # Simple keyword-based follow-ups
        if "family" in response.lower():
            fallback_questions.append("Tell me more about your family during that time.")
        
        if "difficult" in response.lower() or "hard" in response.lower():
            fallback_questions.append("How did that experience shape you?")
        
        if "happy" in response.lower() or "joy" in response.lower():
            fallback_questions.append("What made that moment so special?")
        
        if "work" in response.lower() or "job" in response.lower():
            fallback_questions.append("What did you learn from that experience?")
        
        # Default questions if no keywords match
        if not fallback_questions:
            fallback_questions = [
                "Can you tell me more about that?",
                "How did that make you feel?",
                "What do you remember most about that time?"
            ]
        
        return fallback_questions[:3]  # Return max 3 questions
    
    def suggest_reflection_questions(self, interview_summary: str, project_id: str = None) -> List[str]:
        """Generate reflective questions based on the interview so far"""
        
        prompt = f"""
        Based on this interview summary, suggest 3-4 reflective questions that help the subject 
        think about the deeper meaning of their experiences:
        
        Interview Summary:
        {interview_summary}
        
        The questions should:
        1. Help them reflect on patterns in their life
        2. Connect different experiences together
        3. Explore what they've learned
        4. Consider their legacy and impact
        
        Return as a JSON array of strings.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"prober_{project_id}" if project_id else "default_prober"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"💭 Generating reflection questions using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            questions = json.loads(json_str)
            return questions if isinstance(questions, list) else []
        except:
            return [
                "Looking back, what patterns do you see in your life?",
                "What would you want your family to remember about you?",
                "What experiences shaped who you are today?",
                "What wisdom would you want to pass on?"
            ]
    
    def adapt_question_style(self, subject_profile: Dict[str, Any], base_question: str, project_id: str = None) -> str:
        """Adapt question style based on subject's personality and preferences"""
        
        prompt = f"""
        Adapt this interview question for a subject with these characteristics:
        
        Subject Profile:
        - Age: {subject_profile.get('age', 'Unknown')}
        - Communication style: {subject_profile.get('communication_style', 'Unknown')}
        - Energy level: {subject_profile.get('energy_level', 'Unknown')}
        - Interests: {', '.join(subject_profile.get('interests', []))}
        
        Base Question: {base_question}
        
        Adapt the question to be more suitable for this person while maintaining the same intent.
        Return just the adapted question as a string.
        """
        
        # Use project_id as session_id for continuity
        session_id = f"prober_{project_id}" if project_id else "default_prober"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🎨 Adapting question style using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        return response.content.strip().strip('"')
