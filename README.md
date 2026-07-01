# BizPilot: AI Business Operating System

BizPilot is a production-ready, multi-agent AI Business Operating System powered by Google's Agent Development Kit (ADK). It orchestrates a team of collaborative AI agents to help businesses analyze situations, formulate strategies, and generate detailed executive action plans.

---

## Architecture Overview

BizPilot utilizes a modular, package-based python architecture designed for high scalability, separation of concerns, and ease of testing.

```
BizPilot/
├── .env.example          # Template for environment variables (copy to .env)
├── .gitignore            # Git ignore rules for python packages, cache, and secrets
├── README.md             # Project documentation (this file)
├── requirements.txt      # Python dependencies (google-adk, pydantic, etc.)
│
├── bizpilot/             # Core application package
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Application entrypoint
│   │
│   ├── agents/           # Specialized AI Agent directories
│   │   ├── __init__.py
│   │   ├── core/         # Orchestrator agent
│   │   ├── strategy/     # Business strategy agent
│   │   ├── intelligence/ # Market intelligence agent
│   │   └── growth/       # Growth strategist agent
│   │
│   ├── config/           # Application configuration & settings management
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── memory/           # Agent memory structures (context, persistent logs)
│   │   └── __init__.py
│   │
│   ├── prompts/          # Shared prompt templates and instructions
│   │   └── __init__.py
│   │
│   ├── schemas/          # Data schemas and Pydantic models for structured validation
│   │   └── __init__.py
│   │
│   ├── skills/           # Multi-agent workflows & orchestration logic
│   │   └── __init__.py
│   │
│   ├── tools/            # Shared tools & API integrations
│   │   └── __init__.py
│   │
│   └── utils/            # General shared utility modules (logging, formatting)
│       └── __init__.py
│
├── diagrams/             # Visual architecture and workflow diagrams
│   └── architecture.mermaid
│
└── tests/                # Pytest unit and integration test suite
    ├── __init__.py
    └── test_placeholder.py
```

---

## Directory Descriptions

### 1. `bizpilot/agents/`
Contains the agent logic. In ADK, agents are built as specialized entities with defined roles. To promote modularity, each agent has its own subdirectory:
- **`core`**: The main Orchestrator coordinating task dispatching, routing, and user interaction.
- **`strategy`**: The Business Strategy agent, designed to analyze corporate structures, formulate swot analyses, and suggest direction.
- **`intelligence`**: The Market Intelligence agent, specialized in gathering external data, validating metrics, and performing research.
- **`growth`**: The Growth agent, generating marketing frameworks, customer acquisition strategies, and executive action plans.

Inside each agent directory:
- `agent.py`: Initializer and agent runner using Google ADK `Agent` structures.
- `prompt.md`: Markdown prompt defining instructions, roles, and guidelines.
- `tools.py`: Agent-specific tools used locally by the agent.

### 2. `bizpilot/config/`
Manages application setup and environment variable loading using Pydantic Settings.

### 3. `bizpilot/schemas/`
Houses Pydantic schemas ensuring type-safe and validated inputs and outputs, especially for structured outputs from LLMs.

### 4. `bizpilot/memory/`
Manages session memory, contextual database storage, and semantic RAG vectors.

### 5. `bizpilot/skills/`
Orchestrates agents into pipelines, sequences, and workflows.

### 6. `bizpilot/tools/`
Houses global reusable tools shared across multiple agents.

### 7. `bizpilot/utils/`
Shared internal helpers including logging systems, string formatters, and custom validators.

---

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- A Google Gemini API Key (AI Studio or Vertex AI)

### 1. Clone & Initialize Environment
```bash
# Navigate to project directory
cd Bizpilot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
copy .env.example .env
```
Open `.env` and modify:
```env
GEMINI_API_KEY=AIzaSy...
```

---

## Development & Testing

### Running Tests
To run unit and integration tests, use `pytest`:
```bash
pytest
```

### Code Formatting
Ensure styling guidelines are adhered to before submitting changes:
```bash
black bizpilot tests
flake8 bizpilot tests
```
