"""
Planner Agent - Generates seed questions and identifies themes for interviews
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from database.agent_db import get_agent_db
from typing import List, Dict, Any, Tuple
import json
import re

# ---- Small helpers -----------------------------------------------------------

TOPICS = {
    "identity","home","family","friendship","love","work","craft","migration",
    "faith/culture","service","community","play/hobbies","traditions",
    "turning_points","resilience","humor","values"
}
CUES   = {"sensory","place","object","people","time","activity","photo_prompt"}
PHASES = {"P0","P1","P2","P3","P4"}
DIFFS  = {"easy","medium","deeper"}

def _strip_fences(s: str) -> str:
    s = s.strip()
    if "```" in s:
        # take the longest JSON-looking block
        parts = [p for p in s.split("```") if "{" in p or "[" in p]
        s = parts[-1].strip() if parts else s
        if s.startswith("json"):
            s = s[4:].strip()
    return s

def _safe_json_loads(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        # last-ditch: try to trim stray leading/trailing text
        start = s.find("{")
        end   = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start:end+1])
        raise

def _explode_text_into_questions(text: str) -> list[str]:
    """
    Split a single 'text' that contains multiple questions into separate items.
    Keeps '?' and removes empties/duplicates.
    """
    parts = [p.strip() for p in re.split(r'\?\s*', text.strip()) if p.strip()]
    out = []
    for p in parts:
        q = p.rstrip("?") + "?"
        if q and q not in out:
            out.append(q)
    return out

def _validate_and_repair(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure top-level keys
    if not isinstance(payload, dict):
        raise ValueError("PlannerAgent: expected dict at top level")
    payload.setdefault("questions", [])
    payload.setdefault("themes", [])

    fixed_questions = []
    for q in payload["questions"]:
        if not isinstance(q, dict):
            continue

        # defaults
        q.setdefault("text", "")
        q.setdefault("topic", "identity")
        q.setdefault("cue_type", "people")
        q.setdefault("phase", "P0")
        q.setdefault("difficulty", "easy")
        q.setdefault("rationale", "Anchors memory gently; invites a short scene.")
        q.setdefault("followup_if_short", "Could you share a small scene or example?")
        q.setdefault("opt_out_tags", [])

        # enum repairs
        if q["topic"] not in TOPICS: q["topic"] = "identity"
        if q["cue_type"] not in CUES: q["cue_type"] = "people"
        if q["phase"] not in PHASES: q["phase"] = "P0"
        if q["difficulty"] not in DIFFS: q["difficulty"] = "easy"
        if not isinstance(q["opt_out_tags"], list): q["opt_out_tags"] = []

        # explode any bundled multi-question text into separate items
        texts = _explode_text_into_questions(q["text"]) or ["?"]

        for i, t in enumerate(texts):
            q_i = q if i == 0 else dict(q)  # shallow copy metadata
            t = t.strip().rstrip("?")
            if " and " in t:  # simple heuristic to avoid stacked clauses
                t = t.split(" and ")[0].strip()
            q_i["text"] = t + "?"
            fixed_questions.append(q_i)

    payload["questions"] = fixed_questions

    # Themes shape
    fixed_themes = []
    for t in payload["themes"]:
        if not isinstance(t, dict):
            continue
        t.setdefault("name", "Home & Belonging")
        t.setdefault("why", "Recurring signals of place, family bonds, and safety.")
        signals = t.get("signals") or ["home", "place", "routines", "family"]
        t["signals"] = signals if isinstance(signals, list) else ["home"]
        fixed_themes.append(t)
    payload["themes"] = fixed_themes

    return payload


class PlannerAgent:
    def __init__(self):
        # Initialize with Agno's proper session management
        self.db = get_agent_db()
        
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            name="Interview Planner",
            role="Generate thoughtful interview questions and identify emerging themes",
            # Enable Agno's built-in session management
            db=self.db,
            add_history_to_context=True,  # Include conversation history in context
            num_history_runs=3,  # Include last 3 planning sessions for context
            enable_user_memories=True,  # Remember facts about subjects
            instructions=["""
You are a senior interview planner for family legacy biographies. Design a *real* biographical interview that starts gently, builds trust, and elicits short, story-shaped answers (30–120 seconds).

RAMPED FLOW (strict):
- P0 Settle-In (2–3 Qs): identity, today, comfort. No trauma, no earliest-memory starts.
- P1 Home & Daily Life Now (3–4): routines, spaces, people.
- P2 Near Past (3–4): recent roles, events, community.
- P3 Formative Years (4–6): childhood/adolescence using memory cues.
- P4 Values & Reflections (2–3): lessons, pride, hopes.

MEMORY CUES (choose one per Q): sensory | place | object | people | time | activity | photo_prompt

ELDER-FRIENDLY TONE:
- One idea per question. Short sentences. No stacked clauses. Offer choices without forcing recall.
- Avoid assumptions about countries/eras/trauma unless intake notes include them.
- Use opt-in frames for sensitive areas: “If you’re comfortable, could we talk about…?”

COMFORT & TRANSITIONS:
- Before sensitive: “This might be hard — share only what you want.”
- After brief answer: gentle nudge in followup_if_short (e.g., “Could you share a small scene or example?”).
- Encourage sensory detail: “What did it smell like? Who was there?”

STRUCTURE & OUTPUT:
- Generate 15–20 questions spanning P0→P4 in order, with smooth escalation (easy→deeper).
- Each question includes: topic, cue_type, phase (P0–P4), difficulty (easy/medium/deeper), rationale (1–2 short sentences), followup_if_short, opt_out_tags (e.g., ["sensitive","migration","war"] or []).
- Infer 3–5 candidate themes from your plan (e.g., “Home & Belonging,” “Work & Craft,” “Journeys,” “Values & Faith,” “Love & Friendship”).

STRICT JSON ONLY (no markdown fences):
{
  "questions": [
    {
      "text": "string, friendly, one idea, ends with ?",
      "topic": "identity|home|family|friendship|love|work|craft|migration|faith/culture|service|community|play/hobbies|traditions|turning_points|resilience|humor|values",
      "cue_type": "sensory|place|object|people|time|activity|photo_prompt",
      "phase": "P0|P1|P2|P3|P4",
      "difficulty": "easy|medium|deeper",
      "rationale": "why this unlocks memory in 1–2 sentences",
      "followup_if_short": "gentle nudge",
      "opt_out_tags": []
    }
  ],
  "themes": [
    { "name": "string", "why": "string", "signals": ["keywords"] }
  ]
}
"""],
            markdown=True,
        )

    def generate_seed_questions_structured(
        self, subject_info: Dict[str, Any], project_id: str = None
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Generate 15–20 structured questions and candidate themes.
        Returns (flat_question_texts, full_structured_payload)
        """

        prompt = f"""
You are planning a legacy interview. Use the intake:

Name: {subject_info.get('name','Unknown')}
Age: {subject_info.get('age','Unknown')}
Relation: {subject_info.get('relation','Unknown')}
Background notes: {subject_info.get('background','None')}
Language: {subject_info.get('language','English')}
Sensitive topics to avoid unless explicitly invited: {subject_info.get('sensitive_topics','None')}
Key interests or anchors (if any): {subject_info.get('anchors','None')}

Plan an elder-friendly seed interview starting in the present and gently moving back in time.
Use memory cues (sensory/place/object/people/time/activity/photo_prompt).
Do NOT start with “earliest memory” or trauma-adjacent prompts.
Respect opt-in for sensitive topics. Include opt_out_tags when applicable.

Generate 15–20 questions across phases P0→P4 (in order) and 3–5 themes.
Respond ONLY with strict JSON matching the schema you were given.
"""

        # Use project_id as session_id for continuity
        session_id = f"planner_{project_id}" if project_id else "default_planner"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🤖 Sending prompt to OpenAI (truncated): {prompt[:200]}...")
        print(f"📋 Using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        content = str(getattr(response, "content", response))

        try:
            json_str = _strip_fences(content)
            parsed_data = _safe_json_loads(json_str)
            validated = _validate_and_repair(parsed_data)

            # Flatten just the texts for quick UI display
            flat_questions = [q["text"] for q in validated.get("questions", []) if q.get("text")]
            return flat_questions, validated

        except Exception as e:
            print(f"❌ JSON parsing/validation failed: {e}")
            print(f"📄 Raw content was: {content}")

            # Fallback: safe, phase-ordered basics that reflect conclusions
            fallback = {
                "questions": [
                    {"text":"Where do you feel most at home these days?","topic":"home","cue_type":"place","phase":"P0","difficulty":"easy","rationale":"Safe present-day anchor.","followup_if_short":"What do you see from your chair?","opt_out_tags":[]},
                    {"text":"What small part of your day brings you joy?","topic":"identity","cue_type":"activity","phase":"P0","difficulty":"easy","rationale":"Builds warm rapport via routine.","followup_if_short":"Can you share a small example?","opt_out_tags":[]},
                    {"text":"Who do you speak with most in a typical week?","topic":"family","cue_type":"people","phase":"P1","difficulty":"easy","rationale":"People anchors recall detail.","followup_if_short":"What do you talk about?","opt_out_tags":[]},
                    {"text":"Is there an object you keep nearby because it means something to you?","topic":"traditions","cue_type":"object","phase":"P1","difficulty":"easy","rationale":"Objects unlock stories.","followup_if_short":"Where did it come from?","opt_out_tags":[]},
                    {"text":"Are there places in town that feel special to you?","topic":"home","cue_type":"place","phase":"P1","difficulty":"easy","rationale":"Place + routine yields scenes.","followup_if_short":"What do you notice there?","opt_out_tags":[]},
                    {"text":"Has there been a recent celebration or event that stands out?","topic":"community","cue_type":"time","phase":"P2","difficulty":"medium","rationale":"Near-past scene setting.","followup_if_short":"Who was there?","opt_out_tags":[]},
                    {"text":"If you’re comfortable, could we talk about a big move or difficult time?","topic":"migration","cue_type":"time","phase":"P3","difficulty":"deeper","rationale":"Opt-in gate for sensitive era.","followup_if_short":"Only what you wish to share.","opt_out_tags":["sensitive","migration"]},
                    {"text":"What was your neighborhood like when you were growing up?","topic":"home","cue_type":"place","phase":"P3","difficulty":"medium","rationale":"Childhood place anchors.","followup_if_short":"What smells or sounds do you recall?","opt_out_tags":[]},
                    {"text":"What games or hobbies did you enjoy as a child?","topic":"play/hobbies","cue_type":"activity","phase":"P3","difficulty":"easy","rationale":"Light, specific cues.","followup_if_short":"Who played with you?","opt_out_tags":[]},
                    {"text":"What values guided your family when you were young?","topic":"values","cue_type":"people","phase":"P3","difficulty":"medium","rationale":"Opens value narratives.","followup_if_short":"Who modeled that for you?","opt_out_tags":[]},
                    {"text":"Are there achievements you feel proud of?","topic":"turning_points","cue_type":"activity","phase":"P4","difficulty":"medium","rationale":"Invites positive appraisal.","followup_if_short":"What made that meaningful?","opt_out_tags":[]},
                    {"text":"What lessons would you like to share with future generations?","topic":"values","cue_type":"time","phase":"P4","difficulty":"deeper","rationale":"Legacy extraction.","followup_if_short":"One example that taught this?","opt_out_tags":[]},
                    {"text":"How would you like your family to remember you?","topic":"love","cue_type":"people","phase":"P4","difficulty":"deeper","rationale":"Closes with identity and love.","followup_if_short":"What small ritual best shows that?","opt_out_tags":[]}
                ],
                "themes":[
                    {"name":"Home & Belonging","why":"Recurring anchors of place, routine, and safety.","signals":["home","chair","window","street","places"]},
                    {"name":"Family & Care","why":"Frequent references to children, caregiver, and calls.","signals":["daughter","son","grandchildren","Miriam"]},
                    {"name":"Journeys & Resilience","why":"Migration and endurance underpin identity.","signals":["move","Haifa","boat","British Mandate"]},
                    {"name":"Work & Craft","why":"Hands-on making (sewing/embroidery) as dignity.","signals":["sew","embroidery","shop","work"]},
                    {"name":"Values & Legacy","why":"Lessons, pride, remembrance, hopes.","signals":["values","lessons","remember","proud"]}
                ]
            }
            flat = [q["text"] for q in fallback["questions"]]
            return flat, fallback

    def generate_seed_questions(self, subject_info: Dict[str, Any], project_id: str = None) -> List[str]:
        """
        Backward-compatible: returns only a flat list[str] of question texts.
        """
        flat, _structured = self.generate_seed_questions_structured(subject_info, project_id)
        return flat

        

    def identify_themes(self, responses: List[Dict[str, str]], project_id: str = None) -> List[Dict[str, Any]]:
        """Analyze responses to identify themes for deeper exploration"""
        combined = "\n\n".join([f"Q: {r.get('question','')}\nA: {r.get('answer','')}" for r in responses])

        prompt = f"""
Analyze these interview responses and identify 3–5 major themes for deeper exploration:

{combined}

For each theme, provide:
1. Theme name
2. Why it matters (1–2 sentences)  
3. 10-15 deeper follow-up questions that explore this theme comprehensively
4. Suggested interviewer (e.g., "eldest child", "AI", "spouse")

The questions should:
- Progress from general to specific
- Include both factual and emotional aspects
- Encourage storytelling and detailed memories
- Cover different time periods and perspectives
- Be appropriate for the subject's background and age

Return STRICT JSON array:
[
  {{
    "name": "Theme Name",
    "description": "Why this theme matters",
    "questions": [
      "Question 1 - introductory/general",
      "Question 2 - specific memory",
      "Question 3 - emotional aspect",
      "...continue with 10-15 total questions"
    ],
    "suggested_interviewer": "eldest child"
  }}
]
"""
        # Use project_id as session_id for continuity
        session_id = f"planner_{project_id}" if project_id else "default_planner"
        user_id = f"subject_{project_id}" if project_id else "default_subject"
        
        print(f"🎯 Identifying themes using session_id: {session_id}")
        
        response = self.agent.run(
            prompt,
            session_id=session_id,
            user_id=user_id
        )
        content = str(getattr(response, "content", response))

        try:
            json_str = _strip_fences(content)
            themes = _safe_json_loads(json_str)
            return themes if isinstance(themes, list) else []
        except Exception:
            return [
                {
                    "name": "Home & Belonging",
                    "description": "Place and routine provide safety and identity.",
                    "questions": [
                        "Can you describe your favorite spot at home and what makes it special?",
                        "Who visits you there, and what do you do together?",
                        "What sounds, smells, or sights make this place feel like home?",
                        "How has your relationship with this space changed over time?",
                        "What objects in this space hold the most meaning for you?",
                        "Can you share a specific memory that happened in this place?",
                        "Who else has spent meaningful time in this space with you?",
                        "What daily routines happen here that bring you comfort?",
                        "If you had to leave this place, what would you miss most?",
                        "How does this space reflect who you are as a person?",
                        "What stories would these walls tell if they could speak?",
                        "How do you hope others will remember this place?"
                    ],
                    "suggested_interviewer": "eldest child"
                },
                {
                    "name": "Journeys & Resilience", 
                    "description": "Moves and hardships shaped outlook and choices.",
                    "questions": [
                        "What was the most significant journey or move in your life?",
                        "What led to the decision to make that change?",
                        "Who supported you during that transition?",
                        "What did you have to leave behind, and how did that feel?",
                        "What surprised you most about adapting to something new?",
                        "How did you find strength during the most difficult moments?",
                        "What skills or qualities did you discover in yourself?",
                        "Who were the people who helped you along the way?",
                        "What advice would you give someone facing a similar challenge?",
                        "How did this experience change your perspective on life?",
                        "What are you most proud of about how you handled it?",
                        "What did you learn about yourself that you didn't know before?",
                        "How has this experience influenced the choices you've made since?",
                        "What would you want your family to understand about this time?",
                        "Looking back, what meaning do you find in this journey?"
                    ],
                    "suggested_interviewer": "AI"
                }
            ]
