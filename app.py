"""
CodeLens — Code Explainer Chat UI
Run with: streamlit run app.py
"""

import streamlit as st

from llm_service import ChatService

st.set_page_config(page_title="CodeLens — Code Explainer", page_icon="🔍")
st.title("🔍 CodeLens — Code Explainer")
st.caption("Paste any code snippet and ask me to explain, debug, or improve it.")

# --- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.4, 0.1,
                            help="Lower = more focused, Higher = more creative")
    model = st.selectbox(
        "Model",
        ["gemini-3.1-flash-lite", "gemini-2.0-flash-lite", "gemini-2.0-flash"],
        index=0,
    )
    st.divider()
    if st.button("🗑️ Clear chat"):
        st.session_state.pop("service", None)
        st.session_state.pop("messages", None)
        st.rerun()
    st.divider()
    st.markdown("**Tips:**")
    st.markdown("- Paste code then ask a question\n- Ask to find bugs\n- Ask for improvements")

# --- State ---------------------------------------------------------------------
if "service" not in st.session_state:
    st.session_state.service = ChatService(model=model, temperature=temperature)
if "messages" not in st.session_state:
    st.session_state.messages = []

service: ChatService = st.session_state.service
service.temperature = temperature
service.model = model

# --- Render history ------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle new user turn ------------------------------------------------------
if prompt := st.chat_input("Paste code or ask a question…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reply = st.write_stream(service.stream(prompt))

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --- Token usage ---------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.caption(
        f"**Token usage**\n\n"
        f"Input: {service.total_input_tokens:,}\n\n"
        f"Output: {service.total_output_tokens:,}"
    )
