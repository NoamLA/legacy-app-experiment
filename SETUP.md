# Legacy Interview App - Setup Guide

This guide will help you set up and run the Legacy Interview App for experimentation and development.

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **OpenAI API Key** (for GPT-4o AI agents and optional Whisper voice transcription)

## Quick Start

### 1. Clone and Setup Environment

```bash
cd /Users/noamleviavshalom/legacy

# Copy environment template and add your API keys
cp .env.template .env
# Edit .env file with your OpenAI API key - see env-setup.md for details
```

### 2. Run Automated Setup (Recommended)

```bash
python setup.py
```

This will:
- Create a virtual environment (`legacy-venv/`)
- Install Python dependencies in the virtual environment
- Copy environment template to `.env`
- Check Node.js dependencies
- Validate your configuration

### 3. Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv legacy-venv

# Activate virtual environment
source legacy-venv/bin/activate  # Linux/Mac
# OR
legacy-venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Setup environment
cp .env.template .env
# Edit .env with your OpenAI API key
```

### 4. Start the Application

**Option A: With Virtual Environment (Recommended)**

Terminal 1 (Backend with venv):
```bash
./start-with-venv.sh
```

Terminal 2 (Frontend):
```bash
./start-frontend.sh
```

**Option B: Manual activation**

Terminal 1:
```bash
source activate-venv.sh  # Activate venv
python start-backend.py  # Start backend
```

Terminal 2:
```bash
./start-frontend.sh
```

The backend will be available at: `http://localhost:8000`
The frontend will be available at: `http://localhost:3000`

## Testing the Flow

1. **Create a Project**: Visit `http://localhost:3000` and click "Start Your First Interview"

2. **Fill Project Details**:
   - Project Name: "Test Interview"
   - Subject Name: "Test Subject"
   - Relationship: "grandmother"
   - Interview Mode: "Self Interview" (AI-led)

3. **Start Seed Questions**: The AI will generate 15-20 warm-up questions

4. **Answer Questions**: Provide sample responses to see the AI's follow-up questions

5. **Identify Themes**: After 5+ responses, the system will analyze and identify themes

6. **Deep Dive**: Explore themes with more targeted questions

## Key Features to Test

### 🤖 AI Agents
- **Planner Agent**: Generates contextual questions based on subject info
- **Prober Agent**: Creates intelligent follow-up questions
- **Summarizer Agent**: Transforms responses into narratives

### 📱 User Interface
- **Responsive Design**: Works on desktop and mobile
- **Progress Tracking**: Visual progress through interview phases
- **Theme Cards**: Organized exploration of identified themes

### 🔄 Interview Flow
- **Phase 1**: Seed questions for rapport building
- **Phase 2**: AI theme identification
- **Phase 3**: Deep-dive interviews by theme
- **Phase 4**: Summary and export generation

## API Endpoints

The backend provides a RESTful API:

- `POST /projects` - Create new project
- `GET /projects/{id}/seed-questions` - Generate seed questions
- `POST /responses` - Submit interview responses
- `POST /projects/{id}/identify-themes` - Analyze themes
- `POST /projects/{id}/summarize` - Generate summaries

View full API documentation at: `http://localhost:8000/docs`

## Customization Points

### Adding New Question Types
Edit `backend/agents/planner_agent.py` to modify question generation logic.

### Changing AI Models
Update the model configuration in agent constructors:
```python
model=Claude(id="claude-3-5-sonnet-20241022")
```

### UI Styling
Modify `src/App.css` and Tailwind classes for visual customization.

### Export Formats
Extend `backend/agents/summarizer_agent.py` to add new output formats.

## Troubleshooting

### Backend Issues
- **Import Error**: Ensure all requirements are installed: `pip install -r requirements.txt`
- **API Key Error**: Check that `OPENAI_API_KEY` is set in `.env`
- **Port Conflict**: Backend runs on port 8000, ensure it's available

### Frontend Issues
- **Dependencies**: Run `npm install` if packages are missing
- **Proxy Error**: Ensure backend is running on port 8000
- **Build Error**: Check that all React components are properly imported

### Agent Issues
- **No Questions Generated**: Check API key and internet connection
- **Theme Identification Fails**: Ensure at least 5 seed responses are provided
- **Slow Response**: GPT-4o API calls may take 2-10 seconds

## Next Steps for Development

1. **Database Integration**: Replace in-memory storage with SQLite/PostgreSQL
2. **Authentication**: Add user accounts and family group management  
3. **Voice Recording**: Integrate real speech-to-text functionality
4. **Export Features**: Add PDF, audio, and video export capabilities
5. **Collaboration**: Implement real-time family member assignment and notifications

## Support

For issues with:
- **Agno Framework**: Check [Agno Documentation](https://docs.agno.com)
- **React Components**: Refer to [React Documentation](https://react.dev)
- **API Integration**: Use the built-in API docs at `/docs`

This lean structure provides a solid foundation for experimenting with the Legacy Interview App concept while keeping the codebase manageable and extensible.
