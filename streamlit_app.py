import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RAG Bot", page_icon="📄")
st.title("Chat with your documents")


def error_text(resp):
    """Pull a readable message out of a failed API response."""
    try:
        return str(resp.json().get("detail", resp.text))
    except ValueError:
        return resp.text


def show_sources(sources):
    with st.expander("Sources"):
        for i, s in enumerate(sources, start=1):
            st.markdown(
                f"**[{i}] {s['filename']} - page {s['page']}** "
                f"(distance {s['distance']:.3f})"
            )
            text = s["content"]
            st.caption(text[:500] + ("..." if len(text) > 500 else ""))


# ---------- Sidebar: upload and document list ----------
with st.sidebar:
    st.header("Documents")
    uploaded = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded is not None and st.button("Add to knowledge base"):
        with st.spinner("Reading and indexing the PDF..."):
            try:
                resp = requests.post(
                    f"{API_URL}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=600,
                )
            except requests.exceptions.RequestException:
                st.error("Cannot reach the API. Is it running?")
            else:
                if resp.ok:
                    info = resp.json()
                    st.success(
                        f"Added {info['filename']}: {info['pages']} pages, "
                        f"{info['chunks']} chunks"
                    )
                else:
                    st.error(error_text(resp))

    st.subheader("In the knowledge base")
    try:
        docs = requests.get(f"{API_URL}/documents", timeout=10).json()
        if docs:
            for d in docs:
                st.write(f"• {d['filename']} ({d['chunks']} chunks)")
        else:
            st.caption("No documents yet.")
    except requests.exceptions.RequestException:
        st.warning("API not reachable.")

# ---------- Chat ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])

question = st.chat_input("Ask a question about your documents")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{API_URL}/ask", json={"question": question, "k": 5}, timeout=120
                )
                if resp.ok:
                    data = resp.json()
                    answer, sources = data["answer"], data["sources"]
                else:
                    answer, sources = f"Error: {error_text(resp)}", []
            except requests.exceptions.RequestException:
                answer, sources = "I can't reach the API. Is it running?", []

        st.markdown(answer)
        if sources:
            show_sources(sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )