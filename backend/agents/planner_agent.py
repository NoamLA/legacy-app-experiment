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
            instructions=["""
You are a senior interview planner for family legacy biographies. Your goal is to create a real biographical interview that starts gently, builds trust, and elicits rich, story-shaped memories.

Ramped flow: begin with present-day and identity (“today”), then near-past routines and people, then formative periods (adolescence/childhood), then optional sensitive eras the subject explicitly opts into.

Memory cues: favor questions that use concrete anchors:

Sensory (smells, sounds, tastes), Place (home, street, town), Objects (kept items, tools, photos), People (names, roles), Time (seasons, holidays), Activities (work, rituals).

Elder-friendly tone: short sentences, plain language, one idea per question, no stacked sub-questions. Offer choices without forcing recall. Avoid assumptions about countries, eras, or trauma unless the subject has already mentioned them or intake notes say it’s okay.

Comfort first: opening questions must feel safe and familiar (today/this week/home/favorites). Avoid “earliest memory” as a first question.

Cultural and historical sensitivity: when referencing places/periods, use neutral, opt-in frames: “If you’re comfortable, would you like to talk about…?”

Generate 15–20 questions with a smooth progression and include fields for topic, cue type, phase, difficulty, and a gentle “followup_if_short”.

End by proposing 3–5 candidate themes inferred from the questions you plan (e.g., “Home & Belonging,” “Work & Craft,” “Journeys,” “Values & Faith,” “Love & Friendship”).

Output strict JSON: { "questions": [...], "themes": [...] } with the schema provided in the user prompt.

Keep questions conversational, open-ended, and designed for voice answers of 30–120 seconds. 
"""
            ],
            markdown=True,
        )
    
    def generate_seed_questions(self, subject_info: Dict[str, Any]) -> List[str]:
        """Generate 10-25 warm-up questions based on subject information"""
        
        prompt = f"""
        You are planning a legacy interview. Use the intake data:

        Name: {subject_info.get('name','Unknown')}
        Age: {subject_info.get('age','Unknown')}
        Relation: {subject_info.get('relation','Unknown')}
        Background notes: {subject_info.get('background','None')}
        Language: {subject_info.get('language','English')}
        Sensitive topics to avoid unless explicitly invited: {subject_info.get('sensitive_topics','None')}
        Key interests or anchors (if any): {subject_info.get('anchors','None')}

        Plan a gentle, elder-friendly **seed interview** that starts present-day and gradually explores the past.
        Use memory cues (sensory/place/object/people/time/activity). Avoid assumptions about specific countries/eras
        unless present in background notes. Do **not** start with "earliest memory" or trauma-adjacent prompts.

        **Phases**
        - Phase 0: Settle-In (2–3 questions): identity, today, comfort.
        - Phase 1: Home & Daily Life Now (3–4): routines, spaces, people.
        - Phase 2: Near Past (3–4): recent meaningful events, roles, communities.
        - Phase 3: Formative Years (4–6): childhood/adolescence with gentle cueing.
        - Phase 4: Values & Reflections (2–3): lessons, pride, hopes.

        **Cue taxonomy** (choose per question): sensory | place | object | people | time | activity | photo_prompt
        **Topics** (pick as relevant): identity, home, family, friendship, love, work, craft, migration, faith/culture,
        service, community, play/hobbies, traditions, turning_points, resilience, humor.

        **Output JSON schema (STRICT)**
        {{
        "questions": [
            {{
            "text": "string (one question, friendly, no clauses)",
            "topic": "one_of_topics",
            "cue_type": "one_of_cues",
            "phase": "P0|P1|P2|P3|P4",
            "difficulty": "easy|medium|deeper",
            "rationale": "1–2 short sentences on why this unlocks memory",
            "followup_if_short": "gentle nudge if answer is brief",
            "opt_out_tags": ["sensitive","migration","war"]  // empty if not applicable
            }}
        ],
        "themes": [
            {{
            "name": "string",
            "why": "1–2 sentences",
            "signals": ["keywords to look for in answers"]
            }}
        ]
        }}

        **Opening examples (style guide)**
        - Good: "To start, where do you feel most at home these days?"
        - Good: "What’s a small part of your day that makes you smile?"
        - Good: "Who do you speak with most in a typical week?"
        - Good (object cue): "Is there an object at home that you keep within reach because it means something to you?"
        - Opt-in: "If you’d like, we can talk about big moves or difficult times later. Would that be okay?"

        Generate 15–20 questions spanning P0→P4 with a smooth ramp, and 3–5 candidate themes.
        Respond **only** with valid JSON matching the schema, no markdown fences.
        """

        
        print(f"🤖 Sending prompt to OpenAI: {prompt[:200]}...")
        response = self.agent.run(prompt)
        print(f"📥 Raw response from OpenAI: {response}")
        print(f"📝 Response content: {response.content}")
        
        try:
            # Extract JSON from the response
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content
            
            print(f"🔍 Extracted JSON string: {json_str}")
            parsed_data = json.loads(json_str)
            print(f"✅ Parsed data: {parsed_data}")
            
            # Extract just the question text from the complex structure
            if isinstance(parsed_data, dict) and 'questions' in parsed_data:
                questions = [q['text'] for q in parsed_data['questions'] if isinstance(q, dict) and 'text' in q]
                print(f"📝 Extracted question texts: {questions}")
                return questions
            elif isinstance(parsed_data, list):
                # Handle simple array format
                questions = parsed_data
                print(f"📝 Simple questions array: {questions}")
                return questions
            else:
                print(f"❌ Unexpected data structure: {type(parsed_data)}")
                return []
        except Exception as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"📄 Raw content was: {content}")
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
