import streamlit as st
import uuid
import os

from langchain_chroma import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

from rag_engine import handle_user_question, get_chat_history, insert_application_logs, create_application_logs

# -- Load vectorstore from local folder
@st.cache_resource(show_spinner="Loading vectorstore...")
def load_vectorstore():
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(
        collection_name="my_collection",
        embedding_function=embedding_function,
        persist_directory="vector_db"  # path to your local chroma_db
    )
    return vectorstore

# Sidebar: Reload Vectorstore Option
if st.sidebar.button("🔄 Reload Vectorstore"):
    st.cache_resource.clear()
    st.experimental_rerun()

# Initialize logging DB
create_application_logs()

# Load the vectorstore and retriever
vectorstore = load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Session Management
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state["chat_history"] = []

# UI Title
st.title("🎓 Student Mental Health Chatbot")

# User input
user_input = st.chat_input("Ask me anything about student mental health...")

if user_input:
    response = handle_user_question(
        session_id=st.session_state["session_id"],
        user_input=user_input,
        retriever=retriever  # Pass retriever to RAG engine
    )
    st.session_state["chat_history"].append(("You", user_input))
    st.session_state["chat_history"].append(("AI", response))

# Display Chat History
for role, message in st.session_state["chat_history"]:
    if role == "You":
        st.markdown(f"**🧑 {role}:** {message}")
    else:
        st.markdown(f"**🤖 {role}:** {message}")
