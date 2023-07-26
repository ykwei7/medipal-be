users = {"gao.bo": 1}

def get_userid(email):
    if email not in users:
        return ""
    return users[email]