## Nova AI — Local AI Agent & Chatbot

A modern local-first AI chatbot and agent application built with **Python, Streamlit, and Ollama**.

## 📘 Overview

Nova AI is a local AI assistant that allows users to interact with Large Language Models (LLMs) running through Ollama.

The project combines a modern Streamlit interface with an AI agent architecture that can use built-in tools when required. It supports streaming responses, session-based conversation memory, Ollama model selection, configurable creativity, and configurable tool execution steps.

The agent can perform calculations, retrieve date and time, search Wikipedia, and fetch readable content from public URLs.

## ✨ Key Features

- Modern responsive dark UI
- Nova AI branding
- Local LLM execution through Ollama
- Session-based conversation memory
- Ollama model discovery and selection
- Streaming AI responses
- Creativity / temperature control
- Maximum tool-step control
- Calculator tool
- Date/time tool
- Wikipedia search tool
- Public URL content retrieval
- Tool activity indicators
- Ollama connection status
- Session statistics
- New chat functionality
- Error handling for Ollama and tool failures
- Safer calculator implementation without unrestricted `eval()`

## 🛠️ Technologies Used

- Python 🐍
- Streamlit
- Ollama
- Requests
- REST APIs
- JSON
- Python AST
- HTML text processing

## 🤖 AI / LLM

- **LLM Runtime:** Ollama
- **Model:** User-selected local Ollama model
- **Default Example Model:** Llama 3.2
- **API:** Ollama local chat API
- **Response Type:** Streaming


## Setup

1. Install Python 3.10+.
2. Install dependencies:

 pip install -r requirements.txt


3. Install Ollama and start it:

 ollama serve


4. Pull a model, for example:

 ollama pull llama3.2


5. Start Nova:

streamlit run app.py


Open the local Streamlit URL shown in the terminal.

## Extending it

The TOOLS dictionary in agent.py is the extension point for adding RAG,
custom APIs, database search, file retrieval, or specialized AI agents.
