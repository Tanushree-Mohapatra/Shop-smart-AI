# 🛒 ShopSmart AI – Agentic Intelligent Shopping Assistant

<div align="center">

![ShopSmart AI](https://img.shields.io/badge/IBM-Hackathon_Project-blue?style=for-the-badge&logo=ibm)
![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=for-the-badge&logo=flask)
![IBM Granite](https://img.shields.io/badge/IBM_Granite-watsonx.ai-blue?style=for-the-badge&logo=ibm)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap)

**Enterprise-grade AI Shopping Assistant powered by IBM Granite, IBM Orchestrate, IBM Langflow & ChromaDB RAG**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [8 AI Agents](#8-ai-agents)
- [IBM Integrations](#ibm-integrations)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [IBM Langflow Workflow](#ibm-langflow-workflow)
- [IBM Orchestrate](#ibm-orchestrate)

---

## 🎯 Overview

ShopSmart AI is an enterprise-grade **Agentic AI Shopping Assistant** that helps users make smarter purchasing decisions. The system uses **8 specialised AI agents** coordinated by an IBM Orchestrate-powered orchestrator, grounded with **ChromaDB Retrieval-Augmented Generation (RAG)**, and driven by **IBM Granite large language models**.

### Key Features

| Feature | Technology |
|---|---|
| Multi-Agent AI | 8 Specialised Agents + IBM Orchestrate |
| LLM | IBM Granite (watsonx.ai) |
| RAG | ChromaDB + sentence-transformers |
| Visual Workflows | IBM Langflow |
| Product Comparison | Side-by-side AI analysis |
| Review Analysis | Sentiment + Fake detection |
| Price Prediction | Historical trends + seasonal forecasting |
| Recommendations | Personalised AI picks |
| Sustainability | Eco scores + carbon impact |
| Multimodal Search | Text + Image + Voice |
| Analytics | Real-time Chart.js dashboard |
| Database | SQLite (14 products, 15 brands, 10 categories) |
| UI | Bootstrap 5 + Dark Mode |

---

## 🏗️ Architecture

```
User Query
    │
    ▼
Intent Detection (IBM Granite)
    │
    ▼
IBM Orchestrate Orchestrator
    │
    ├─── Agent 1: Shopping Knowledge
    ├─── Agent 2: Product Comparison
    ├─── Agent 3: Review Intelligence
    ├─── Agent 4: Price Predictor
    ├─── Agent 5: Recommendations
    ├─── Agent 6: Sustainability
    ├─── Agent 7: Multimodal Search
    └─── Agent 8: Shopping Assistant
              │
              ▼
    RAG Retrieval (ChromaDB)
              │
              ▼
    IBM Granite LLM (watsonx.ai)
              │
              ▼
    Response Formatter
              │
              ▼
    Flask Frontend (Bootstrap 5)
```

---

## 🤖 8 AI Agents

### Agent 1: Shopping Knowledge Agent
- Answers product questions using IBM Granite + RAG
- Explains specs (OLED vs AMOLED, SSD vs HDD, 5G)
- Recommends products based on needs
- **Prompt**: `What is the best laptop for programming?`

### Agent 2: Product Comparison Agent
- Side-by-side product comparison
- Generates pros/cons, best value/premium/budget picks
- Highlights specification differences

### Agent 3: Review Intelligence Agent
- Sentiment analysis (positive/negative/neutral)
- Fake review probability detection
- Customer satisfaction scoring (0-10)
- Common complaint identification

### Agent 4: Predictive Shopping Agent
- 30-day price history visualisation
- Seasonal sale prediction (Indian festival calendar)
- **BUY NOW / WAIT / MONITOR** recommendation
- Price trend charts (Chart.js)

### Agent 5: Recommendation Agent
- Budget, category, brand, purpose-based filtering
- Top 10 personalised picks with AI scoring
- Accessory and bundle recommendations

### Agent 6: Sustainability Agent
- Eco score (1-10), energy efficiency, recyclability
- Carbon footprint estimate (kg CO₂e)
- Green alternatives suggestions
- Brand sustainability commitments

### Agent 7: Multimodal Search Agent
- **Text Search**: Standard product search
- **Image Search**: OCR + IBM Granite Vision (pytesseract)
- **Voice Search**: Web Speech API + SpeechRecognition

### Agent 8: Shopping Assistant Agent
- Conversational AI with persistent chat history
- Uses IBM Granite-13B-Chat model
- Handles: comparisons, pricing advice, gift recommendations

---

## 🔵 IBM Integrations

### IBM watsonx.ai (Granite Models)
```python
# shopping_model.py – Every agent uses this function
from ibm_watsonx_ai.foundation_models import ModelInference

model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    credentials=Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY),
    project_id=WATSONX_PROJECT_ID,
)
response = model.generate_text(prompt=full_prompt)
```

### IBM Langflow
1. Open IBM Langflow
2. Click **Import** → select `langflow_workflow.json`
3. Configure your IBM Granite credentials
4. The full pipeline is visualised as a node graph
5. Test and deploy the workflow

**Langflow Nodes**: User Input → Intent Classifier → IBM Orchestrate → Agent Router → RAG (ChromaDB) → IBM Granite → Response Formatter → Frontend

### IBM Orchestrate
The `orchestrator.py` mirrors IBM Orchestrate's task routing. In production:
- Each agent is a registered **Skill** in IBM Orchestrate
- Orchestrate handles intent-based skill selection
- Multi-skill chaining for complex queries
- Automated workflows (price alerts, weekly deals)

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### 1. Clone & Setup
```bash
git clone <repo-url>
cd shopsmart-ai
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your IBM watsonx.ai credentials
```

### 3. Run the Application
```bash
python app.py
```

Open: [http://localhost:5000](http://localhost:5000)

> **Note**: The app works in **Demo Mode** without IBM watsonx.ai credentials — all agent responses use intelligent mock responses.

---

## ⚙️ Configuration

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
SECRET_KEY=your-flask-secret-key
FLASK_DEBUG=true
PORT=5000
```

---

## 🌐 Flask Pages

| Route | Page |
|---|---|
| `/` | Home – Trending products, hero, quick chat |
| `/assistant` | AI Shopping Assistant (Chat) |
| `/comparison` | Product Comparison (Agent 2) |
| `/reviews` | Review Analyser (Agent 3) |
| `/recommendations` | Personalised Picks (Agent 5) |
| `/predictor` | Price Predictor (Agent 4) |
| `/wishlist` | User Wishlist |
| `/multimodal` | Image/Voice/Text Search (Agent 7) |
| `/dashboard` | Analytics Dashboard |
| `/resources` | Shopping Guides (RAG) |
| `/about` | About & Architecture |
| `/product/<id>` | Product Detail Page |

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | POST | Central orchestrator (all agents) |
| `/api/compare` | POST | Product comparison |
| `/api/reviews/<id>` | GET | Review analysis |
| `/api/predict/<id>` | GET | Price prediction |
| `/api/recommend` | POST | Recommendations |
| `/api/sustainability/<id>` | GET | Eco analysis |
| `/api/search` | POST | Product search |
| `/api/image-search` | POST | Image upload search |
| `/api/voice-search` | POST | Voice search (transcribed text) |
| `/api/wishlist/toggle` | POST | Add/remove wishlist |
| `/api/products` | GET | All products |
| `/api/dashboard` | GET | Dashboard statistics |
| `/api/knowledge` | POST | Shopping knowledge Q&A |

---

## 📁 Project Structure

```
ShopSmart AI/
├── app.py               # Flask application, routes, API endpoints
├── agents.py            # 8 AI agents (Knowledge, Comparison, Review, etc.)
├── orchestrator.py      # Central orchestrator + intent detection
├── database.py          # SQLite schema, seed data, query helpers
├── rag.py               # ChromaDB RAG implementation
├── shopping_model.py    # IBM watsonx.ai Granite integration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── langflow_workflow.json  # IBM Langflow workflow definition
├── README.md            # This file
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base layout (navbar, footer, dark mode)
│   ├── home.html        # Landing page
│   ├── assistant.html   # Chat interface
│   ├── comparison.html  # Product comparison
│   ├── reviews.html     # Review analysis
│   ├── recommendations.html
│   ├── predictor.html   # Price predictor
│   ├── wishlist.html
│   ├── multimodal.html  # Image/voice/text search
│   ├── dashboard.html   # Analytics dashboard
│   ├── resources.html   # Shopping guides
│   ├── about.html       # Architecture info
│   ├── product_detail.html
│   └── error.html
├── static/
│   ├── css/style.css    # Custom CSS (Bootstrap 5 theme)
│   ├── js/app.js        # Global JavaScript utilities
│   └── uploads/         # Image upload directory
├── dataset/
│   └── README.txt       # Dataset documentation
└── instance/
    ├── shopsmart.db     # SQLite database (auto-created)
    └── chroma_store/    # ChromaDB vector store (auto-created)
```

---

## 🎖️ IBM Hackathon Highlights

✅ **IBM Granite Models** – All 8 agents use `ibm/granite-3-8b-instruct`  
✅ **IBM Langflow** – Complete workflow JSON for visual pipeline  
✅ **IBM Orchestrate** – Agent coordination & skill registration  
✅ **RAG with ChromaDB** – 17 knowledge documents indexed  
✅ **Multi-Agent Architecture** – 8 specialised independent agents  
✅ **Enterprise-Ready** – Modular, OOP, error handling, logging  
✅ **Production UI** – Bootstrap 5, Dark Mode, Chart.js visualisations  

---

## 📊 Technologies

- **Backend**: Python 3.11, Flask 3.0, SQLite
- **AI/ML**: IBM watsonx.ai Granite, ChromaDB, sentence-transformers
- **Frontend**: Bootstrap 5.3, JavaScript ES6, Chart.js 4
- **Vision/Speech**: Pillow, pytesseract, SpeechRecognition
- **Workflows**: IBM Langflow, IBM Orchestrate

---

<div align="center">
  <strong>Built for IBM Hackathons • IBM SkillsBuild • Enterprise AI Showcases</strong>
  <br/>
  <em>Powered by IBM Granite & watsonx.ai</em>
</div>
