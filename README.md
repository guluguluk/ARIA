# ARIA

**Adaptive Responsive Intelligent Assistant**

ARIA is a personal AI assistant designed to make everyday computer use easier through natural-language interaction, intelligent automation, and system control.

The project is being developed from the ground up with a focus on **online and offline operation**, allowing ARIA to remain useful even when an internet connection isn't available.

## 🚀 Vision

ARIA aims to become a personal computer assistant capable of:

* 🎙️ Understanding voice commands
* 🧠 Reasoning about tasks and choosing appropriate actions
* 🖥️ Controlling applications and system functions
* 📁 Searching and working with local files
* 🌐 Using online services when an internet connection is available
* 📴 Operating with a local AI when offline
* ⚙️ Automating repetitive tasks
* 🧠 Remembering useful preferences and context
* 🔐 Asking for confirmation before potentially dangerous actions

## 🌐 Online & 📴 Offline Modes

ARIA is designed around two operating modes:

### Online Mode

When an internet connection is available, ARIA can use more powerful cloud-based AI capabilities for complex tasks such as research, reasoning, and online services.

### Offline Mode

When the internet is unavailable, ARIA can fall back to locally running AI models and local system tools.

The goal is for the transition between these modes to be automatic and seamless.

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
                 │  AI Assistant │
                 └───────┬───────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       ┌─────────────┐       ┌─────────────┐
       │ Online Brain│       │Offline Brain│
       │ Cloud AI    │       │ Local AI    │
       └──────┬──────┘       └──────┬──────┘
              │                     │
              └──────────┬──────────┘
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

## 📅 Development

ARIA is being developed incrementally, with small development sessions focused on building one capability at a time.

The initial development goals include:

* [ ] Basic Python project
* [ ] Text interaction
* [ ] AI integration
* [ ] Voice input
* [ ] Voice output
* [ ] Application control
* [ ] File searching
* [ ] Browser automation
* [ ] System information
* [ ] Tool-calling architecture
* [ ] Online/offline mode switching
* [ ] Local AI integration
* [ ] Memory system
* [ ] Safety and permission system
* [ ] Personalization

## 💻 Development Environment

ARIA is initially being developed on:

* **OS:** Windows 11
* **Editor:** Visual Studio Code
* **Language:** Python

The project is intended to remain lightweight enough to run on everyday hardware while using cloud resources for computationally intensive tasks when appropriate.

## 🔐 Safety Philosophy

ARIA should assist with system operations without having unrestricted control over the computer.

Actions will eventually be divided into different permission levels:

* **Safe:** execute automatically
* **Sensitive:** request confirmation
* **Dangerous:** require explicit authorization or remain unavailable

The goal is to make ARIA powerful **without making it reckless**.

## 🧠 ARIA's Multi-Level Intelligence Architecture

ARIA is designed around a multi-level intelligence architecture. Instead of sending every request to the most powerful AI model, ARIA determines the appropriate level of intelligence required for each task.

This approach is designed to improve efficiency, reduce unnecessary API usage, support offline operation, and allow ARIA to use different AI systems for different types of tasks.

### Architecture

```text
User Input
    ↓
Intelligent Router
    ↓
┌─────────────────────────────────────────────┐
│                                             │
│  Level 1 → Built-in ARIA Tools              │
│  Level 2 → Local AI (Qwen)                  │
│  Level 3 → Gemini 3.5 Flash-Lite            │
│  Level 4 → Advanced Gemini Reasoning        │
│  Level 5 → Highest-Capability AI / Complex  │
│                                             │
└─────────────────────────────────────────────┘
    ↓
ARIA Response / Action
```

### Level 1 — Built-in Intelligence

Handles simple, deterministic tasks without requiring an AI model.

Examples:
- Basic commands
- Application launching
- System controls
- Simple calculations
- File and folder operations
- Other deterministic tools

**Goal:** Complete simple tasks instantly without using an AI model.

---

### Level 2 — Local AI

Uses two (uses as per the needs) locally running AI model such as **Qwen and Gemma** through a local inference system.

Examples:
- Coding assistance
- Explanations
- General questions
- Offline conversations
- Tasks that do not require current information

**Goal:** Provide useful AI capabilities even when ARIA is offline.

---

### Level 3 — Efficient Online AI

Uses **Google Gemini 3.5 Flash-Lite** for general online AI tasks.

Examples:
- Natural conversations
- General knowledge
- Writing and summarization
- More complex questions
- Multilingual interactions

**Goal:** Handle everyday AI tasks efficiently while keeping API usage economical.

---

### Level 4 — Advanced Reasoning

Uses a more capable online AI model when a task requires stronger reasoning or analysis.

Examples:
- Complex programming problems
- Multi-step reasoning
- Detailed technical analysis
- Difficult problem solving

**Goal:** Use additional computational capability only when the task actually requires it.

---

### Level 5 — Maximum Intelligence

Reserved for the most demanding tasks that require ARIA's highest available reasoning capability.

Examples:
- Highly complex technical problems
- Large multi-step tasks
- Advanced analysis
- Difficult planning and reasoning

**Goal:** Provide maximum capability when lower levels are insufficient.

---

### 🤖 Intelligent Model Routing

A key part of ARIA's architecture is its planned intelligent routing system.

Instead of manually selecting a model, ARIA will analyze the user's request and determine the appropriate processing level.

For example:

> "Open Chrome"

→ **Level 1**

> "Write a Python program"

→ **Level 2**

> "Explain this complicated concept"

→ **Level 3**

> "Solve this difficult programming problem"

→ **Level 4**

> "Perform a highly complex multi-step analysis"

→ **Level 5**

The routing system is designed to eventually use a lightweight local model such as **Gemma** as a dedicated routing/classification model.

This creates an architecture where one AI system can determine which AI system or tool should handle the task.

### 🔄 Online / Offline Intelligence

ARIA is designed to operate in both online and offline environments.

**Online Mode**
- Gemini-based intelligence
- Current information through external tools
- Advanced reasoning
- Online services

**Offline Mode**
- Local Qwen model
- Local tools
- Local files and system control
- No internet dependency for supported tasks

ARIA can therefore choose between local and online intelligence depending on the task and available connectivity.

> **Design principle:** Use the simplest capable level for each task rather than using the most powerful model for everything.

📊 ARIA — Project Status

| Feature                             | Status    |
| ----------------------------------- | --------- |
| Basic commands                      | ✅         |
| Gemini integration                  | ✅         |
| Gemini 3.5 Flash-Lite               | ✅         |
| API key security                    | ✅         |
| Session memory storage              | ✅         |
| Conversation context sent to Gemini | ✅         |
| Context-aware responses             | ✅         |
| Persistent memory                   | ❌ Not yet |
| Web-grounded answers                | ❌ Not yet |
| Offline Qwen                        | ❌ Not yet |

Local AI Integration ✅
Gemma 3 1B is now integrated into ARIA as Level 2, with the router successfully directing suitable tasks to the local model. BTW Qwen not yet integrated and will be integrated tomorrow.

That gives ARIA:

Level 1 → Built-in tools

Level 2 → Gemma 3 1B (local/offline) and Qwen 2.5 Coder 7B Instruct (Not Yet Integrated)

Online → Gemini 3.5 Flash-Lite
