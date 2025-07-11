from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from rag_engine import handle_user_question
import uuid
import html

app = FastAPI(
    title="Student Mental Health RAG API",
    description="A Gemini-powered API for answering student mental health questions.",
    version="1.0.0"
)

class QuestionRequest(BaseModel):
    question: str
    session_id: str | None = None

@app.get("/", response_class=HTMLResponse)
async def homepage():
    return """
    <html>
        <head>
            <title>Mental Health Assistant</title>
            <style>
                body { margin: 0; font-family: Arial, sans-serif; background: #f0f0f0; }
                .container { display: flex; height: 100vh; }
                .sidebar {
                    width: 250px; background: #2c3e50; color: white; padding: 20px;
                    display: flex; flex-direction: column;
                }
                .sidebar h2 { color: #ecf0f1; font-size: 18px; margin-bottom: 20px; }
                .sidebar a {
                    color: #bdc3c7; text-decoration: none; margin: 10px 0; display: block;
                }
                .sidebar a:hover { color: #1abc9c; }
                .main {
                    flex: 1; padding: 40px;
                }
                .box {
                    max-width: 600px; margin: auto; background: white;
                    padding: 30px; border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                textarea {
                    width: 100%; padding: 10px; font-size: 16px;
                    border-radius: 5px; border: 1px solid #ccc;
                }
                button {
                    padding: 10px 20px; font-size: 16px; background: #007bff;
                    color: white; border: none; border-radius: 5px; cursor: pointer;
                }
                button:hover { background: #0056b3; }
                a.back { display: inline-block; margin-top: 20px; color: #007bff; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="sidebar">
                    <h2>📚 Menu</h2>
                    <a href="/">➕ New Chat</a>
                    <a href="#">🔍 Search Chat</a>
                    <a href="#">📄 Chat List</a>
                </div>
                <div class="main">
                    <div class="box">
                        <h2>🧠 Mental Health Assistant</h2>
                        <p>Ask a question related to student mental health.</p>
                        <form method="post" action="/ask_web" id="questionForm">
                            <textarea id="questionInput" name="question" rows="5" required
                                placeholder="e.g. I'm having trouble sleeping before exams."></textarea><br><br>
                            <button type="submit">Ask</button>
                        </form>
                        <p style="margin-top: 10px;">Developer? Use the <a href="/docs">Swagger UI</a>.</p>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

@app.post("/ask_web", response_class=HTMLResponse)
async def ask_web(question: str = Form(...)):
    session_id = str(uuid.uuid4())
    response = handle_user_question(session_id, question)

    answer = html.escape(response.get("answer", "Sorry, no answer available.")).replace("\n", "<br>")
    follow_ups = response.get("follow_up_questions", [])
    suggested = response.get("suggested_replies", [])

    follow_ups_html = ""
    if follow_ups:
        follow_ups_html = "<div class='follow-ups'><h3>Follow-up questions:</h3><ul>"
        for fq in follow_ups:
            follow_ups_html += f"<li>{html.escape(fq)}</li>"
        follow_ups_html += "</ul></div>"

    suggested_html = ""
    if suggested:
        suggested_html = "<div class='suggested-replies'><h3>Suggested replies:</h3>"
        for i, option in enumerate(suggested, start=1):
            escaped_option = html.escape(option).replace("'", "\\'").replace('"', "&quot;")
            suggested_html += f"<button onclick=\"fillAndSubmit('{escaped_option}')\">{i}. {html.escape(option)}</button> "
        suggested_html += "</div>"

    return f"""
    <html>
        <head>
            <title>Serenity</title>
            <style>
                body {{ margin: 0; font-family: Arial, sans-serif; background: #f9f9f9; }}
                .container {{ display: flex; height: 100vh; }}
                .sidebar {{
                    width: 250px; background: #2c3e50; color: white; padding: 20px;
                    display: flex; flex-direction: column;
                }}
                .sidebar h2 {{ color: #ecf0f1; font-size: 18px; margin-bottom: 20px; }}
                .sidebar a {{
                    color: #bdc3c7; text-decoration: none; margin: 10px 0; display: block;
                }}
                .sidebar a:hover {{ color: #1abc9c; }}
                .main {{
                    flex: 1; padding: 40px;
                }}
                .box {{
                    max-width: 700px; margin: auto; background: white;
                    padding: 30px; border-radius: 10px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.1);
                }}
                a.back {{ display: inline-block; margin-top: 20px; color: #007bff; }}
                .follow-ups {{
                    background: #e0f7e9;  /* Light green background */
                    padding: 15px; border-radius: 8px; margin-top: 20px;
                }}
                .follow-ups h3 {{ margin-top: 0; color: #2e7d32; }}
                .suggested-replies {{
                    margin-top: 25px;
                }}
                .suggested-replies button {{
                    margin: 5px 8px 0 0; padding: 8px 14px;
                    background-color: #007bff; color: white;
                    border: none; border-radius: 5px; cursor: pointer; font-size: 14px;
                }}
                .suggested-replies button:hover {{ background-color: #0056b3; }}
                textarea {{
                    width: 100%; padding: 10px; font-size: 16px;
                    border-radius: 5px; border: 1px solid #ccc; margin-top: 20px;
                }}
                button.ask {{ margin-top: 10px; }}
            </style>
            <script>
                function fillAndSubmit(text) {{
                    const form = document.createElement('form');
                    form.method = 'post';
                    form.action = '/ask_web';

                    const input = document.createElement('textarea');
                    input.name = 'question';
                    input.style.display = 'none';
                    input.value = text;
                    form.appendChild(input);

                    document.body.appendChild(form);
                    form.submit();
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="sidebar">
                    <h2>📚 Menu</h2>
                    <a href="/">➕ New Chat</a>
                    <a href="#">🔍 Search Chat</a>
                    <a href="#">📄 Chat List</a>
                </div>
                <div class="main">
                    <div class="box">
                        <h2>🧠 Question:</h2>
                        <p>{html.escape(question)}</p>

                        <h2>💬 Answer:</h2>
                        <p>{answer}</p>

                        {f'<div class="follow-ups">{follow_ups_html}</div>' if follow_ups_html else ''}
                        {suggested_html}

                        <br><br>
                        <form method="post" action="/ask_web">
                            <textarea name="question" rows="3" required placeholder="Type your own follow-up..."></textarea><br>
                            <button class="ask" type="submit">Ask</button>
                        </form>

                        <br><a class="back" href="/">← Back to home</a>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

@app.post("/ask")
async def ask_api(request: QuestionRequest):
    session_id = request.session_id or str(uuid.uuid4())
    response = handle_user_question(session_id, request.question)
    return {
        "session_id": session_id,
        "question": request.question,
        "answer": response.get("answer"),
        "follow_up_questions": response.get("follow_up_questions"),
        "suggested_replies": response.get("suggested_replies"),
        "full_response": response.get("full_response"),
    }
