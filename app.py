from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_bcrypt import Bcrypt
from chatbot import init_faiss
from session import UserSession, GlobalSessionStore
from models import db, User
from config import ApplicationConfig
from werkzeug.utils import secure_filename
from logger import setup_logger
import logging
import os

setup_logger()

vectordb = init_faiss()
sessions = GlobalSessionStore()

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
db.init_app(app)

with app.app_context():
    db.create_all()

def is_authenticated(cookies):
    sessionid = get_sessionid(cookies)
    if sessionid is None:
        return False
    
    return sessions.get(sessionid) is not None
    
def get_sessionid(cookies):
    return cookies.get("sessionid", None)

@app.route("/api/register", methods=["POST"])
def register_user():
    params = request.get_json()
    email = params.get("email", "")
    password = params.get("password", "")
    first_name = params.get("first_name", "")
    last_name = params.get("last_name", "")
    if email == "" or password == "" or first_name == "" or last_name == "":
        return make_response(jsonify({"error": "invalid params"}), 400)

    user = User.find(email)
    if user:
        return make_response(jsonify({"error": "user already exists"}), 409)
    
    hashed_password = bcrypt.generate_password_hash(password)
    User.add(email, hashed_password, first_name, last_name)
    logging.info(f"new user {email} created")
    return make_response(jsonify({"msg": "new user added"}), 200)


@app.route("/api/login", methods=["POST"])
def login_user():
    params = request.get_json()
    email = params.get("email", "")
    password = params.get("password", "")
    if email == "" or password == "":
        return make_response(jsonify({"error": "invalid params"}), 400)

    user = User.find(email)
    if user is None:
        return make_response(jsonify({"error": "user not found"}), 403)
    
    if not bcrypt.check_password_hash(user.password, password):
        return make_response(jsonify({"error": "wrong password"}), 403)
    
    session = UserSession(user.id, user.email, vectordb)
    sessions.add(session)
    response = {"email": user.email, 
                "sessionid": session.id, 
                "first_name": user.first_name,
                "last_name": user.last_name}
    logging.info(f"user {user.email} logged in")
    return make_response(jsonify(response), 200)

@app.route("/api/logout", methods=["POST"])
def logout_user():
    sessionid = request.get_json().get("sessionid", "")
    if sessionid == "":
        return make_response(jsonify({"error": "sessionid not found"}), 400)
    
    user_session = sessions.delete(sessionid)
    if user_session is not None:
        user_session.store_session()
        logging.info(f"user {user_session.email} has logged out")
        return make_response(jsonify({"msg": "user logged out"}), 200)

    return make_response(jsonify({"error": "session does not exist"}), 200)

@app.route("/api/chat", methods=["POST"])
def chat():
    if not is_authenticated(request.cookies):
        return make_response(jsonify({"error": "user not logged in"}), 401)
    
    question = request.get_json().get("question", "")
    if question == "":
        return make_response(jsonify({"error": "invalid params"}), 400)
    
    sessionid = get_sessionid(request.cookies)
    user_session = sessions.get(sessionid)
    answer = user_session.chat(question)
    data = {"question": question, 
            "answer": answer, 
            "history": user_session.get_history(exclude_last=True)}
    
    logging.info("user {user_session.email} asked question {question}")
    return make_response(jsonify(data), 200)

@app.route("/api/rating", methods=["POST"])
def rate_response():
    if not is_authenticated(request.cookies):
        return make_response(jsonify({"error": "user not logged in"}), 401)
    
    params = request.get_json()
    index = params.get("index", -1)
    rating = params.get("rating", "")
    if index == -1 or rating == "":
        return make_response(jsonify({"error": "invalid params"}), 400)
    
    sessionid = get_sessionid(request.cookies)
    user_session = sessions.get(sessionid)

    if not user_session.is_valid_index(index):
        return make_response(jsonify({"error": "invalid index"}), 400) 
    
    user_session.store_rating(index, rating)
    return make_response(jsonify({"msg": "response rated"}), 200)

@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):    
    return send_from_directory("data", filename)

@app.route("/api/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file", None)
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join("data", filename)
        file.save(save_path)
        return make_response(jsonify({"msg": "file uploaded"}), 200)
    
    return make_response(jsonify({"error": "empty file"}), 400)

    
if __name__ == "__main__":
    app.run(debug=True)