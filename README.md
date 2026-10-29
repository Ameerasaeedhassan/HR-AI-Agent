<<<<<<< HEAD
# 🤖 DemoCo HR Copilot — AI Agent

An AI-powered HR assistant built using **Python, LangGraph, Llama 3.2, RAG, and SQLite**.

The project demonstrates how an AI agent can understand HR-related questions, select the appropriate tools, retrieve information from company policies, query employee records, and calculate leave balances.

The system uses fictional company policies and employee data for educational purposes.

## 🛠️ Technologies & Tools

- **Python:** Main programming language for the agent and its tools.
- **Llama 3.2 (3B) + Ollama:** Runs a local LLM for decision-making, tool selection, and evaluating responses.
- **LangGraph:** Manages the agent workflow, tool execution, conversation memory, and decision-making loop.
- **RAG (Retrieval-Augmented Generation):** Retrieves relevant information from HR policy documents instead of relying only on the LLM's knowledge.
- **SQLite:** Stores fictional employee records and supports SQL queries for employee-related information.
- **Leave Calculator:** Calculates remaining paid sick leave using employee leave records.
- **Streamlit:** Web-based chat interface for interacting with the HR assistant.
- **Pydantic:** Validates structured responses and supporting policy evidence.

## 📚 HR Policy Knowledge Base

The RAG system uses five fictional company policy documents:

1. Annual Leave Policy
2. Sick Leave Policy
3. Working Hours Policy
4. Employee Benefits Policy
5. Probation Policy

The policies are divided into searchable sections with unique IDs, such as `AL-02` and `SL-07`.

When an employee asks a policy question, the system retrieves relevant sections and uses the LLM to select supporting evidence. It validates the selected quotations against the original documents and provides section citations.

If a question cannot be answered from the available policies, the assistant reports insufficient information rather than generating an unsupported answer.

## ⚙️ How the AI Agent Works

The agent uses a **LangGraph workflow** to select and execute tools based on the user's question.

- **Policy Tool:** Searches HR policies using RAG and returns verified information with citations.
- **SQL Tool:** Queries the employee database for information such as employee counts, departments, and employment details.
- **Sick Leave Calculator:** Retrieves employee leave information and calculates remaining paid sick leave.
- **Conversation Memory:** Maintains conversation context to handle follow-up questions.
- **Review Node:** Checks whether the executed tools have answered all parts of the user's request.

The agent also handles out-of-scope questions and requests with missing information.

## 🚧 Current Development Status

The core AI agent workflow has been developed, including LangGraph integration, LLM-based tool routing, RAG policy retrieval, SQLite queries, and sick leave calculations.

**Currently working on:**

- Implementing the **annual leave balance calculator** to calculate employees' remaining annual leave days. The general annual leave policy can already be retrieved, but personal annual leave balance calculations are not implemented yet.
- Refining tool selection and response handling for different HR questions.
- Testing the agent with policy, employee-data, and mixed questions.
- Completing the evaluation and remaining fixes to improve reliability and accuracy.

**Project Status:** Under development and testing.

---

*An educational project exploring Agentic AI, tool calling, RAG, and multi-step AI workflows.*
=======
# DemoCo HR Copilot

Educational HR assistant using fictional company policies
and employee data.

## Technology
- Ollama: llama3.2:3b
- LangGraph: agent loop and conversation memory
- RAG: policy retrieval with section citations
- SQLite: employee data
- Streamlit: chat interface

## Status
 Evaluation and remaining fixes are ongoing.
>>>>>>> 5f75f3e2a6a326a8b59ded22f40711899ce28042
