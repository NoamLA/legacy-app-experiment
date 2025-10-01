# 🚨 PRODUCTION TODO - DO NOT FORGET!

## Critical Items Before Production Deployment

### 🗄️ **#1 PRIORITY: Database Migration**
- [ ] **Switch all agents from InMemoryDb to PostgresDb**
- [ ] **Read and follow `PRODUCTION_DEPLOYMENT.md`**
- [ ] **Update agent initialization in all 4 agent files**
- [ ] **Set `LEGACY_ENV=production`**
- [ ] **Test PostgreSQL connectivity in production**

### 📁 **Files That MUST Be Updated:**
- [ ] `backend/agents/planner_agent.py`
- [ ] `backend/agents/prober_agent.py` 
- [ ] `backend/agents/summarizer_agent.py`
- [ ] `backend/agents/subject_simulator_agent.py`

### 🔧 **Quick Migration Helper:**
Use the smart configuration already created:
```python
# Replace this in all agent files:
from agno.db.in_memory import InMemoryDb
self.db = InMemoryDb()

# With this:
from database.agent_db import get_agent_db
self.db = get_agent_db()
```

### 🎯 **Why This Matters:**
- **InMemoryDb**: Perfect for development, but data is lost on restart
- **PostgresDb**: Required for production, persistent data, multi-user support

### 📋 **Quick Check:**
```bash
python database/agent_db.py  # Test current configuration
```

---
**🔥 CRITICAL: This decision was made during development. PostgreSQL infrastructure is ready, just need to switch agent configuration!**

---
**📅 Last Updated:** October 1, 2025
