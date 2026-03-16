# 🚀 Recruitment AI Automation System

Production-ready modular Python architecture for complete AI-powered recruitment automation.

## 📋 Features

- **Resume Screening**: AI-powered candidate matching against job descriptions
- **Job Description Processing**: Automated JD analysis and multi-platform posting
- **Semantic Matching**: Embeddings-based similarity matching
- **Messaging Agent**: AI-generated recruitment communications (email, WhatsApp, LinkedIn)
- **Interview Management**: Interview scheduling and feedback tracking
- **Candidate Tracking**: Complete candidate lifecycle management
- **Database Integration**: Supabase with vector embeddings support
- **Google Drive Integration**: JD and resume loading
- **n8n Orchestration**: Workflow automation and integration
- **Control Panel Integration**: JSON-based n8n form configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      n8n Workflow Orchestration         │
│   (Control Panel + Automation)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Python Backend (Recruitment AI)        │
│  ┌────────────────────────────────────┐ │
│  │ Agents & Engines                   │ │
│  │ - Screening Agent (GPT-4o)        │ │
│  │ - Messaging Agent (GPT-4o)        │ │
│  │ - Matching Engine (Embeddings)    │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┬──────────────┐
    │          │          │              │
┌───▼──┐  ┌───▼──┐  ┌───▼────┐  ┌──────▼────┐
│Google│  │ Supa │  │ OpenAI │  │  n8n API  │\n│Drive │  │base │  │       │  │ Workflows │\n└──────┘  └──────┘  └────────┘  └───────────┘\n```

## 📁 Project Structure

```
recruitment_ai_system/
├── models/                 # Pydantic data models
│   ├── candidate.py       # Candidate model with skills and experience
│   ├── requirement.py     # Job description model
│   ├── interview.py       # Interview scheduling and feedback
│   ├── selection.py       # Offer and selection tracking
│   ├── screening.py       # Screening results
│   └── messaging.py       # Message generation models
│
├── agents/                # AI Agents
│   ├── screening_agent.py     # Resume-to-JD matching
│   ├── messaging_agent.py     # Message generation
│   └── matching_engine.py     # Semantic similarity matching
│
├── database/              # Database layer
│   └── supabase_client.py # Supabase integration with async support
│
├── integrations/          # External integrations
│   ├── drive_loader.py       # Google Drive JD/Resume loading\n│   └── embedding_engine.py    # OpenAI embeddings\n│\n├── workflows/             # Orchestration\n│   └── n8n_client.py        # n8n workflow triggering\n│\n├── control_panel/         # Control panel integration\n│   └── control_panel_manager.py  # JSON form configuration\n│\n├── utils/                 # Utilities\n│   ├── config.py         # Configuration management\n│   └── logging_config.py # Logging setup\n│\n├── main.py               # Main entry point\n├── requirements.txt      # Dependencies\n└── .env.example          # Environment template\n```\n\n## 🚀 Quick Start\n\n### 1. Installation\n\n```bash\ncd recruitment_ai_system\npip install -r requirements.txt\n```\n\n### 2. Configuration\n\n```bash\ncp .env.example .env\n# Edit .env with your credentials\n```\n\n### 3. Setup Supabase\n\nCreate these tables in Supabase:\n\n```sql\n-- Requirements table\nCREATE TABLE requirements (\n  id UUID PRIMARY KEY,\n  job_title TEXT NOT NULL,\n  client TEXT NOT NULL,\n  jd_text TEXT,\n  required_skills TEXT[] DEFAULT '{}',\n  min_experience FLOAT,\n  status TEXT DEFAULT 'open',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Candidates table\nCREATE TABLE candidates (\n  id UUID PRIMARY KEY,\n  name TEXT NOT NULL,\n  email TEXT NOT NULL,\n  phone TEXT,\n  resume_text TEXT,\n  jd_id UUID REFERENCES requirements(id),\n  status TEXT DEFAULT 'new',\n  total_experience FLOAT,\n  skills TEXT[] DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Screening results table\nCREATE TABLE screening_results (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  overall_score FLOAT,\n  recommendation TEXT,\n  strengths TEXT[] DEFAULT '{}',\n  gaps TEXT[] DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Interviews table\nCREATE TABLE interviews (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  stage TEXT,\n  scheduled_at TIMESTAMP,\n  status TEXT DEFAULT 'scheduled',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Selections table\nCREATE TABLE selections (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  status TEXT DEFAULT 'pending',\n  overall_score FLOAT,\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Embeddings table (for vector search)\nCREATE TABLE embeddings (\n  id UUID PRIMARY KEY,\n  entity_type TEXT,\n  entity_id TEXT,\n  text TEXT,\n  embedding VECTOR(1536),\n  metadata JSONB DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Message history table\nCREATE TABLE message_history (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  platform TEXT,\n  subject TEXT,\n  body TEXT,\n  status TEXT DEFAULT 'pending',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n```\n\n### 4. Setup Google Drive Credentials\n\n1. Create a Google service account\n2. Download credentials JSON\n3. Place in `credentials/google_service_account.json`\n4. Share Google Drive folders with service account email\n\n### 5. Setup n8n (Optional)\n\nFor local n8n instance:\n\n```bash\nnpm install -g n8n\nn8n\n```\n\nThen import workflows and connect with your API key.\n\n## 💻 Usage Examples\n\n### Screen a Candidate\n\n```python\nfrom recruitment_ai_system.main import RecruitmentAISystem\nimport asyncio\n\nasync def main():\n    system = RecruitmentAISystem()\n    \n    result = await system.screen_candidate(\n        candidate_id=\"cand_123\",\n        resume_text=\"John has 5 years Python experience...\",\n        jd_id=\"jd_456\",\n        jd_text=\"We need a senior Python developer with...\"\n    )\n    \n    print(result)\n\nasyncio.run(main())\n```\n\n### Generate a Message\n\n```python\nmessage = await system.generate_message(\n    message_type=\"interview_invite\",\n    tone=\"professional\",\n    platform=\"email\",\n    recipient_name=\"John\",\n    recipient_email=\"john@example.com\",\n    context={\n        \"job_title\": \"Senior Developer\",\n        \"interview_date\": \"2026-02-15\",\n        \"interview_link\": \"zoom_link\"\n    }\n)\n```\n\n### Process Form Submission\n\n```python\nresult = await system.process_form_submission({\n    \"task_type\": \"Screen CV against JD\",\n    \"input_text\": \"CV content here...\",\n    \"context_info\": \"Backend role\"\n})\n```\n\n## 🤖 Agents Overview\n\n### Screening Agent\n- Analyzes resume vs job description\n- Provides matching score (0-1)\n- Identifies skill gaps\n- Recommends interview questions\n- Returns decision (proceed/conditional/reject)\n\n### Messaging Agent\n- Generates personalized messages\n- Supports multiple platforms (Email, WhatsApp, LinkedIn)\n- Offers different tones (Formal, Professional, Friendly)\n- Multi-language capable\n- Platform-specific formatting\n\n### Matching Engine\n- Semantic similarity using embeddings\n- Skill overlap calculation\n- Experience matching\n- Composite scoring\n- Term-based matching\n\n## 🗄️ Database Schema\n\nAll tables include:\n- UUID primary keys\n- Foreign key relationships\n- Audit timestamps (created_at, updated_at)\n- Status fields for workflow tracking\n- JSONB fields for flexible metadata\n\n## 🔗 n8n Integration\n\nThe system automatically triggers n8n workflows for:\n\n1. **Resume Screening Workflow**\n   - Triggered when candidate screening starts\n   - Can add manual review steps\n   - Updates screening results\n\n2. **Messaging Workflow**\n   - Triggered for message generation\n   - Handles email/WhatsApp/LinkedIn sending\n   - Tracks delivery and reads\n\n3. **JD Processing Workflow**\n   - Triggered when new JD is processed\n   - Generates multi-platform job posts\n   - Updates database\n\n## 🔐 Security Considerations\n\n- Store credentials in `.env` (never commit)\n- Use service accounts for Google Drive\n- Enable Supabase RLS (Row Level Security)\n- Validate all input data with Pydantic\n- Log sensitive operations (no passwords/keys in logs)\n- Use HTTPS for API communication\n\n## 📊 Monitoring\n\n- Health checks for all components\n- Structured logging to file and console\n- Execution audit trail\n- Error tracking and notifications\n- Performance metrics\n\n## 🧪 Testing\n\n```bash\npytest tests/ -v\npytest --cov=recruitment_ai_system tests/\n```\n\n## 📈 Scaling\n\n- Async/await throughout for concurrency\n- Batch processing for large candidate lists\n- Vector database for semantic search\n- Connection pooling to Supabase\n- Workflow queueing via n8n\n\n## 🤝 Contributing\n\n1. Create feature branch\n2. Add tests\n3. Format with black\n4. Type checking with mypy\n5. Submit pull request\n\n## 📝 License\n\nProprietary - Recruitment AI System\n\n## 📞 Support\n\nFor API keys and integration help:\n- OpenAI: https://platform.openai.com\n- Supabase: https://supabase.com\n- n8n: https://n8n.io\n- Google Drive API: https://developers.google.com/drive\n\n---\n\n**Built with ❤️ for modern recruitment automation**\n