# ARIA

**Adaptive Responsive Intelligent Assistant**

ARIA is a personal AI assistant designed to make everyday computer use easier through natural-language interaction, intelligent automation, and system control.

The project is being developed from the ground up with a focus on **online-first operation**, while retaining local AI capabilities for situations where an internet connection is unavailable.

**The main branch of this repo will feature the latest stable release other new branches will be named by their own version with name...**
**You can see the version name in CHANGELOD.md**

## 🚀 Vision

ARIA aims to become a personal computer assistant capable of:

- 🎙️ Understanding voice commands
- 🧠 Reasoning about tasks and choosing appropriate actions
- 🖥️ Controlling applications and system functions
- 📁 Searching and working with local files
- 🌐 Using online services when an internet connection is available
- 📴 Operating with local AI when offline
- ⚙️ Automating repetitive tasks
- 🧠 Remembering useful preferences and context
- 🔐 Asking for confirmation before potentially dangerous actions

## 🌐 Online-First & 📴 Offline Operation

ARIA is designed around an **online-first architecture**.

### Online Mode

When an internet connection is available, ARIA uses cloud-based AI for normal conversation, reasoning, coding, research, and other tasks that benefit from stronger models.

The current online AI stack is based on Google Gemini models, with **Gemini 3.5 Flash-Lite** intended for efficient everyday use and more capable Flash models reserved for harder tasks as the routing architecture develops.

### Offline Mode

When the internet is unavailable, ARIA can fall back to locally running AI models and local system tools.

Current local models include:

- **Gemma 3 1B** — lightweight local AI
- **Qwen 2.5 Coder 7B Instruct** — local coding-oriented AI

The long-term goal is for ARIA to detect connectivity automatically and transition between online and offline capabilities with minimal user involvement.

## 🛠️ Planned Architecture

```text
                         ┌───────────────┐
                         │     User      │
                         │ Voice / Text  │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │     ARIA      │
                         │    Core       │
                         └───────┬───────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │ Intelligent Router  │
                      └──────────┬──────────┘
                                 │
                 ┌───────────────┼────────────────┐
                 ▼               ▼                ▼
          ┌────────────┐  ┌──────────────┐  ┌─────────────┐
          │ ARIA Tools│  │ Online AI    │  │ Offline AI  │
          └────────────┘  │ Gemini Stack │  │ Local Models│
                          └──────┬───────┘  └──────┬──────┘
                                 │                 │
                 ┌───────────────┼─────────┐       │
                 ▼               ▼         ▼       ├── Gemma
              3.5 Lite          3.6       3.7/3.8   └── Qwen

                                 │                 │
                                 └────────┬────────┘
                                          ▼
                                  ┌───────────────┐
                                  │  Tool System  │
                                  ├───────────────┤
                                  │ Files         │
                                  │ Applications  │
                                  │ Browser       │
                                  │ System        │
                                  │ Automation    │
                                  └───────────────┘
```

## 🛠️ Tool System Architecture

ARIA implements a modular, extensible Tool System designed to enable safe system-control capabilities. This system separates tool registration from execution to ensure stability and safety.

### Components

- **Tool Registry (`src/tools/registry.py`)**: Manages tool definitions (name, description, function). It provides validation during registration to reject duplicates, invalid names, or non-callable functions.
- **Tool Dispatcher (`src/tools/dispatcher.py`)**: Responsible for executing registered tools with validated arguments. It enforces a standardized response format (`success`, `tool`, `result`, `error`) and catches runtime errors safely to prevent system crashes or leakages.
- **Basic Tools (`src/tools/basic.py`)**: Contains harmless demonstration tools used for testing the architecture:
  - `get_aria_status`: Returns system operational status.
  - `get_current_session_info`: Returns safe session metadata.
  - `echo_tool`: Echoes input text (length-limited).
  - `calculator_tool`: Safely performs basic math using AST parsing (no `eval()`).

### Safety & Design Guidelines

- **Safety First**: Dangerous operations (shutdown, file deletion, etc.) are currently excluded.
- **Input Validation**: Tools must validate inputs. `calculator_tool` uses a safe AST-based parser instead of `eval()`.
- **Error Handling**: The `ToolDispatcher` wraps execution in try-except blocks, ensuring that failures return a structured error result rather than crashing the application.
- **Extensibility**: New tools can be added easily by defining a function and registering it with the `registry` instance in `src/tools/basic.py` or other modules.

*Note: The Tool System is built for independent testability and is currently being integrated into ARIA's routing logic.*

## 🤖 Model Routing

ARIA is moving from a fixed **Level 1–4 model hierarchy** toward a more flexible **model-routing architecture**.

Instead of assuming that every task belongs to a permanent level, ARIA is being designed to choose the most appropriate backend for the request.

Potential routing targets include:

```text
ARIA_TOOL
GEMINI_3_5_FLASH_LITE
GEMINI_3_6_FLASH
GEMINI_3_7_FLASH
GEMINI_3_8_FLASH
LOCAL_GEMMA
LOCAL_QWEN
```

### Online Model Roles

| Model | Intended role |
|---|---|
| **Gemini 3.5 Flash-Lite** | Default everyday online conversation and efficient tasks |
| **Gemini 3.6 Flash** | More demanding reasoning and technical tasks |
| **Gemini 3.7 Flash** | Advanced reasoning and analysis |
| **Gemini 3.8 Flash** | Highest-capability online Flash tier for the most demanding tasks |

The exact routing policy is still under development. The goal is to use the **simplest model capable of completing a task well**, rather than automatically using the most powerful model for everything.

### Offline Model Roles

Offline models are primarily intended to preserve functionality when cloud AI is unavailable.

- **Gemma 3 1B** — lightweight local fallback and experimentation
- **Qwen 2.5 Coder 7B Instruct** — local coding fallback and experimentation

Online operation remains the preferred path whenever connectivity is available.

## 🔄 Intelligent Routing Philosophy

The router is intended to answer a broader question than simply choosing a "level":

> **What is the best way for ARIA to handle this request?**

For example:

```text
"Open Chrome"
        ↓
ARIA Tool

"Tell me a joke"
        ↓
Gemini 3.5 Flash-Lite

"Explain this difficult concept"
        ↓
Gemini 3.5 Flash-Lite / stronger model as needed

"Solve a highly complex multi-step problem"
        ↓
A more capable Gemini model

No internet connection
        ↓
Local AI fallback
```

A major design principle is that **normal online conversation should not be unnecessarily routed through a small local model first**. Local models should mainly provide offline resilience and specialized fallback capability.

## 🧠 Memory Architecture

ARIA supports session conversation memory and explicit permanent memories stored
locally in SQLite.

Conversation context is stored by ARIA and can be sent to the selected AI backend when required.

Permanent memory is owned by ARIA Core and is not automatically added to normal
conversation prompts. The terminal supports these explicit commands:

- `remember that <key> is <content>`
- `what do you remember about <key>`
- `what do you remember`
- `forget <key>`

The permanent-memory database path can be configured by ARIA Core. Normal
conversation is never saved automatically.

The long-term design separates memory from individual models so that changing the active Gemini model does not mean losing ARIA's conversation context.

Planned memory capabilities include:

- Persistent memory
- Useful preferences
- Long-term context
- Personalization

## 🛡️ Safety Philosophy

ARIA should assist with system operations without having unrestricted control over the computer.

Actions will eventually be divided into different permission levels:

- **Safe:** execute automatically
- **Sensitive:** request confirmation
- **Dangerous:** require explicit authorization or remain unavailable

The goal is to make ARIA powerful **without making it reckless**.

## 📅 Development

ARIA is being developed incrementally, with short development sessions focused on building and testing one capability at a time.

Current and planned development areas include:

- [x] Basic Python project
- [x] Text interaction
- [x] AI integration
- [x] Session conversation memory
- [x] Conversation context sent to Gemini
- [x] Gemini 3.5 Flash-Lite integration
- [x] Local Gemma integration
- [x] Local Qwen integration
- [x] Basic AI-assisted routing prototype
- [ ] Final intelligent model router
- [ ] Reliable online/offline mode switching
- [ ] Web-grounded answers
- [ ] Tool-calling architecture
- [x] Persistent memory
- [ ] Voice input
- [ ] Voice output
- [ ] Application control
- [ ] File searching
- [ ] Browser automation
- [ ] System information tools
- [ ] Safety and permission system
- [ ] Personalization
- [ ] Multi-device support

## 📊 Project Status

| Feature | Status |
|---|---|
| Basic commands | ✅ Implemented |
| Text interaction | ✅ Implemented |
| Gemini integration | ✅ Implemented |
| Gemini 3.5 Flash-Lite | ✅ Implemented |
| API key security | ✅ Implemented |
| Session memory | ✅ Implemented |
| Conversation context | ✅ Implemented |
| Context-aware Gemini responses | ✅ Implemented |
| Gemma 3 1B local AI | ✅ Implemented |
| Qwen 2.5 Coder 7B local AI | ✅ Implemented |
| AI-assisted routing prototype | ✅ Prototype implemented |
| Robust model router | 🚧 In development |
| Gemini 3.6 routing | 🚧 Planned |
| Gemini 3.7 routing | 🚧 Planned |
| Gemini 3.8 routing | 🚧 Planned |
| Persistent memory | ❌ Not yet |
| Web-grounded answers | ❌ Not yet |
| Voice interaction | ❌ Not yet |
| Computer control | ❌ Not yet |

## 💻 Development Environment

ARIA is initially being developed on:

- **OS:** Windows 11
- **Editor:** Visual Studio Code
- **Language:** Python
- **Local inference:** LM Studio
- **Online AI:** Google Gemini API

The project is intended to remain practical on everyday hardware by using local models for offline resilience and cloud models for computationally intensive online tasks.

## 📁 Project Structure

The project is being developed as a modular Python application. The architecture currently separates responsibilities such as:

```text
ARIA/
├── aria.py          # ARIA core and main interaction loop
├── router.py        # Routing and model-selection logic
├── .env             # Local API credentials (not committed)
└── README.md        # Project documentation
```

This structure will expand as ARIA gains dedicated modules for memory, tools, voice, system control, and other capabilities.

## 🔐 API Key Security

ARIA uses environment variables for API credentials.

The local `.env` file is excluded from version control and should **never** be committed to the repository.

## 📜 License

ARIA is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

See [`LICENSE`](LICENSE) for the full license text.

## 🚧 Current Development Direction

The current development focus is the redesign of ARIA's routing architecture.

Earlier development used a fixed four-level structure:

```text
Level 1 → Built-in ARIA tools
Level 2 → Gemma 3 1B
Level 3 → Qwen 2.5 Coder 7B
Level 4 → Gemini 3.5 Flash-Lite
```

Testing showed that this structure does not fully match ARIA's intended **online-first** behavior. The project is therefore evolving toward a model router that can select between ARIA tools, multiple Gemini models, and local fallbacks according to task requirements and connectivity.

This architecture is intentionally being redesigned before the next major implementation step.

## 🎯 Long-Term Goal

ARIA is intended to grow from a command-line AI prototype into a modular personal computer assistant capable of understanding natural-language requests, reasoning about tasks, selecting appropriate tools and models, and safely interacting with the user's devices.

> **Design principle:** Use the simplest capable tool or model for each task, prefer online intelligence when available, and preserve useful functionality when offline.
