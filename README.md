# 🤖 TAMARA - Totally Awesome Modular AI Responsive Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**Intelligent voice assistant with Iron Man style web interface**

[Features](#-features) • [Quick Start](#-quick-start) • [Database Setup](#-database-setup) • [Architecture](#-system-architecture) • [Configuration](#-configuration)

</div>

---

## 📋 Description

TAMARA is a complete voice assistant that integrates speech recognition, artificial intelligence, and voice synthesis, all running locally for maximum privacy and performance.

### ✨ Features

- 🎤 **Continuous Speech Recognition** - Browser Web Speech API
- 🧠 **Local AI** - Ollama with language models running on your machine
- 🔊 **Natural Voice** - Kokoro TTS with Misaki phonemization
- 💬 **Real-time Streaming** - Token by token responses
- 🌐 **Modern Web Interface** - Iron Man design with WebSockets
- ⚙️ **100% Configurable** - Editable YAML file
- 🛠️ **Tool Calling** - Query MariaDB databases with natural language

### 🗄️ Database Query Examples

With MariaDB integration enabled, you can ask TAMARA:

| Question | What it does |
|----------|--------------|
| *"What tables are in the database?"* | Lists all tables |
| *"How many users are there?"* | Counts records in a table |
| *"Describe the products table"* | Shows columns and data types |
| *"What products cost more than $100?"* | Executes query with filter |
| *"Show me pending orders"* | Query with WHERE condition |
| *"Who bought the Logitech Mouse?"* | Query with JOIN between tables |

---

## 🛠️ Technology Stack

### Backend (Python)

| Technology | Purpose |
|------------|---------|
| **FastAPI** | WebSocket and HTTP server |
| **Ollama** | Local language model |
| **Kokoro ONNX** | Fast neural text-to-speech |
| **Misaki** | Spanish phonemizer for TTS |
| **MariaDB** | Relational database for Tool Calling |

### Frontend (Web)

| Technology | Purpose |
|------------|---------|
| **HTML5** | Interface structure |
| **CSS3** | Iron Man styling with animations |
| **JavaScript ES6+** | WebSocket client and UI logic |
| **Web Speech API** | Native browser speech recognition |
| **WebSocket** | Real-time bidirectional communication |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- [eSpeak-NG](https://github.com/espeak-ng/espeak-ng) (for phonemization)
- MariaDB (optional, for database tools)

### Installation

```bash
# Clone the repository
git clone https://github.com/Yungblut/TAMARA-PROJECT
cd TAMARA-PROJECT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Download Ollama model
ollama pull gpt-oss:20b

# Download TTS models from Hugging Face
# Visit: https://huggingface.co/hexgrad/Kokoro-82M/tree/main
# Download these files and place them in kokoro-models/ folder:
#   - kokoro-v1.0.onnx (from "Files and versions" tab)
#   - voices-v1.0.bin  (from "Files and versions" tab)
```

### Running

```bash
python server.py
```

Open http://localhost:8000 in your browser.

---

## 🗄️ Database Setup

### 1. Configure Environment Variables

Copy the example file and edit with your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
TAMARA_DB_HOST=localhost
TAMARA_DB_PORT=3306
TAMARA_DB_USER=tamara_user
TAMARA_DB_PASSWORD=your_secure_password
TAMARA_DB_NAME=tamara_db
```

### 2. Create Database (Optional)

Run the included setup script in MariaDB:

```bash
mysql -u root -p < setup_database.sql
```

This creates sample tables (`users`, `products`, `orders`) with demo data.

### 3. Enable in Configuration

Edit `config.yaml`:
```yaml
database:
  enabled: true
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER                                       │
│                      (Voice / Keyboard)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WEB INTERFACE                                   │
│                 (HTML + CSS + JavaScript)                            │
│  ┌──────────────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│  │ Web Speech API   │  │ WebSocket     │  │ Audio Player          │ │
│  │ (Browser STT)    │  │ Client        │  │ (Base64 WAV)          │ │
│  └──────────────────┘  └───────────────┘  └───────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │ WebSocket (ws://localhost:8000/ws)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON SERVER                                   │
│                       (FastAPI)                                      │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ WebSocket      │  │ LLM Engine     │  │ TTS Engine             │ │
│  │ Handler        │◄─┤ (Ollama)       │  │ (Kokoro + Misaki)      │ │
│  └───────┬────────┘  └───────┬────────┘  └────────────────────────┘ │
│          │                   │                                       │
│          │           ┌───────▼────────┐                              │
│          │           │ Tool Registry  │                              │
│          │           │ ┌────────────┐ │                              │
│          │           │ │ DB Tools   │ │                              │
│          │           │ └────────────┘ │                              │
│          │           └───────┬────────┘                              │
└──────────┼───────────────────┼──────────────────────────────────────┘
           │                   │
           │                   ▼
           │           ┌───────────────┐
           │           │   MariaDB     │
           │           │   Database    │
           │           └───────────────┘
           ▼
    ┌──────────────┐
    │   Browser    │
    │   (Audio)    │
    └──────────────┘
```

---

## 📁 Project Structure

```
TAMARA-PROJECT/
├── server.py              # Main entry point
├── config.yaml            # Application configuration
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
│
├── src/                   # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration module
│   ├── llm_engine.py      # Ollama LLM client with Tool Calling
│   ├── tts_engine.py      # Kokoro TTS engine
│   ├── websocket_handler.py  # WebSocket message handling
│   │
│   └── tools/             # Tool Calling system
│       ├── __init__.py
│       ├── base.py        # Base tool classes
│       ├── registry.py    # Tool registry
│       │
│       └── database/      # Database tools
│           ├── __init__.py
│           ├── client.py  # Secure MariaDB client
│           └── tools.py   # Database tool implementations
│
├── static/                # Static assets
│   ├── css/
│   │   └── styles.css     # Iron Man theme
│   └── js/
│       └── app.js         # Frontend application
│
├── templates/             # HTML templates
│   └── index.html         # Main interface
│
├── kokoro-models/         # TTS models (not in git)
│   ├── kokoro-v1.0.onnx
│   └── voices-v1.0.bin
│
└── docs/                  # Documentation
    └── MCP_USAGE.md       # Database tools guide
```

---

## ⚙️ Configuration

### config.yaml

```yaml
llm:
  model: "gpt-oss:20b"        # Ollama model
  max_history: 500            # Conversation history limit

tts:
  voice: "ef_dora"            # Voice style
  speed: 1.1                  # Speech speed

server:
  host: "0.0.0.0"
  port: 8000

database:
  enabled: false              # Enable MariaDB integration

tools:
  enabled: true               # Enable Tool Calling
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TAMARA_DB_HOST` | MariaDB host | localhost |
| `TAMARA_DB_PORT` | MariaDB port | 3306 |
| `TAMARA_DB_USER` | Database user | root |
| `TAMARA_DB_PASSWORD` | User password | - |
| `TAMARA_DB_NAME` | Database name | - |
| `TAMARA_DB_ALLOW_WRITE` | Allow INSERT/UPDATE | false |
| `TAMARA_LLM_MODEL` | Override LLM model | gpt-oss:20b |

---

## 🔒 Security

- **Read-only by default**: Database tools only allow SELECT queries
- **SQL injection prevention**: Identifier validation and parameterized queries
- **Connection pooling**: Secure connection management
- **Environment variables**: Sensitive data stored outside code

---

## 📝 API Reference

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/api/status` | GET | System status |
| `/api/reset` | POST | Reset conversation |

### WebSocket Messages

**Client → Server:**
```json
{"type": "message", "content": "user message"}
{"type": "ping"}
{"type": "reset"}
```

**Server → Client:**
```json
{"type": "thinking"}
{"type": "token", "content": "response token"}
{"type": "tool_executing", "tool": "tool_name"}
{"type": "audio", "content": "base64_audio"}
{"type": "done"}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ using Ollama, Kokoro, and FastAPI**

</div>
