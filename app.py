"""Local Streamlit interface for the existing HR Copilot agent.
Run from the project folder: python -m streamlit run app.py
"""
import logging
import json
import re
import time
from uuid import uuid4

import streamlit as st

from hr_agent import HRAgent
from sql_tool import query_employee_data

st.set_page_config(page_title="DemoCo HR Copilot", page_icon="💬", layout="centered")


st.markdown("""
<style>
:root {color-scheme: dark;}
[data-testid="stAppViewContainer"] {
 background: radial-gradient(ellipse at 75% 0%, #29203f 0%, transparent 50%),
 linear-gradient(150deg, #10121b, #121c29) !important; color: #e9edf6 !important;
}
[data-testid="stHeader"] {background: transparent !important;}
[data-testid="stMainBlockContainer"] {max-width: 960px; padding-top: 2.7rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {background: #11141f !important; border-right: 1px solid #2a2e40;}
[data-testid="stSidebarUserContent"] {padding-top: 2.1rem;}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stWidgetLabel"] p {color: #e1e6f1 !important;}
[data-testid="stCaptionContainer"] p {color: #a9b3c9 !important; font-size: .82rem;}
h1,h2,h3 {color: #f1f3fa !important;}
.brand {font-size: .75rem; letter-spacing: .18em; color: #b6a0f8; font-weight: 700; margin-bottom: 1.5rem;}
.hero {padding: 1.4rem 0 1.6rem;}
.hero h1 {font-size: clamp(2rem, 4vw, 2.8rem); letter-spacing: -.045em; line-height: 1.15; margin: 0 0 .9rem; padding: 0;}
.hero p {color: #aab6cb !important; font-size: 1rem; max-width: 520px; line-height: 1.7;}
.eyebrow {font-size: .68rem; letter-spacing: .13em; font-weight: 600; color: #a0acc2; margin: 1.7rem 0 .8rem;}
[data-testid="stChatMessage"] {background: #1b2132 !important; border: 1px solid #343a51; border-radius: 16px; padding: 1.2rem; margin-bottom: 1rem;}
[data-testid="stChatMessage"] p {line-height: 1.8;}
[data-testid="stChatMessage"] strong {color: #d4c4ff !important;}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"] {
 background: #20273a !important; border-color: #4a536c !important; border-radius: 16px !important;
 color: #f1f3fa !important;
}
[data-testid="stChatInput"] textarea {background: transparent !important; color: #f1f3fa !important; caret-color: #c9b4ff;}
[data-testid="stChatInput"] textarea::placeholder {color: #aeb9cf !important; opacity: 1;}
[data-testid="stChatInput"]:focus-within {outline: 2px solid #9e88d6; outline-offset: 2px;}
[data-testid="stChatInputSubmitButton"] {background: #aa91eb !important; color: #141020 !important; border-radius: 10px;}
[data-testid="stChatInput"] svg {fill: currentColor;}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
 background: #202638 !important; color: #edf1fa !important; border-color: #41485f !important; border-radius: 10px;
}
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] input {color: #edf1fa !important;}
[data-baseweb="popover"], [role="listbox"], [role="option"] {background: #202638 !important; color: #edf1fa !important;}
[data-testid="stButton"] button {background: #22283a !important; color: #edf1fa !important; border: 1px solid #3c455e !important; border-radius: 12px; min-height: 3rem; text-align: left;}
[data-testid="stButton"] button p {color: #edf1fa !important; font-size: .87rem;}
[data-testid="stButton"] button:hover {background: #302c48 !important; border-color: #aa91eb !important;}
[data-testid="stSidebar"] [data-testid="stButton"] button {background: #a58bdd !important; width: 100%;}
[data-testid="stSidebar"] [data-testid="stButton"] button p {color: #160e28 !important; font-weight: 600;}
[data-testid="stExpander"] {background: #191f2f !important; border-color: #353c51 !important; color: #dce3f3 !important;}
[data-testid="stExpander"] summary p {color: #bfc9de !important;}
@media (max-width: 640px) {[data-testid="stMainBlockContainer"] {padding-top: 1.2rem;} .hero {padding-top: .7rem;}}
[data-testid="stChatMessageAvatarAssistant"] {background: #36d6be !important; color: #062b27 !important;}
[data-testid="stChatMessageAvatarUser"] {background: #9a83d6 !important; color: #1b1231 !important;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {border-left: 3px solid #36d6be; background: linear-gradient(120deg, #162c31, #1b2132 65%) !important;}
[data-testid="stBottom"], [data-testid="stBottom"] > div {background: #121925 !important;}
[data-testid="stMainBlockContainer"] {padding-bottom: 7rem;}
</style>
""", unsafe_allow_html=True)


def new_conversation():
    """Discard the old graph as well as the visible conversation."""
    old_agent = st.session_state.pop("hr_agent", None)
    if old_agent is not None:
        old_agent.close()
    st.session_state.thread_id = str(uuid4())
    st.session_state.chat_messages = []
    st.session_state.department_picker = False


def format_employee_count(question, answer):
    """Presentation-only compatibility for older agent SQL responses.

    The agent still chooses/runs SQL. Read its numeric result; never supply
    a hardcoded count. Only the department-count question is reformatted.
    """
    match = re.fullmatch(
        r"\s*How many employees work in (?:the )?(.+?) department\?\s*",
        question, re.IGNORECASE,
    )
    prefix = 'Employee database result:'
    if not match or not answer.lstrip().startswith(prefix):
        return answer
    try:
        payload, _ = json.JSONDecoder().raw_decode(
            answer.lstrip()[len(prefix):].lstrip()
        )
        if (payload.get('columns') != ['employee_count']
                or payload.get('truncated') is not False
                or payload.get('row_count') != 1):
            return answer
        rows = payload['rows']
        if len(rows) != 1 or len(rows[0]) != 1:
            return answer
        count = rows[0][0]
        if type(count) is not int or count < 0:
            return answer
        verb, noun = ('is', 'employee') if count == 1 else ('are', 'employees')
        sentence = f'There {verb} {count} {noun} in the {match.group(1)} department.'
        # Preserve real execution-limit notices, not the obsolete unrelated
        # clarification that older versions appended to the Sources section.
        if 'The agent reached its decision limit' in answer:
            sentence += '\n\nThe agent reached its decision limit; additional requested information may be incomplete.'
        return sentence
    except (ValueError, KeyError, TypeError, IndexError, AttributeError):
        return answer


def show_message(message):
    with st.chat_message(message["role"]):
        # Preserve the agent's answer and citations without another LLM rewrite.
        content, limit_marker, limit_note = message["content"].partition("\nThe agent reached")
        body, separator, sources = content.partition("\n\nSources:\n")
        st.markdown(body)
        if separator:
            with st.expander("References"):
                st.markdown(sources)
        if limit_marker:
            st.warning("The agent reached" + limit_note)


if "thread_id" not in st.session_state:
    new_conversation()

st.markdown('<div class="brand">DEMOCO / PEOPLE &amp; WORK</div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Your HR questions.</h1><p>Check your leave balance, explore company policies, or ask about your team.</p></div>', unsafe_allow_html=True)

try:
    employees = query_employee_data(
        "SELECT employee_id, full_name FROM employees ORDER BY employee_id"
    )["rows"]
except Exception:
    logging.exception("Unable to load demo employee selector")
    st.error("Could not load employees. Check that data/employees.db exists and sql_tool.py works.")
    st.stop()

if not employees:
    st.error("The employee database contains no employees.")
    st.stop()

labels = {row[0]: f"{row[0]} — {row[1]}" for row in employees}
with st.sidebar:
    st.subheader("HR Copilot")
    st.caption("Your company knowledge, in one place.")
    employee_id = st.selectbox(
        "Demo employee", options=list(labels), format_func=labels.get,
        key="demo_employee", on_change=new_conversation,
    )
    st.caption("Switching employees starts a fresh chat.")
    st.button("New conversation", on_click=new_conversation)
    
    st.divider()
    st.caption("Educational prototype • Fictional company policies and employee records.")
    with st.expander("About this demo"):
        st.write("The employee selector is not a sign-in. Conversation history lasts for this browser session and may reset on refresh.")
        st.write("Out-of-scope classification still needs improvement. Personal annual-leave balances are not implemented yet.")

suggested = None
if not st.session_state.chat_messages:
    st.markdown('<div class="eyebrow">START WITH A QUESTION</div>', unsafe_allow_html=True)
    columns = st.columns(3)
    prompts = [
        ("My sick-leave balance", "How many paid sick leave days do I have left?"),
        ("Annual leave notice", "How early should I request annual leave?"),
        ("People in my company", None),
    ]
    for column, (label, prompt) in zip(columns, prompts):
        if column.button(label, use_container_width=True):
            if prompt is None:
                st.session_state.department_picker = True
                st.session_state.chat_messages.extend([
                    {"role": "user", "content": "People in my company"},
                    {"role": "assistant", "content": "Which department would you like to check? Choose below to see its employee count."},
                ])
                st.rerun()
            suggested = prompt
    st.write("")

previous_question = ''
for message in st.session_state.chat_messages:
    if message['role'] == 'user':
        previous_question = message['content']
    else:
        message = {**message, 'content': format_employee_count(previous_question, message['content'])}
    show_message(message)

if st.session_state.get("department_picker"):
    try:
        department_rows = query_employee_data(
            "SELECT DISTINCT department FROM employees WHERE department IS NOT NULL ORDER BY department"
        )["rows"]
        departments = [row[0] for row in department_rows]
        if not departments:
            st.info("No departments were found in the employee database.")
        else:
            with st.form("department_choice"):
                department = st.selectbox("Department", ["All departments"] + departments)
                submitted = st.form_submit_button("Show employee count")
            if submitted:
                suggested = (
                    "How many employees work in each department?"
                    if department == "All departments"
                    else f"How many employees work in the {department} department?"
                )
                st.session_state.department_picker = False
    except Exception:
        logging.exception("Department lookup failed")
        st.error("Could not load department choices from the employee database.")

# Top-level chat_input is pinned by Streamlit; nesting it makes it scroll.
typed_question = st.chat_input("What would you like to know?", max_chars=2000)
question = typed_question or suggested
if question and question.strip():
    question = question.strip()
    st.session_state.department_picker = False
    user_message = {"role": "user", "content": question}
    st.session_state.chat_messages.append(user_message)
    show_message(user_message)
    started = time.perf_counter()
    try:
        with st.spinner("Your HR Copilot is working. Local responses may take a while…"):
            if "hr_agent" not in st.session_state:
                st.session_state.hr_agent = HRAgent()
            result = st.session_state.hr_agent.ask(
                question, employee_id, st.session_state.thread_id
            )
            answer = format_employee_count(question, result["answer"])
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Agent returned no answer")
    except Exception:
        logging.exception("HR Copilot request failed")
        answer = (
            "The request could not be completed. Check the terminal for details "
            "and confirm that Ollama is running. Start a new conversation before retrying."
        )
    assistant_message = {
        "role": "assistant", "content": answer,
        "seconds": time.perf_counter() - started,
    }
    st.session_state.chat_messages.append(assistant_message)
    st.rerun()
