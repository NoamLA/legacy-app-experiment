"""
Planner Agent - Generates seed questions and identifies themes for interviews
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from typing import List, Dict, Any
import json

class PlannerAgent:
    def __init__(self):
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            name="Interview Planner",
            role="Generate thoughtful interview questions and identify emerging themes",
            instructions=[
                "You are an expert interview planner specializing in family legacy preservation.",
                "Generate warm, engaging questions that build rapport while gathering meaningful stories.",
                "Focus on biographical details, emotional connections, and life-defining moments.",
                "Keep questions conversational and comfortable for elderly subjects.",
                "After collecting responses, identify 3-5 major themes for deeper exploration."
            ],
            markdown=True,
        )
    
    def generate_seed_questions(self, subject_info: Dict[str, Any]) -> List[str]:
        """Generate 10-25 warm-up questions based on subject information"""
        
        prompt = f"""
        Generate 15-20 warm-up questions for a legacy interview with the following subject:
        
        Name: {subject_info.get('name', 'Unknown')}
        Age: {subject_info.get('age', 'Unknown')}
        Relation: {subject_info.get('relation', 'Unknown')}
        Background: {subject_info.get('background', 'No additional context')}
        
        The questions should:
        1. Start with easy, comfortable topics
        2. Build rapport and trust
        3. Cover key life areas: childhood, family, career, values, memories
        4. Include some playful/light questions to maintain comfort
        5. Be open-ended to encourage storytelling
        
        Return the questions as a JSON array of strings.
        """
        
        response = self.agent.run(prompt)
        try:
            # Extract JSON from the response
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            questions = json.loads(json_str)
            return questions if isinstance(questions, list) else []
        except:
            # Fallback questions if parsing fails
            return [
                "Tell me about where you were born and what it was like growing up there.",
                "What's your earliest childhood memory?",
                "Who were the most important people in your early life?",
                "What was your family like when you were young?",
                "What did you want to be when you grew up?",
                "Tell me about your school days - what do you remember most?",
                "What was the neighborhood like where you lived?",
                "What were your favorite activities as a child?",
                "Who taught you the most important lessons in life?",
                "What traditions did your family have?",
                "What's a funny story from your childhood?",
                "What was different about the world when you were young?",
                "Tell me about your parents - what were they like?",
                "What values were most important in your household?",
                "What's something you're proud of from your younger years?"
            ]
    
    def identify_themes(self, responses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Analyze responses to identify themes for deeper exploration"""
        
        # Combine all responses for analysis
        combined_responses = "\n\n".join([
            f"Q: {r['question']}\nA: {r['answer']}" 
            for r in responses
        ])
        
        prompt = f"""
        Analyze these interview responses and identify 3-5 major themes for deeper exploration:
        
        {combined_responses}
        
        For each theme, provide:
        1. Theme name (e.g., "Childhood Adventures", "Career Journey", "Family Values")
        2. Brief description of why this theme is significant
        3. 3-5 deeper follow-up questions for this theme
        4. Suggested interviewer (family member type or AI)
        
        Return as JSON with this structure:
        [
            {{
                "name": "Theme Name",
                "description": "Why this theme matters",
                "questions": ["Question 1", "Question 2", ...],
                "suggested_interviewer": "eldest child" or "AI" or "spouse"
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
            
            themes = json.loads(json_str)
            return themes if isinstance(themes, list) else []
        except:
            # Fallback themes if parsing fails
            return [
                {
                    "name": "Early Life & Family",
                    "description": "Childhood memories and family relationships",
                    "questions": [
                        "What was your relationship like with your siblings?",
                        "What family traditions meant the most to you?",
                        "How did your parents meet and fall in love?",
                        "What was the hardest thing about your childhood?",
                        "What made your family unique?"
                    ],
                    "suggested_interviewer": "AI"
                },
                {
                    "name": "Life Lessons & Values",
                    "description": "Core beliefs and wisdom gained through experience",
                    "questions": [
                        "What's the most important lesson life has taught you?",
                        "What values do you hope to pass down?",
                        "What would you do differently if you could?",
                        "What advice would you give to your younger self?",
                        "What are you most proud of in your life?"
                    ],
                    "suggested_interviewer": "eldest child"
                }
            ]
