# 🕵️ Local Deep Research Agent

> A focused project built to **explore multi-agent systems with LangGraph**. This experiment orchestrates a team of autonomous agents to test iterative, self-correcting research workflows in a local environment.

## 👋 About The Project

This is a **simple exploration** into how multiple AI agents can collaborate on a single task. Instead of using a single "do-it-all" prompt, this project breaks research down into specialized roles—a Planner, a Researcher, a Reviewer, and a Writer—to see how they handle hand-offs and feedback loops.

The core goal was to test an **Agentic RAG (Retrieval-Augmented Generation)** cycle. Unlike a linear pipeline, this system includes a "Reviewer" gate: if the gathered information isn't good enough, the agent is forced to loop back, refine its strategy, and try again.

It runs entirely **locally** via **Ollama**, which made it easier to iterate on the agent logic without worrying about API costs or data privacy.

---

## 🧠 The Multi-Agent Workflow

The system is built on **LangGraph**, treating the research process as a state machine where each agent is a node in the graph:

1. **Query Generator (Planner)**: Takes the user query and deconstructs it into 3–5 targeted search strings to test different research angles.
2. **Researcher (Executor)**:
* Fetches data using **DuckDuckGo**.
* Scrapes pages via **Jina AI**.
* Explores local indexing by building a **temporary Vector Store (FAISS)** and using **FlashRank** to find the most relevant snippets.


3. **Reviewer (Auditor)**: A logic gate that evaluates if the current findings actually answer the user's question. If gaps are found, it identifies them to guide the next loop.
4. **Writer (Synthesizer)**: The final step that compiles everything into a Markdown report with inline citations.

---

## 💻 Streamlit Implementation

The `app.py` file provides a web interface to visualize how **LangGraph events** unfold in real-time:

* **State Persistence**: Uses `st.session_state` to keep the chat history visible.
* **Process Tracking**: Uses `st.status` to show which agent is currently active, making the multi-agent loop transparent.
* **Event Streaming**: Leverages `graph.stream()` to update the UI as the agents progress through the nodes.

---

## 🛠️ Prerequisites

* **Python 3.10+**
* **Ollama**: Running locally with `qwen3:8b` (logic) and `nomic-embed-text` (embeddings).
* **Jina AI API Key**: For clean Markdown scraping.

---

## 📦 Setup

### 1. Install Dependencies

Instead of manual installation, use the provided requirements file:

```bash
pip install -r requirements.txt

```

### 2. Configure Environment

```bash
export JINA_API_KEY="your_jina_key"

```

### 3. Run the App

```bash
streamlit run app.py

```

---

## 📂 Project Structure

* **`app.py`**: The Streamlit frontend and graph event handler.
* **`graph.py`**: The LangGraph definition and node orchestration.
* **`states.py`**: Pydantic models used for structured communication between agents.
* **`prompts.py`**: System instructions for the different agent roles.
* **`utils.py`**: Search, scrape, and vector indexing utilities.

---

## ⚠️ Notes

* **Iteration Limits**: The Reviewer can sometimes be too picky, leading to multiple loops.
* **Local Latency**: Since everything is local, the embedding and re-ranking steps take time—this is a "slow and steady" research explorer.

---
