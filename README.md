# **DemoCo HR Copilot AI Agent**

An AI-powered HR assistant built with **Python, LangGraph, Llama 3.2, RAG, and SQLite**.

The project demonstrates how an AI agent can interpret HR questions, choose the appropriate tools, retrieve relevant company policies, query fictional employee records, and calculate leave balances. It was developed as an educational project using **fictional policies and employee data only**.

## 🌐 Live Demo

[Try HR AI Copilot](https://gold-adware-piece-christ.trycloudflare.com/)

**Note:** This is a temporary demo link provided through Cloudflare Tunnel. It works only during active testing sessions while Streamlit, Ollama, and the tunnel are running on the host computer. The link may change between sessions.

## Technologies & Tools

- **Python:** Core language for the agent, tools, and data processing.
- **Llama 3.2 (3B) + Ollama:** Runs a local language model for selecting tools and checking whether a request is complete, without requiring a paid external LLM API.
- **LangGraph:** Coordinates the model, tool execution, review loop, and conversation state.
- **RAG (Retrieval-Augmented Generation):** Searches HR policy documents for relevant evidence rather than relying on model knowledge alone.
- **SQLite:** Stores fictional employee records and supports structured employee-data queries.
- **Sick Leave Calculator:** Calculates remaining paid sick leave from recorded employee leave data.
- **Streamlit:** Provides an interactive chat interface for the demo.
- **Pydantic:** Validates structured outputs and supporting policy evidence.

## HR Policy Knowledge Base

The RAG knowledge base contains five fictional policy documents:

1. Annual Leave Policy
2. Sick Leave Policy
3. Working Hours Policy
4. Employee Benefits Policy
5. Probation Policy

Each policy is divided into searchable sections with identifiers such as `AL-02` and `SL-07`. When a user asks a policy question, the retrieval component searches for relevant passages, and Llama 3.2 selects supporting evidence. The system checks quotations against the original text before displaying them with section citations.

If the documents do not support an answer, the assistant reports that the information is unavailable instead of inventing a policy.

## Architecture & Design Decisions

The HR Copilot uses a **modular agent architecture**. Agent orchestration, policy retrieval, employee-data queries, and leave calculations are kept in separate Python modules so the project is easier to test, maintain, and extend.

### Agent Workflow

**Streamlit UI → LangGraph model node → selected tool → review node → verified response**

1. A user submits an HR question through the Streamlit interface.
2. The Llama 3.2 model, called through Ollama's local API, chooses an appropriate action.
3. LangGraph executes the selected tool: policy RAG, employee SQL, or sick leave calculation.
4. The review node checks whether the tool results address the user's full request. If information is still missing, the workflow can return to the model to select another tool.
5. The agent displays the available evidence and answer in the chat interface. Conversation state is maintained using LangGraph's `InMemorySaver`.

### Why This Design?

- **LangGraph** provides explicit control of the model–tools–review loop and supports follow-up questions through conversation state.
- **Local Llama 3.2 via Ollama** lets the project run without a paid external API; it does require Ollama to be running on the host computer.
- **RAG with verified citations** grounds policy answers in the supplied documents and reduces unsupported responses.
- **SQLite and a dedicated SQL tool** keep structured employee-data access separate from policy retrieval.
- **A dedicated calculator** performs deterministic sick leave arithmetic rather than asking the LLM to calculate balances itself.
- **Separate modules** make the agent easier to debug and prepare it for future extensions.
- **Streamlit** provides a lightweight way to demonstrate the system to a reviewer.

## How the AI Agent Works

The agent can use the following components depending on the question:

- **Policy Tool:** Retrieves HR policy passages through RAG and returns source-verified quotations with section references.
- **SQL Tool:** Queries the fictional SQLite employee database for information such as employee counts and department-level data.
- **Sick Leave Calculator:** Uses employee leave records to calculate remaining paid sick leave and show pending days separately.
- **Conversation Memory:** Preserves conversation context to help with follow-up questions.
- **Review Node:** Checks whether all parts of a request have been handled, including requests requiring multiple tools.

The agent also handles out-of-scope questions, missing information, and questions that are not answerable from the provided policies or data.

## Current Development Status

The core LangGraph workflow, local LLM integration, RAG policy retrieval with citations, SQLite querying, sick leave calculation, and Streamlit interface have been implemented.

**Currently working on:**

- Adding a personal **annual leave balance calculator**. General annual leave policy questions already work, but personal annual leave balances are not yet implemented.
- Refining tool selection and response handling across different HR questions.
- Completing an evaluation set of **at least 15 policy, employee-data, and mixed questions**, with recorded results.
- Final testing and documentation updates.

**Project status:** Under development and testing.

---

*An educational project exploring Agentic AI, tool calling, RAG, and multi-step AI workflows.*