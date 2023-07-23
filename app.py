from flask import Flask, session, request, jsonify, make_response
from flask_session import Session
from chatbot import init_base_context, init_faiss, new_chat, process_response


vectordb = init_faiss()
llm, template = init_base_context()
sessions = {}

app = Flask(__name__)




@app.route("/chat")
def chat():
    userid = request.args.get("userid")
    if userid not in sessions:
        user_context = {}
        user_context["convo_chain"] = new_chat(vectordb, llm, template)
        user_context["past_input"] = []
        user_context["past_response"] = []
    else:
        user_context = sessions[userid]

    chain = user_context["convo_chain"]
    question = request.args.get("question")
    response = process_response(chain(question))
    data = {"input": question, "response": response, "past_input": user_context["past_input"], "past_response": user_context["past_response"]}
    user_context["past_input"].append(question)
    user_context["past_response"].append(response)
    sessions[userid] = user_context
    return make_response(jsonify(data), 200)