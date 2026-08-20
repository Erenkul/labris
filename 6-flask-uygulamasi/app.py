from flask import Flask
from flask import jsonify
from flask import request

from flask import session

from functools import wraps

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

#mail için regex ile expression düzeltme
import re
import os
import hashlib
import logging

app = Flask(__name__)
app.secret_key = "gelistirme-icin-gizli-anahtar-123"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://flask_user:flask_pass@localhost:5432/flask_app_db" #hangi veritabanına bağlanacağız 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False #sql alchemy ile flask uygulaması arasında bir bağlantı kuruyoruz ve veritabanı değişikliklerini takip etmeye gerek olmadığını belirtiyoruz

db = SQLAlchemy(app) #flask ile sql alchemy arasında bir bağlantı kuruyoruz ve db değişkeni ile veritabanı işlemlerini yapabileceğiz

#logging.basicConfig(
#    filename='activity.log',
#    level=logging.INFO,
#    format='%(asctime)s - %(levelname)s - %(message)s'
#)
activity_logger = logging.getLogger("activity")
activity_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("activity.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

activity_logger.addHandler(file_handler)
activity_logger.propagate = False#en kritik satır: "bu logger'ın mesajları root logger'a sızmasın"


#users=[]
#online_users=[]
class User(db.Model):
    __tablename__ ="users"
    id=db.Column(db.Integer,primary_key=True)
    username= db.Column(db.String(50),unique=True,nullable=False)
    email= db.Column(db.String(100),unique=True,nullable=False)
    password_hash= db.Column(db.String(128),nullable=False)
    password_salt= db.Column(db.String(32),nullable=False)

class OnlineUser(db.Model):
    __tablename__="online_users"
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),nullable=False)
    ipaddress=db.Column(db.String(45),nullable=False)
    login_time=db.Column(db.DateTime,default=datetime.now)


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


    if User.query.filter_by(username=data.get("username")).first() is not None:
        return jsonify({"error": "Bu kullanıcı adı zaten mevcut"}), 409

    if User.query.filter_by(email=data.get("email")).first() is not None:
        return jsonify({"error": "Bu e-posta zaten mevcut"}), 409

    
#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test1\", \"email\": \"gecersizemail\"}'
#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test2\", \"email\": \"test2@example.com\"}'
    salt = generate_salt()
    password_hash = hash_password(data.get("password"), salt)

    new_user = User(
        username=data.get("username"),
        email=data.get("email"),
        password_hash=password_hash,
        password_salt=salt
    )

    db.session.add(new_user)
    db.session.commit()
    activity_logger.info(f"Yeni Kullanici olusturuldu: {new_user.username} id=({new_user.id})")

#users.append(new_user)
    return jsonify({"message": "Kullanici olusturuldu  !", "user": {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email
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
    #for user in users:
    #    if user["username"]==username:
    #        user_found=user
    #        break
    user_found = User.query.filter_by(username=username).first()

    if not user_found:
        activity_logger.warning(f"Giris basarisiz: {username} kullanici bulunamadi")
        return jsonify({"error": "Kullanici bulunamadi"}), 404

    hash_check=hash_password(password,user_found.password_salt)
    if hash_check!=user_found.password_hash:
        activity_logger.warning(f"Giris basarisiz: {username} hatali sifre")
        return jsonify({"error": "Hatali sifre"}), 401

    session["username"]=username

    #online_users.append({
    #    "username": username,
    #    "ipaddress": request.remote_addr,
    #    "login_time": datetime.now().isoformat()
    #})
    #return jsonify({"message": "Giris basarili", "username": username})

# ilk olarak: curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test5\", \"email\": \"test5@example.com\", \"password\": \"Passw0rd1\"}'
# ikinci olarak: curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"test5\", \"password\": \"Passw0rd1\"}'
    new_online_user = OnlineUser(
        username=username,
        ipaddress=request.remote_addr,
    )
    db.session.add(new_online_user)
    db.session.commit()
    activity_logger.info(f"Giris basarili: {username} ip: {request.remote_addr}")
    return jsonify({"message": "Giris basarili", "username": username}), 200


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        username = session.get("username")
        if not username:
            return jsonify({"error": "Once giris yapmalisiniz"}), 401

        #is_online = any(user["username"] == username for user in online_users)
        is_online = OnlineUser.query.filter_by(username=username).first() is not None
        if not is_online:
            session.clear()
            return jsonify({"error": "Oturum sona ermis, tekrar giris yapin"}), 401

        return view_func(*args, **kwargs)
    return wrapper


@app.route("/logout", methods=["POST"])
@login_required
def logout():

    username=session["username"]

    #global online_users
    #online_users = [user for user in online_users if user["username"] != username]

    OnlineUser.query.filter_by(username=username).delete()
    db.session.commit()
    activity_logger.info(f"Cikis yapildi: {username}")

    session.clear()
    return jsonify({"message": "Cikis yapildi", "username": username}),200




@app.route("/onlineusers", methods=["GET"])
@login_required
def online_users_route():
    all_online_users = OnlineUser.query.all()
    result = [
        {
            "username": user.username,
            "ipaddress": user.ipaddress,
            "login_time": user.login_time.isoformat()
        }
        for user in all_online_users
    ]
    return jsonify({"online_users": result})
#curl.exe http://127.0.0.1:5000/onlineusers
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers


@app.route("/users/list", methods=["GET"])
#password_hash ve password_salt bilgilerini döndürmemek için safe_users listesi oluşturuyoruz
#def user_list():
#    safe_users = [
#        {"id": user["id"], "username": user["username"], "email": user["email"]}
#        for user in users
#    ]
#    return jsonify({"users": safe_users})
#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"eren\", \"email\": \"eren@example.com\"}'
def user_list():
    all_users = User.query.all()
    safe_users = [
        {"id": user.id, "username": user.username, "email": user.email}
        for user in all_users
    ]
    return jsonify({"users": safe_users})





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


@app.route("/users/delete/<int:user_id>", methods=["DELETE"])
@login_required #giriş yapmış kullanıcılar sadece silme işlemi yapabilir
def delete_user(user_id):
    #global users
    user_found= User.query.filter_by(id=user_id).first()
    
    #for user in users: #önce silinecek kullanıcı gerçekten var mı diye kontrol ediyoruz
    #    if user["id"]==user_id:
    #        user_found=user
    #        break

    if not user_found:
            return jsonify({"error": "Kullanici bulunamadi"}), 404
    db.session.delete(user_found)
    db.session.commit()
    activity_logger.info(f"Kullanici silindi: {user_found.username} silen=({session.get('username')})")

    #users=[user for user in users if user["id"] != user_id] 
    #o kullanıcı dışıındaki herkesi tutan yani bir liste oluşturuyoruz. Ve kullanıcı listeden atılmış oluyor

    return jsonify({"message": "Kullanici silindi", "id": user_id}), 200

    #1 kullanıcıyı oluşturma: curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"admin1\", \"email\": \"admin1@example.com\", \"password\": \"Passw0rd1\"}'
    #2 silinecek olan ikinci kullanıcıyı oluşturma: curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"silinecek\", \"email\": \"silinecek@example.com\", \"password\": \"Passw0rd1\"}'
    #3 giriş yaptık admin1 olarak: curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"admin1\", \"password\": \"Passw0rd1\"}'
    #4 kullanıcı listesini çektik: curl.exe -b cookies.txt http://127.0.0.1:5000/users/list
    #5 kullanıcı silme: curl.exe -b cookies.txt -X DELETE http://127.0.0.1:5000/users/delete/2
    #6 kullanıcı listesini tekrar çektik: curl.exe -b cookies.txt http://127.0.0.1:5000/users/list
    #7 kullanıcı listesini silme: curl.exe -b cookies.txt -X DELETE http://127.0.0.1:5000/users/delete/999


@app.route("/users/update/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    user_found = User.query.filter_by(id=user_id).first()
    #for user in users:
    #    if user["id"] == user_id:
    #        user_found = user
    #        break

    if not user_found:
        return jsonify({"error": "Kullanici bulunamadi"}), 404

    data = request.get_json()

    if data.get("email"):
        if not is_valid_email(data.get("email")):
            return jsonify({"error": "Geçersiz e-posta formatı"}), 400
        user_found.email = data.get("email")

    if data.get("password"):
        if not is_valid_password(data.get("password")):
            return jsonify({"error": "Geçersiz şifre formatı"}), 400
        salt = generate_salt()
        password_hash = hash_password(data.get("password"), salt)
        user_found.password_hash = password_hash
        user_found.password_salt = salt

    db.session.commit()

    activity_logger.info(f"Kullanici guncellendi:[{user_found.id}] guncelleyen=({session.get('username')})")
    return jsonify({"message": "Kullanici guncellendi", "user": {
        "id": user_found.id,
        "username": user_found.username,
        "email": user_found.email
    }}), 200

#curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"admin1\", \"password\": \"Passw0rd1\"}'
#curl.exe -b cookies.txt -X PUT http://127.0.0.1:5000/users/update/1 -H "Content-Type: application/json" -d '{\"email\": \"admin1-yeni@example.com\"}'
#curl.exe -b cookies.txt http://127.0.0.1:5000/users/list

if __name__ == "__main__":
    with app.app_context():#flask a uygulamanın ayarlarına erişmesini sağlamak için app.app_context() kullanıyoruz. Bu, veritabanı işlemlerini gerçekleştirmek için gerekli olan uygulama bağlamını oluşturur.
        db.create_all()  # Veritabanı tablolarını oluştur
        #user ve online_users tablolarını oluşturmak için db.create_all() kullanıyoruz. Bu, SQLAlchemy'nin veritabanı şemasını oluşturmasını sağlar.
    app.run(host="0.0.0.0", port=5000, debug=True)

#curl.exe -X POST http://127.0.0.1:5000/users/create -H "Content-Type: application/json" -d '{\"username\": \"test7\", \"email\": \"test7@example.com\", \"password\": \"Passw0rd1\"}'
#curl.exe -c cookies.txt -X POST http://127.0.0.1:5000/login -H "Content-Type: application/json" -d '{\"username\": \"test7\", \"password\": \"Passw0rd1\"}'
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers
#curl.exe -b cookies.txt -X POST http://127.0.0.1:5000/logout
#curl.exe -b cookies.txt http://127.0.0.1:5000/onlineusers