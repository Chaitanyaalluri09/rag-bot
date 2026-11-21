import os
import tempfile
import uuid

import streamlit as st
from google.genai import errors

from app.config import (
    MAX_PAGES,
    MAX_PDF_MB,
    MAX_QUESTIONS_PER_SESSION,
    SESSION_TTL_HOURS,
)
from app.database import get_connection, init_db, list_documents
from app.embedder import get_model
from app.ingest_service import IngestError, ingest_pdf
from app.rag import answer_question

st.set_page_config(page_title="Chat with your documents", page_icon="📄")
st.title("Chat with your documents")
st.caption("Ask questions about the sample documents, or upload your own PDF.")


@st.cache_resource(show_spinner="Starting up (the first load can take a minute)...")
def warm_up():
    """Runs once per server: create tables and load the embedding model."""
    with get_connection() as conn:
        init_db(conn)
    get_model()
    return True


warm_up()

# ---------- Per-visitor session ----------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state.messages = []
    st.session_state.questions_asked = 0

session_id = st.session_state.session_id


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
    st.info(
        "Text from PDFs you upload is stored in a demo database "
        f"(deleted after {SESSION_TTL_HOURS} hours) and sent to Google's Gemini API "
        "to generate answers. Other visitors can't see your files, but please "
        "**don't upload anything private or confidential.**"
    )

    uploaded = st.file_uploader(
        f"Upload a PDF (up to {MAX_PDF_MB} MB and {MAX_PAGES} pages)", type="pdf"
    )

    if uploaded is not None and st.button("Add to my documents"):
        with st.spinner("Reading and indexing your PDF..."):
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name
                info = ingest_pdf(
                    tmp_path,
                    session_id=session_id,
                    display_name=os.path.basename(uploaded.name)[:100],
                )
            except IngestError as e:
                st.error(str(e))
            except Exception:
                st.error("Something went wrong while processing that file. Please try another PDF.")
            else:
                st.success(
                    f"Added {info['filename']}: {info['pages']} pages, "
                    f"{info['chunks']} chunks"
                )
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

    st.subheader("Available documents")
    try:
        with get_connection() as conn:
            docs = list_documents(conn, session_id)
        if docs:
            for d in docs:
                label = "sample" if d["shared"] else "yours"
                st.write(f"• {d['filename']} ({d['chunks']} chunks, {label})")
        else:
            st.caption("No documents yet. Upload a PDF to begin.")
    except Exception:
        st.warning("Could not load the document list.")

# ---------- Chat ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])

question = st.chat_input("Ask a question about the documents")

if question:
    if len(question) > 1000:
        st.warning("Please keep your question under 1,000 characters.")
    elif st.session_state.questions_asked >= MAX_QUESTIONS_PER_SESSION:
        st.warning(
            f"This demo allows {MAX_QUESTIONS_PER_SESSION} questions per session. "
            "Please try again later."
        )
    else:
        st.session_state.questions_asked += 1
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = answer_question(question, k=5, session_id=session_id)
                    answer, sources = result["answer"], result["sources"]
                except errors.APIError as e:
                    if e.code == 429:
                        answer = (
                            "The demo has reached its free AI usage limit for now. "
                            "Please try again in a few minutes."
                        )
                    else:
                        answer = "The AI service is busy right now. Please try again shortly."
                    sources = []
                except Exception:
                    answer, sources = "Something went wrong. Please try again.", []

            st.markdown(answer)
            if sources:
                show_sources(sources)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )