from flask import Flask, session, request, jsonify
from flask_session import Session
from chatbot import init_faiss, new_chat, process_response


vectordb = init_faiss()
sessions = {}

app = Flask(__name__)

@app.route("/api/chat", methods=["POST"])
def chat():
    userid = request.json.get("userid")
    if userid not in sessions:
        user_context = {}
        user_context["history"] = []
        chain = new_chat(vectordb)
    else:
        user_context = sessions[userid]
        chain = user_context["convo_chain"]

    question = request.json.get("question")
    response = process_response(chain(question))
    data = jsonify({"input": question, "response": response, "history": user_context["history"]})
    
    user_context["history"].append([question, response])
    user_context["convo_chain"] = chain
    sessions[userid] = user_context
    return data

if __name__ == "__main__":
    app.run(debug=True)