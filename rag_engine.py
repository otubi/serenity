import uuid
import re
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.tools.tavily_search import TavilySearchResults

# --- API keys and env variables ---
genai.configure(api_key="AIzaSyAr284fbkM5uxKg1m684Rphbt_hqiR4Igs")
os.environ["TAVILY_API_KEY"] = "tvly_live_1n5ceAopUBrM8Tds03bDP6"

# --- Global in-memory chat histories ---
chat_histories = {}

# --- Initialize LLM ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyAr284fbkM5uxKg1m684Rphbt_hqiR4Igs"
)

# --- Vectorstore & embeddings ---
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(
    persist_directory="chroma_db",
    embedding_function=embedding_function
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# --- Prompt templates ---
contextualize_q_system_prompt = """
You are a helpful assistant focused only on student mental health.
Reformulate the user's question to be clear and specific if it relates to student mental health.
If the question is unrelated, say:
"I'm specialized in mental health. Please ask a question related to that."
"""

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a compassionate assistant for university students facing mental health challenges. "
     "Use the context provided to offer helpful, accurate, and supportive answers. "
     "Keep your answer very concise (1-15 sentences) unless otherwise. "
     "At the end, provide 1 or 2 follow-up questions for the user to consider. "
     "Then, provide 4 to 6 suggested quick reply options the user can select from to continue the conversation. "
     "Format your response clearly, for example:\n\n"
     "Answer: <concise answer here>\n"
     "Follow-up questions:\n- Question 1\n- Question 2\n"
     "Suggested replies:\n1. Option A\n2. Option B\n3. Option C\n4. Option D\n\n"
     "Greet the student, joke about love/relationships, and ask light but thoughtful questions. "
     "Only provide answers based on student mental health in Ugandan universities. "
     "Make sure you are as direct as possible while still sounding warm and wise."
    ),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# --- Create chains ---
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

search_tool = TavilySearchResults()

web_search_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a friendly therapist helping university students in Uganda. "
     "Use the search results below to give a warm, concise answer focused on student mental health. "
     "Greet them kindly, make them smile, and give 1-2 follow-up questions and quick replies."),
    ("human", "{context}")
])
fallback_chain = web_search_prompt | llm | StrOutputParser()

# --- Helper functions ---

def is_question_relevant_llm(question: str) -> bool:
    relevance_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Classify this input as one of the following:\n"
         "- 'greeting': if the message is just a polite opener.\n"
         "- 'related': if it’s about student mental health or Ugandan universities.\n"
         "- 'unrelated': if it’s not related.\n"
         "Reply with only one word."),
        ("human", "{input}")
    ])
    chain = relevance_prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"input": question}).strip().lower()
        return result in ["related", "greeting"]
    except Exception as e:
        print(f"[ERROR] Domain classification failed: {e}")
        return False

def parse_llm_response(text: str) -> dict:
    # Defensive parsing; some sections may be missing
    answer_match = re.search(r"Answer:\s*(.*?)\s*(Follow-up questions:|Suggested replies:|$)", text, re.DOTALL | re.IGNORECASE)
    follow_up_match = re.search(r"Follow-up questions:\s*((?:- .+\n?)+)", text, re.IGNORECASE)
    suggested_match = re.search(r"Suggested replies:\s*((?:\d+\. .+\n?)+)", text, re.IGNORECASE)

    answer = answer_match.group(1).strip() if answer_match else text.strip()
    follow_ups = [line.strip("- ").strip() for line in follow_up_match.group(1).strip().splitlines()] if follow_up_match else []
    suggested = [re.sub(r"^\d+\.\s*", "", line).strip() for line in suggested_match.group(1).strip().splitlines()] if suggested_match else []

    return {
        "answer": answer,
        "follow_up_questions": follow_ups,
        "suggested_replies": suggested
    }

def insert_application_logs(session_id: str, question: str, answer: str, model_name: str = "gemini-2.0-flash"):
    print(f"\n[SESSION: {session_id}]")
    print(f"Model: {model_name}")
    print(f"Q: {question}")
    print(f"A: {answer}")

# --- CHAT HISTORY HANDLING ---

def get_chat_history(session_id: str):
    return chat_histories.get(session_id, [])

def add_to_chat_history(session_id: str, role: str, content: str):
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    chat_histories[session_id].append({"role": role, "content": content})

# --- MAIN handler ---

def handle_user_question(session_id: str, question: str) -> dict:
    # Add user question to history
    add_to_chat_history(session_id, "user", question)

    # Check if question is relevant
    if not is_question_relevant_llm(question):
        answer = "I'm specialized in student mental health. Please ask a question related to that domain."
        add_to_chat_history(session_id, "assistant", answer)
        return {
            "full_response": answer,
            "answer": answer,
            "follow_up_questions": [],
            "suggested_replies": [],
            "session_id": session_id,
            "question": question
        }

    chat_history = get_chat_history(session_id)

    try:
        # Call RAG chain with chat history and input question
        result = rag_chain.invoke({
            "input": question,
            "chat_history": chat_history
        })

        full_response = result.get('answer', '').strip()

        # Fallback if response unsatisfactory
        if not full_response or "Sorry" in full_response or len(full_response) < 10:
            search_results = search_tool.invoke({"query": question})
            full_response = fallback_chain.invoke({"context": str(search_results)})

        parsed = parse_llm_response(full_response)
        answer = parsed.get("answer")

        # Add assistant answer to history
        add_to_chat_history(session_id, "assistant", answer)

        response = {
            "full_response": full_response,
            "answer": answer,
            "follow_up_questions": parsed.get("follow_up_questions"),
            "suggested_replies": parsed.get("suggested_replies"),
            "session_id": session_id,
            "question": question
        }
    except Exception as e:
        error_msg = f"An error occurred: {e}"
        add_to_chat_history(session_id, "assistant", error_msg)
        response = {"error": error_msg}

    insert_application_logs(session_id, question, response.get("full_response", ""))
    return response

def handle_suggested_reply(session_id: str, selected_index: int, last_suggested_replies: list) -> dict:
    """
    Given a selected index from suggested replies, treat it as a new user question.
    """
    if 0 <= selected_index < len(last_suggested_replies):
        selected_question = last_suggested_replies[selected_index]
        print(f"\n[INFO] User selected suggested reply: {selected_question}")
        return handle_user_question(session_id, selected_question)
    else:
        return {"error": "Invalid suggested reply selection."}

# --- CLI tester with suggested replies selection ---

if __name__ == "__main__":
    print("✅ rag_engine.py running with chat history enabled")
    session_id = str(uuid.uuid4())
    print(f"Your session id: {session_id}")

    last_suggested_replies = []

    while True:
        question = input("\n💬 Ask me something (or enter number to pick suggested reply): ")

        if question.lower() in ['exit', 'quit']:
            break

        if question.isdigit():
            # If input is digit, treat as selection from suggested replies
            if last_suggested_replies:
                idx = int(question) - 1  # user-facing numbering starts at 1
                response = handle_suggested_reply(session_id, idx, last_suggested_replies)
            else:
                print("No suggested replies to select from. Please type a question.")
                continue
        else:
            response = handle_user_question(session_id, question)

        if "error" in response:
            print("\n❌ Error:", response["error"])
            last_suggested_replies = []
        else:
            print("\n📘 Answer:", response.get("answer"))
            print("🔁 Follow-up Questions:", response.get("follow_up_questions"))
            suggested = response.get("suggested_replies")
            if suggested:
                print("💬 Suggested Replies:")
                for i, option in enumerate(suggested, 1):
                    print(f"  {i}. {option}")
                last_suggested_replies = suggested
            else:
                last_suggested_replies = []
