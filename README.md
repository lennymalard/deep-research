Here is a summary of the updates I made to your `README.md` to reflect the latest changes in your codebase:

* **Added the Evaluator Agent:** The workflow now includes a 5th agent, the Evaluator (Arbiter), which acts as an anti-hallucination guardrail.
* **Parallel Writing:** Updated the Writer's description to reflect that it now generates multiple candidate reports in parallel for the Evaluator to score.
* **Model Prerequisites:** Added `qwen3:14b` to the Ollama requirements, as it is now used by the Writer and Evaluator classes.
* **UI Updates:** Added the evaluation step to the Streamlit implementation details.

Here is the updated `README.md` content:

# 🕵️ Local Deep Research Agent

> A focused project built to **explore multi-agent systems with LangGraph**. This experiment orchestrates a team of autonomous agents to test iterative, self-correcting research workflows in a local environment.

## 👋 About The Project

This is a **simple exploration** into how multiple AI agents can collaborate on a single task. Instead of using a single "do-it-all" prompt, this project breaks research down into specialized roles—a Planner, a Researcher, a Reviewer, a Writer, and an Evaluator—to see how they handle hand-offs and feedback loops.

The core goal was to test an **Agentic RAG (Retrieval-Augmented Generation)** cycle. Unlike a linear pipeline, this system includes a "Reviewer" gate to force self-correction, and an "Evaluator" to mathematically score and select the best generated response to prevent hallucinations.

It runs entirely **locally** via **Ollama**, which made it easier to iterate on the agent logic without worrying about API costs or data privacy.

---

## 🧠 The Multi-Agent Workflow

The system is built on **LangGraph**, treating the research process as a state machine where each agent is a node in the graph:

1. **Query Generator (Planner)**: Takes the user query and deconstructs it into 3–5 targeted search strings to test different research angles.
2. **Researcher (Executor)**:
   * Fetches data using **DuckDuckGo**.
   * Scrapes pages via **Jina AI**.
   * Explores local indexing by building a **temporary Vector Store (FAISS)** and using **FlashRank** to find the most relevant snippets.
3. **Reviewer (Auditor)**: A logic gate that evaluates if the current findings actually answer the user's question. If gaps are found, it identifies them to guide the next search loop (up to 3 iterations).
4. **Writer (Synthesizer)**: Once research is complete, this node generates *multiple candidate reports in parallel*, compiling findings into structured Markdown with inline citations.
5. **Evaluator (Arbiter)**: A strict verification agent with a zero-tolerance policy for hallucinations. It scores the parallel drafts against the raw source summaries (based on faithfulness, relevance, completeness, etc.) and outputs the highest-scoring final report.

---

## 💻 Streamlit Implementation

The `app.py` file provides a web interface to visualize how **LangGraph events** unfold in real-time:

* **State Persistence**: Uses `st.session_state` to keep the chat history visible.
* **Process Tracking**: Uses `st.status` to show which agent is currently active (Querying ➔ Searching ➔ Reviewing ➔ Drafting ➔ Evaluating), making the multi-agent loop transparent.
* **Event Streaming**: Leverages `graph.stream()` to update the UI as the agents progress through the nodes.

---

## 🛠️ Prerequisites

* **Python 3.10+**
* **Ollama**: Running locally with:
  * `qwen3:8b` (used for logic: Planner, Researcher, Reviewer)
  * `qwen3:14b` (used for generation and strict grading: Writer, Evaluator)
  * `nomic-embed-text` (for FAISS vector embeddings)
* **Jina AI**: Used for clean Markdown scraping (No API key strictly required for basic rate limits, but recommended).

---

## 📦 Setup

### 1. Install Dependencies

Instead of manual installation, use the provided requirements file:

```bash
pip install -r requirements.txt

```

### 2. Run the App

```bash
streamlit run app.py

```

---

## 📂 Project Structure

* **`app.py`**: The Streamlit frontend and graph event handler.
* **`graph.py`**: The LangGraph definition, node orchestration, and parallel routing.
* **`states.py`**: Pydantic models used for structured communication and strict outputs between agents.
* **`prompts.py`**: System instructions, including the strict grading criteria for the Evaluator.
* **`utils.py`**: Search, scrape, and vector indexing utilities.

---

## ⚠️ Notes

* **Local Latency**: Since everything is local, the embedding, re-ranking, and parallel writing steps take time—this is a "slow and steady" research explorer.
