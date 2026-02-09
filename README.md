<h1 align="center">🏗️ BiblioAI — Autonomous AI Web Project Builder</h1>

<p align="center">
  <strong>From Prompt to Production-Ready Code in Seconds</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/LangGraph-Workflow-FF6F00?logo=langchain&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Groq-LLMs-00D4FF?logo=groq&logoColor=white" alt="Groq"/>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [The Problem](#-the-problem)
- [Our Solution](#-our-solution)
- [Architecture](#-architecture)
- [The 6-Node Pipeline](#-the-6-node-pipeline)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [How It Works](#-how-it-works)
- [Contributing](#-contributing)


---

## 🎯 Overview

**BiblioAI** is an autonomous AI-powered web project builder that transforms natural language descriptions into complete, downloadable web applications. Simply describe your project, and the system intelligently designs, generates, validates, and packages production-ready code—all without human intervention.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔒 **Intelligent Scope Gating** | Classifies requests into HOMEWORK/PRODUCTION/MALICIOUS to ensure platform safety |
| 🏛️ **AI Architecture Design** | Automatically plans file structure, tech stack, features, and design specifications |
| ⚡ **Code Generation** | Generates complete, functional HTML/CSS/JS code using specialized LLMs |
| 🛡️ **Dual Validation Layer** | Both syntax validation (deterministic) and semantic audit (AI-powered) |
| 🔄 **Self-Healing Pipeline** | Automatic retries with targeted fixes when issues are detected |
| 📦 **Instant Packaging** | Delivers downloadable ZIP with all files + comprehensive README |
| 🖥️ **Real-time UI** | Beautiful frontend with live progress tracking and tabbed interface |

---

## 🎯 The Problem

Building web applications typically requires:

1. **Technical Expertise** — HTML, CSS, JavaScript knowledge
2. **Architectural Decisions** — File structure, framework selection
3. **Time Investment** — Hours to days for even simple projects
4. **Quality Assurance** — Manual testing and debugging

**Traditional approaches fail because:**
- AI code generators produce incomplete or non-functional code
- No validation ensures the code actually works
- No intelligent retry mechanisms exist
- Output lacks proper structure and documentation

---

## 💡 Our Solution

BiblioAI solves these problems through a **Human-in-the-Loop (HITL) autonomous pipeline** powered by LangGraph:

```
┌─────────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────────┐    ┌───────────┐
│  Gatekeeper │───►│ Architect │───►│ Approval │───►│ Tech    │───►│  Builder     │───►│ Syntax   │───►│  Auditor     │───►│  Packager │
│   (Filter)  │    │ (Design)  │    │ (Feature)│    │ Stack   │    │ (Code)       │    │ Guard    │    │ (Verify)     │    │ (Deliver) │
└─────────────┘    └───────────┘    └──────────┘    └─────────┘    └──────────────┘    └──────────┘    └──────────────┘    └───────────┘
                                          │               │                 │                  │                  │
                                     (User Edit)      (Generator)           │            (Retry Loop)       (Retry Loop)
                                          │               │                 │                  │                  │
                                          ▼               ▼                 ▼                  ▼                  ▼
                                    [USER APPROVAL] [TECH REVIEW]      [GENERATION]       [VALIDATION]       [AUDITING]
```

### Key Innovations

1. **Human-in-the-Loop Workflow** — You review and approve Features and Tech Stack before a single line of code is written.
2. **Dynamic Structure Generator** — Change your mind about the tech stack? The **Generator** button instantly re-architects the file structure (e.g., swapping `index.html` for `app.py`) based on your input.
3. **Smart Validation** — Dual-layer validation (Syntax + Semantic) ensures code actually runs.
4. **Token-Efficient Retries** — Only regenerates files with specific errors.
5. **Production-Ready Output** — Delivers clean, flat file structures optimized for immediate use.

---

### System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Vanilla HTML/CSS/JS | Modern glassmorphism UI with real-time updates |
| **Backend** | FastAPI + Uvicorn | High-performance async API server |
| **Orchestration** | LangGraph | Stateful workflow with conditional routing |
| **LLM Provider** | Groq Cloud | Ultra-fast inference with multiple models |
| **State Management** | TypedDict | Strongly-typed state object across pipeline |

---

## 🔄 The 7-Node Pipeline

### Node 1: Scope Gatekeeper
**Model:** `llama-3.3-70b-versatile` @ Temperature 0.0

```
Purpose: Protect the system from misuse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ HOMEWORK    → Calculators, To-Do apps, Landing pages, Clones
❌ PRODUCTION  → Full-stack apps, Authentication systems, Payment gateways
❌ MALICIOUS   → Hacking tools, Malware, Exploits
```

**Output:** Classification with confidence score and reasoning

---

### Node 2: The Architect
**Model:** `llama-3.3-70b-versatile` @ Temperature 0.3

```
Purpose: Design the project blueprint (NO CODE!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Project Features    → Core + Enhancement features with benefits
🎨 Design Specs        → Colors, Typography, Layout, Animations
📁 File Structure      → Files to generate with prompts
📦 Asset Manifest      → CDN dependencies
🧠 Reasoning           → Strategic explanation
```

**Tech Stack Options:**
- `html_single` — Single HTML file with embedded CSS/JS
- `html_multi` — Multiple pages with shared stylesheets
- `react_cdn` — React via CDN (only when explicitly requested)
- `vue_cdn` — Vue via CDN (only when explicitly requested)

---

### Node 3: The Builder
**Model:** `openai/gpt-oss-120b` @ Temperature 0.1

```
Purpose: Generate complete, executable code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Follows Architect's blueprint exactly
• Uses only specified CDN libraries
• No placeholders or TODOs
• Full responsive CSS
• Clean, commented JavaScript
```

**Optimization:** On retry, only regenerates files with errors (token savings!)

---

### Node 4: Syntax Guard
**Non-LLM Deterministic Validation**

```
Purpose: Fast syntax validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTML → Tag balance, structure validation
CSS  → Brace matching, semicolon issues
JS   → Minimal checks (comment balance)
```

**Philosophy:** Relaxed validation to avoid false positives; trust the LLM for logic

---

### Node 5: The Auditor
**Model:** `llama-3.3-70b-versatile` @ Temperature 0.2

```
Purpose: Semantic verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Feature completeness
✓ Logic correctness
✓ No hallucinated libraries
✓ Working interactions
✓ User experience quality
```

**Output:** Approval status + detailed issues for retry

---


---

### Node 6: Dependency Analyzer
**Deterministic Rule-Based Engine**

```
Purpose: Integration & Dependency Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Scans code for imports/requires
✓ Generates requirements.txt / package.json
✓ Validates frontend-backend integration
✓ Ensures API calls exist in frontend logic
```

**Output:** Updated file set with dependency files

---

### Node 7: The Packager
**Pure Python**

```
Purpose: Create deliverable
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 All generated code files
📖 Comprehensive README.md
📦 Compressed ZIP archive
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core runtime |
| FastAPI | Latest | Async web framework |
| LangGraph | Latest | Workflow orchestration |
| LangChain-Groq | Latest | LLM integration |
| Pydantic | v2 | Data validation |
| Uvicorn | Latest | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| Vanilla JavaScript | No framework dependencies |
| CSS3 | Glassmorphism design |
| Font Awesome | Icon library |
| Google Fonts | Inter + JetBrains Mono |

### LLM Models (via Groq)
| Role | Model | Temperature |
|------|-------|-------------|
| Gatekeeper | llama-3.3-70b-versatile | 0.0 |
| Architect | llama-3.3-70b-versatile | 0.3 |
| Builder | openai/gpt-oss-120b | 0.1 |
| Auditor | llama-3.3-70b-versatile | 0.2 |

---

## 📁 Project Structure

```
BiblioAI/
├── 📄 README.md                    # This file
├── 📄 .env.example                 # Environment template
├── 🖼️ Builder_Architecture.png     # Architecture diagram
│
├── 🔙 backend/
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 .env                     # Environment variables (create this)
│   │
│   └── 📁 app/
│       ├── 📄 main.py              # FastAPI entry point
│       ├── 📄 config.py            # Pydantic settings
│       │
│       ├── 📁 api/
│       │   └── 📄 routes.py        # API endpoints
│       │
│       ├── 📁 core/
│       │   ├── 📄 graph.py         # LangGraph workflow
│       │   └── 📄 llm_factory.py   # LLM configuration
│       │
│       ├── 📁 models/
│       │   └── 📄 state.py         # BuilderState TypedDict
│       │
│       ├── 📁 nodes/
│       │   ├── 📄 scope_gatekeeper.py
│       │   ├── 📄 architect.py
│       │   ├── 📄 builder.py
│       │   ├── 📄 syntax_guard.py
│       │   ├── 📄 auditor.py
│       │   └── 📄 packager.py
│       │
│       ├── 📁 prompts/
│       │   ├── 📄 gatekeeper_prompts.py
│       │   ├── 📄 architect_prompts.py
│       │   ├── 📄 builder_prompts.py
│       │   └── 📄 auditor_prompts.py
│       │
│       └── 📁 utils/
│           ├── 📄 logger.py
│           └── 📄 parsers.py       # LLM JSON extraction
│
├── 🎨 frontend/
│   ├── 📄 index.html               # Main UI
│   ├── 📄 style.css                # Glassmorphism styles
│   └── 📄 script.js                # Client logic
│
└── 📁 output/                      # Generated ZIP files
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Groq API key ([Get one free](https://console.groq.com))

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/BiblioAI.git
cd BiblioAI
```

**2. Set up the backend**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**3. Configure environment**
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your Groq API key
GROQ_API_KEY=your_api_key_here
```

**4. Start the backend**
```bash
python -m app.main
```

**5. Open the frontend**
```
Open frontend/index.html in your browser
```

**6. Build something amazing!**
```
Enter a prompt like: "Build a todo app with local storage"
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### `POST /build`
Start a new build task.

**Request Body:**
```json
{
  "user_query": "Build a calculator with basic operations",
  "reference_url": null
}
```

**Response:**
```json
{
  "task_id": "uuid-string",
  "message": "Build started successfully",
  "status": "queued"
}
```

---

#### `GET /build/{task_id}/status`
Check build status.

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "processing",
  "current_node": "builder",
  "tech_stack": "html_single",
  "file_structure": [...],
  "project_features": [...],
  "design_specs": {...},
  "is_complete": false
}
```

---

#### `GET /build/{task_id}/stream`
Server-Sent Events for real-time updates.

**Event Format:**
```javascript
data: {"status": "processing", "node": "architect", ...}
```

---

#### `GET /build/{task_id}/download`
Download the generated ZIP file.

**Response:** `application/zip`

---

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Builder Platform"
}
```

---

## ⚙️ Configuration

All settings are managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *required* | Your Groq API key |
| `GATEKEEPER_MODEL` | llama-3.3-70b-versatile | Classification model |
| `ARCHITECT_MODEL` | llama-3.3-70b-versatile | Blueprint design model |
| `BUILDER_MODEL` | openai/gpt-oss-120b | Code generation model |
| `AUDITOR_MODEL` | llama-3.3-70b-versatile | Semantic verification model |
| `BUILDER_COOLDOWN_SECONDS` | 2 | Rate limit between file generations |
| `MAX_RETRY_COUNT` | 2 | Maximum retry attempts |
| `GATEKEEPER_TEMPERATURE` | 0.0 | Deterministic classification |
| `ARCHITECT_TEMPERATURE` | 0.3 | Balanced creativity for design |
| `BUILDER_TEMPERATURE` | 0.1 | Low variance for code |
| `AUDITOR_TEMPERATURE` | 0.2 | Balanced for critique |
| `OUTPUT_DIR` | ./output | Generated files directory |
| `LOG_LEVEL` | INFO | Logging verbosity |

---

## 🧠 How It Works



### Example: Building a Counter App

**1. Init & Analysis**
- You enter: "Build a counter app with increment, decrement, and reset buttons"
- **Gatekeeper** validates the request (Scope: HOMEWORK).

**2. Architect Blueprint & User Approval**
- **Architect** proposes features (Counter Display, Buttons) and Design Specs (Purple gradient).
- **YOU** review these in the "Planning" tab. You can add/remove features or tweak the design.
- **YOU** approve the features.

**3. Tech Stack & Structure Generation**
- System proposes `html_single`.
- **YOU** decide you want Python instead. You type "Python Flask" and click **Generator**.
- **System** automatically updates the file structure to `app.py`, `templates/index.html`, `requirements.txt`.
- **YOU** approve the tech stack.

**4. Code Generation (The Builder)**
- **Builder** generates the actual code based on your approved blueprint.
- Creates `app.py` with Flask routes and `index.html` with Jinja2 templates.

**5. Validation & Audit**
- **Syntax Guard** checks for Python syntax errors and HTML tag balance.
- **Auditor** verifies that the "Reset" button actually works and the UI matches the design specs.

**6. Delivery**
- **Packager** zips everything up.
- You download `project.zip` and run it immediately.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


---

## 🙏 Acknowledgments

- [Groq](https://groq.com) — Lightning-fast LLM inference
- [LangGraph](https://langchain-ai.github.io/langgraph/) — Workflow orchestration
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework

---

<p align="center">
  <strong>Built with ❤️ by the BiblioAI Team</strong>
</p>

<p align="center">
  <em>Transform your ideas into code. No experience required.</em>
</p>
