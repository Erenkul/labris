from flask import Flask
from flask import jsonify
from flask import request

from flask import session

from functools import wraps

from datetime import datetime

#mail için regex ile expression düzeltme
import re
import os
import hashlib

app = Flask(__name__)
app.secret_key = "gelistirme-icin-gizli-anahtar-123"

users=[]
online_users=[]

@app.route("/")
def home():
    return "Merhaba, Flask calisiyor!"

def is_valid_email(email):
    # Basit bir e-posta doğrulama regex ifadesi
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
def is_valid_password(password):
    # Basit bir şifre doğrulama regex ifadesi
    pattern = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"
    return re.match(pattern, password) is not None

@app.route("/users/create",methods=["POST"])
def user_create():
    data = request.get_json()

    if not data or not data.get("username") or not data.get("email"):
        return jsonify({"error": "username ve email zorunlu"}), 400

    if not is_valid_email(data.get("email")):
        return jsonify({"error": "Geçersiz e-posta formatı"}), 400

    if not is_valid_password(data.get("password")):
        return jsonify({"error": "Geçersiz şifre formatı"}), 400
#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test1\", \"email\": \"gecersizemail\"}'
#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test2\", \"email\": \"test2@example.com\"}'
    salt = generate_salt()
    password_hash = hash_password(data.get("password"), salt)

    new_user = {
        "id": len(users) + 1,
        "username": data.get("username"),
        "email": data.get("email"),
        "password_hash": password_hash,
        "password_salt": salt
    }
    users.append(new_user)
    return jsonify({"message": "Kullanici olusturuldu  !", "user": {
        "id": new_user["id"],
        "username": new_user["username"],
        "email": new_user["email"]
    }}), 201
#(venv) PS C:\Users\Eren\intern-projeler\6-flask-uygulamasi> curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test5\", \"email\": \"test5@example.com\", \"password\": \"Passw0rd1\"}'
{
  "message": "Kullanici olusturuldu  !",
  "user": {
    "email": "test5@example.com",
    "id": 1,
    "username": "test5"
  }
}
#(venv) PS C:\Users\Eren\intern-projeler\6-flask-uygulamasi> 

@app.route("/login", methods=["POST"])
def login():
    data=request.get_json()
    username=data.get("username")
    password=data.get("password")

    if not username or not password:
        return jsonify({"error": "username ve password zorunlu"}), 400

    user_found=None
    for user in users:
        if user["username"]==username:
            user_found=user
            break
    if not user_found:
        return jsonify({"error": "Kullanici bulunamadi"}), 404

    hash_check=hash_password(password,user_found["password_salt"])
    if hash_check!=user_found["password_hash"]:
        return jsonify({"error": "Hatali sifre"}), 401

    session["username"]=username
    online_users.append({
        "username": username,
        "ipaddress": request.remote_addr,
        "login_time": datetime.now().isoformat()
    })
    return jsonify({"message": "Giris basarili", "username": username})

# ilk olarak: curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test5\", \"email\": \"test5@example.com\", \"password\": \"Passw0rd1\"}'
# ikinci olarak: curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"test5\", \"password\": \"Passw0rd1\"}'


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        username = session.get("username")
        if not username:
            return jsonify({"error": "Once giris yapmalisiniz"}), 401

        is_online = any(u["username"] == username for u in online_users)
        if not is_online:
            session.clear()
            return jsonify({"error": "Oturum sona ermis, tekrar giris yapin"}), 401

        return view_func(*args, **kwargs)
    return wrapper


@app.route("/logout", methods=["POST"])
@login_required
def logout():

    username=session["username"]

    global online_users
    online_users = [user for user in online_users if user["username"] != username]

    session.clear()
    return jsonify({"message": "Cikis yapildi", "username": username}),200




@app.route("/onlineusers", methods=["GET"])
@login_required
def online_users_route():
    return jsonify({"online_users": online_users})
#curl.exe http://127.0.0.1:5000/onlineusers
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers


@app.route("/users/list", methods=["GET"])
def user_list():
    return jsonify({"users": users})

#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"eren\", \"email\": \"eren@example.com\"}'

@app.route("/TEST")
def test():
    return jsonify({"message": "TEST route calisiyor!"})
#jsonify düz yazı yerine json döndürecek

@app.route("/echo", methods=["POST"])
def echo():
    data=request.get_json()
    return jsonify({"aldigim veri": data})

#curl.exe -X POST http://127.0.0.1:5000/echo -H "Content-Type: application/json" -d '{"isim": "Eren"}' tırnak problemi 
#curl.exe -X POST http://127.0.0.1:5000/echo -H "Content-Type: application/json" -d '{\"isim\": \"Eren\"}


def generate_salt():
    return os.urandom(16).hex()

def hash_password(password, salt):
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    app.run(debug=True)

#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test7\", \"email\": \"test7@example.com\", \"password\": \"Passw0rd1\"}'
#curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"test7\", \"password\": \"Passw0rd1\"}'
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers
#curl.exe -b cookies.txt -X POST http://127.0.0.1:5000/logout
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers