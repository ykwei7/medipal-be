from chatbot import new_chat
from datetime import datetime, timedelta
from chatbot import get_response
import secrets

TTL = timedelta(minutes=5)

class UserSession:
    def __init__(self, userid, vectordb):
        self.userid = userid
        self.id = secrets.token_urlsafe(16)
        self.start_time = datetime.now()
        self.expiry_time = self.start_time + TTL
        self.chatbot = new_chat(vectordb)
        self.history = []

    def chat(self, question):
        return get_response(self.chatbot, question)

    def add_history(self, question, answer):
        self.history.append((question, answer))

    def get_history(self):
        return self.history

    def extend_expiry(self):
        self.expiry_time = datetime.now() + TTL

    def has_expired(self):
        return datetime.now() > self.expiry_time
    

