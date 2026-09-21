# Nova AI — Modern Ollama Chatbot

A redesigned local-first chatbot built with **Streamlit + Ollama**.

## What's new

- Modern responsive dark UI
- Clean Nova AI branding
- Welcome / empty-state experience
- Session conversation memory
- Ollama model discovery
- Creativity and max-tool-step controls
- Calculator, date/time, Wikipedia and URL tools
- Tool activity indicators
- Streaming final responses
- Safer calculator implementation (no unrestricted `eval`)
- Better error handling for Ollama connection/model issues
- Mobile-friendly layout

## Project structure

```text
nova-ai/
├── app.py
├── agent.py
├── requirements.txt
└── README.md
```

## Setup

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Ollama and start it:

```bash
ollama serve
```

4. Pull a model, for example:

```bash
ollama pull llama3.2
```

5. Start Nova:

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## Extending it

The `TOOLS` dictionary in `agent.py` is the extension point for adding RAG,
custom APIs, database search, file retrieval, or specialized AI agents.
