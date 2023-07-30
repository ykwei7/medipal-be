from flask import Flask, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from chatbot import init_faiss
from session import UserSession
from models import db, User
from config import ApplicationConfig

vectordb = init_faiss()
sessions = {}

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
db.init_app(app)

with app.app_context():
    db.create_all()

def is_logged_in(cookies):
    if "sessionid" not in cookies:
        return False
    
    sessionid = cookies["sessionid"]
    if sessionid not in sessions:
        return False
    
    return True
    
def get_sessionid(cookies):
    return cookies["sessionid"]


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
    sessions[session.id] = session 
    response = {"email": user.email, 
                "sessionid": session.id, 
                "first_name": user.first_name,
                "last_name": user.last_name}
    return make_response(jsonify(response), 200)

@app.route("/api/logout", methods=["POST"])
def logout_user():
    sessionid = request.get_json().get("sessionid", "")
    if sessionid == "":
        return make_response(jsonify({"error": "sessionid not found"}), 400)
    
    if sessionid in sessions:
        user_session = sessions[sessionid]
        del sessions[sessionid]
        user_session.store_session()
        return make_response(jsonify({"msg": "user logged out"}), 200)

    return make_response(jsonify({"error": "session does not exist"}), 200)

@app.route("/api/chat", methods=["POST"])
def chat():
    if not is_logged_in(request.cookies):
        return make_response(jsonify({"error": "user not logged in"}), 401)
    
    question = request.get_json().get("question", "")
    if question == "":
        return make_response(jsonify({"error": "invalid params"}), 400)
    
    sessionid = get_sessionid(request.cookies)
    user_session = sessions[sessionid]
    answer = user_session.chat(question)
    data = {"question": question, 
            "answer": answer, 
            "history": user_session.get_history(exclude_last=True)}
    
    return make_response(jsonify(data), 200)

@app.route("/api/rating", methods=["POST"])
def rate_response():
    if not is_logged_in(request.cookies):
        return make_response(jsonify({"error": "user not logged in"}), 401)
    
    params = request.get_json()
    index = params.get("index", -1)
    rating = params.get("rating", "")
    if index == -1 or rating == "":
        return make_response(jsonify({"error": "invalid params"}), 400)
    
    sessionid = get_sessionid(request.cookies)
    user_session = sessions[sessionid]

    if not user_session.is_valid_index(index):
        return make_response(jsonify({"error": "invalid index"}), 400) 
    
    user_session.store_rating(index, rating)
    return make_response(jsonify({"msg": "response rated"}), 200)
    
if __name__ == "__main__":
    app.run(debug=True)