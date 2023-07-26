from flask import Flask, request, jsonify, make_response
from chatbot import init_faiss
from session import UserSession
from user import get_userid

vectordb = init_faiss()
sessions = {}

app = Flask(__name__)

@app.route("/api/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    # password = request.json["password"]
    userid = get_userid(email)
    if userid == "":
        return make_response(jsonify({"error": "user not found"}), 403)
    
    session = UserSession(userid, vectordb)
    sessions[session.id] = session 
    return make_response(jsonify({"sessionid": session.id}), 200)

@app.route("/api/chat", methods=["POST"])
def chat():
    if "sessionid" not in request.cookies:
        return make_response(jsonify({"error": "user not logged in"}), 401)
    
    sessionid = request.cookies["sessionid"]
    if sessionid not in sessions:
        return make_response(jsonify({"error": "user session has expired"}), 401)
    
    user_session = sessions[sessionid]
    question = request.json.get("question")
    response = user_session.chat(question)
    data = jsonify({"input": question, "response": response, "history": user_session.get_history()})
    
    user_session.add_history(question, response)
    user_session.extend_expiry()
    return make_response(data, 200)

if __name__ == "__main__":
    app.run(debug=True)