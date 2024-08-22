import os
import pathlib
import random
import string
import datetime
import requests

import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, abort, g
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from MySQLdb import OperationalError

app = Flask(__name__)

# MySQL Configuration
load_dotenv()
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_POOL_RECYCLE'] = 299  # Optional, helps manage database connections

mysql = MySQL(app)
app.secret_key = "IceCream"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Load environment variables from .env file
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
GOOGLE_AUTH_URI = os.getenv('GOOGLE_AUTH_URI')
GOOGLE_TOKEN_URI = os.getenv('GOOGLE_TOKEN_URI')
GOOGLE_AUTH_PROVIDER_CERT_URL = os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL')
GOOGLE_REDIRECT_URIS = os.getenv('GOOGLE_REDIRECT_URIS').split(',')
GOOGLE_JAVASCRIPT_ORIGINS = os.getenv('GOOGLE_JAVASCRIPT_ORIGINS').split(',')

client_secrets_file = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": GOOGLE_AUTH_URI,
        "token_uri": GOOGLE_TOKEN_URI,
        "auth_provider_x509_cert_url": GOOGLE_AUTH_PROVIDER_CERT_URL,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": GOOGLE_REDIRECT_URIS,
        "javascript_origins": GOOGLE_JAVASCRIPT_ORIGINS
    }
}

# Load environment variables and create client secrets file
client_secrets_file_path = "client_secrets.json"

# Ensure this file path exists and is correctly created with the proper content
with open(client_secrets_file_path, "w") as json_file:
    json.dump(client_secrets_file, json_file)

# Use the path to the client secrets file
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file_path,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://smilysoul.onrender.com/authorize"
)

flowcounsellor = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file_path,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://smilysoul.onrender.com/authorizecounsellor"
)

@app.teardown_appcontext
def teardown_db(exception):
    if hasattr(g, 'mysql_db'):
        try:
            g.mysql_db.close()
        except OperationalError as e:
            print(f"Error closing MySQL connection: {e}")
            pass  # Handle the exception or log it

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    else:
        return redirect("/home")

@app.route("/home")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    elif "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
    return render_template("home.html")

@app.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    else:
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)

@app.route("/authorize")
def authorize():
    if "user" in session:
        return redirect(url_for("dashboard"))
    else:
        flow.fetch_token(authorization_response=request.url)
        if session["state"] != request.args["state"]:
            return redirect(url_for("dashboard"))

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        session["user"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["image"] = id_info.get("picture")
        session["mail"] = id_info.get("email")

        cur = mysql.connection.cursor()
        resultvalue = cur.execute("SELECT * FROM users WHERE user_id=%s", (session["user"],))
        if resultvalue == 0:
            cur.execute("INSERT INTO users(user_id,email_id,name) VALUES(%s,%s,%s)", (session["user"],session["mail"],session["name"],))
            mysql.connection.commit()
        cur.close()

        return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html")
    else:
        return redirect(url_for("home"))

@app.route("/profile", methods=["POST", "GET"])
def profile():
    if "user" in session:
        if request.method == "POST":
            userDetails = request.form
            gender = userDetails['gender']
            dob = userDetails['dob']
            cur = mysql.connection.cursor()

            if dob != "":
                cur.execute("UPDATE users SET dob=%s WHERE user_id=%s", (dob, session["user"],))
            else:
                cur.execute("UPDATE users SET dob=NULL WHERE user_id=%s", (session["user"],))

            if gender:
                cur.execute("UPDATE users SET gender=%s WHERE user_id=%s", (gender, session["user"],))
            else:
                cur.execute("UPDATE users SET gender=NULL WHERE user_id=%s", (session["user"],))

            mysql.connection.commit()
            cur.close()

        cur = mysql.connection.cursor()
        resultvalue = cur.execute("SELECT * FROM users WHERE user_id=%s", (session["user"],))
        row = cur.fetchone()
        gender = row[4]
        dob = row[3]
        mysql.connection.commit()
        cur.close()

        return render_template("profile.html", name=session["name"], mail=session["mail"], imageurl=session["image"], dob=dob, gender=gender)
    else:
        return redirect(url_for("home"))

@app.route("/booking")
def booking():
    if "user" in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM counsellor")
        result = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template("booking.html", tb=result)
    else:
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect(url_for("index"))

@app.route("/slot/<id>")
def slot(id):
    if "user" in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointment WHERE user_id=%s", (session["user"],))
        res = cur.fetchall()
        cur.close()
        if len(res) > 0:
            return render_template("alreadybooked.html")

        session["counsellor_id"] = id
        cur = mysql.connection.cursor()
        dct = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []}
        cur.execute("SELECT day_available,time_slot,flag FROM day_availability WHERE counsellor_id=%s", (id,))
        result = cur.fetchall()
        for row in result:
            dct[row[0]].append([row[1], row[2] == 1])
        mysql.connection.commit()
        cur.close()

        l = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        date_lst = []
        day_lst = []
        for i in range(1, 8):
            Day_Date = datetime.datetime.today() + datetime.timedelta(days=i)
            date_lst.append(Day_Date.strftime('%Y-%m-%d'))
            day_lst.append(l[Day_Date.weekday()])
        return render_template("slot.html", ls=day_lst, d=dct, date_lst=date_lst, inc=datetime.timedelta(minutes=45))
    else:
        return redirect(url_for("home"))

@app.route("/mysession", methods=["POST", "GET"])
def mysession():
    if "user" in session:
        if request.method == "POST":
            slotDetail = request.form
            time, date, day = (slotDetail['btnradio']).split('@')
            counsellor_id = session["counsellor_id"]
            session["booked_counsellor"] = counsellor_id
            user_id = session["user"]
            cur = mysql.connection.cursor()

            if counsellor_id == "1":
                meetlink = "https://meet.google.com/atr-jafq-gqt"
            elif counsellor_id == "2":
                meetlink = "https://meet.google.com/ddf-dmbb-kya"
            else:
                meetlink = "https://meet.google.com/ddf-dmbb-kya"

            cur.execute("INSERT INTO appointment(Counsellor_Id, User_ID, Start_Time, Date, meet_link) VALUES(%s, %s, %s, %s, %s)", 
                        (counsellor_id, user_id, time, date, meetlink,))
            cur.execute("UPDATE day_availability SET flag=1 WHERE day_available=%s AND time_slot=%s AND counsellor_id=%s", 
                        (day, time, counsellor_id,))
            mysql.connection.commit()
            cur.close()

        uid = session["user"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM (SELECT * FROM appointment NATURAL JOIN counsellor WHERE user_id=%s) AS a", (session["user"],))
        res = cur.fetchone()
        if res:
            A_date = res[4]
            A_time = res[3]
            name = res[7]
            meet_link = res[5]
            A_counsellor = res[0]
            enable = False

            from datetime import date, datetime
            C_date = date.today()
            my_time = datetime.min.time()
            A_datetime = datetime.combine(A_date, my_time)
            A_datetime += A_time
            C_datetime = datetime.now()

            l = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day = l[A_datetime.weekday()]

            if A_date == C_date and C_datetime - A_datetime > datetime.timedelta(seconds=1) and C_datetime - A_datetime <= datetime.timedelta(hours=1):
                enable = True

            return render_template("mysessions.html", C_datetime=C_datetime, A_datetime=A_datetime, time=A_time, date=A_date, name=name, meet_link=meet_link, enable=enable, A_day=day, A_counsellor=A_counsellor)
        return render_template("nosession.html")
    else:
        return redirect(url_for("home"))

@app.route("/delete", methods=["POST"])
def delete():
    if request.method == "POST":
        bookingDetail = request.form
        day, time, booked_counsellor = (bookingDetail['btndelete']).split('@')
        cur = mysql.connection.cursor()
        cur.execute("UPDATE day_availability SET flag=0 WHERE day_available=%s AND time_slot=%s AND counsellor_id=%s", (day, time, booked_counsellor,))
        cur.execute("DELETE FROM appointment WHERE user_id=%s", (session["user"],))
        mysql.connection.commit()
        cur.close()

    return redirect(url_for("mysession"))

@app.route("/logincounsellor")
def logincounsellor():
    if "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
    else:
        authorization_url, state = flowcounsellor.authorization_url()
        session["state"] = state
        return redirect(authorization_url)

@app.route("/authorizecounsellor")
def authorizecounsellor():
    if "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
    else:
        flowcounsellor.fetch_token(authorization_response=request.url)

        if session["state"] != request.args["state"]:
            return redirect(url_for("counsellor_session"))

        credentials = flowcounsellor.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        session["counsellorid"] = id_info.get("sub")
        session["counsellorname"] = id_info.get("name")
        session["counsellorimage"] = id_info.get("picture")
        session["counsellormail"] = id_info.get("email")

        cur = mysql.connection.cursor()
        resultvalue = cur.execute("SELECT * FROM counsellor WHERE counsellor_id=%s", (session["counsellorid"],))
        if resultvalue == 0:
            cur.execute("INSERT INTO counsellor(counsellor_id, email_id, name, image) VALUES(%s, %s, %s, %s)", (session["counsellorid"], session["counsellormail"], session["counsellorname"], session["counsellorimage"],))
            mysql.connection.commit()
        cur.close()

        return redirect(url_for("counsellor_session"))

@app.route("/counsellor_session")
def counsellor_session():
    if "counsellorid" not in session:
        return redirect(url_for("home"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM appointment WHERE Counsellor_id=%s", (session["counsellorid"],))

    result = cur.fetchall()
    user = []
    for i in range(len(result)):
        temp = []
        temp.append(result[i][3])
        temp.append(result[i][4])
        temp.append(result[i][5])
        cur.execute("SELECT * FROM users WHERE user_id=%s", (result[i][2],))
        tempuser = cur.fetchall()
        temp.append(tempuser[0][2])
        temp.append(tempuser[0][1])
        temp.append(tempuser[0][3])
        temp.append(tempuser[0][4])
        temp.append(result[i][1])
        user.append(temp)
    mysql.connection.commit()
    cur.close()
    return render_template("counsellor_sessions.html", data=user)

# Video calling setup
roomname = ''

load_dotenv()
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_api_key_sid = os.environ.get('TWILIO_API_KEY_SID')
twilio_api_key_secret = os.environ.get('TWILIO_API_KEY_SECRET')
twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret, twilio_account_sid)

def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation
    return twilio_client.conversations.conversations.create(friendly_name=name)

@app.route('/join')
def join():
    if "user" in session:
        return render_template('userjoin.html')
    elif "counsellorid" in session:
        return render_template('counsellorjoin.html')
    else:
        return redirect(url_for("home"))

@app.route('/video', methods=['POST'])
def video():
    if "user" in session:
        uid = session["user"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointment WHERE user_id=%s", (session["user"],))
        res = cur.fetchone()
        cur.close()
        roomname = res[0]
        conversation = get_chatroom(roomname)
        username = session["name"]
        try:
            conversation.participants.create(identity=username)
        except TwilioRestException as exc:
            if exc.status != 409:
                raise

        token = AccessToken(twilio_account_sid, twilio_api_key_sid, twilio_api_key_secret, identity=username)
        token.add_grant(VideoGrant(room=roomname))
        token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

        return {'token': token.to_jwt().decode(), 'conversation_sid': conversation.sid}
    elif "counsellorid" in session:
        cid = session["counsellorid"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointment WHERE counsellor_id=%s", (session["counsellorid"],))
        res = cur.fetchone()
        cur.close()
        roomname = res[0]
        conversation = get_chatroom(roomname)
        username = session["counsellorname"]
        try:
            conversation.participants.create(identity=username)
        except TwilioRestException as exc:
            if exc.status != 409:
                raise

        token = AccessToken(twilio_account_sid, twilio_api_key_sid, twilio_api_key_secret, identity=username)
        token.add_grant(VideoGrant(room=roomname))
        token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

        return {'token': token.to_jwt().decode(), 'conversation_sid': conversation.sid}
    else:
        return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port=8080)
