import os
import pathlib
import random
import string
import datetime
import requests
import json
from datetime import datetime, timedelta
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
from google_auth_oauthlib.flow import Flow

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


@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
        #redirect dashbord html
    else:
        #redirect home html
        return redirect("/home")
@app.route("/home")
def home():

    if "user" in session:
        return redirect(url_for("dashboard"))
    elif "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
        #check if authenticated and redirect dashbord
    return render_template("home.html")


@app.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    else:
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        print("user")
        return redirect(authorization_url)

@app.route("/authorize")
def authorize():
    print("userauth")
    if "user" in session:
       return redirect(url_for("dashboard"))
    else:
        flow.fetch_token(authorization_response=request.url)

        if (not (session["state"] == request.args["state"])):
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
        
        cur=mysql.connection.cursor()
        resultvalue=cur.execute("SELECT * FROM USERS WHERE user_id=%s", (session["user"],))
        if (resultvalue==0):
            print(resultvalue)
            print("userauth")
            cur.execute("INSERT INTO USERS(user_id,email_id,name) VALUES(%s,%s,%s)", (session["user"],session["mail"],session["name"],))
            mysql.connection.commit()
        cur.close()

        return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html")
    else:
        return redirect(url_for("home"))


@app.route("/profile", methods = ["POST","GET"])
def profile():
    if "user" in session:
        if request.method == "POST":
            userDetails = request.form
            gender = userDetails['gender']
            dob = userDetails['dob']
            cur=mysql.connection.cursor()
            if(dob!=""):
                cur.execute("UPDATE USERS SET dob=%s WHERE user_id=%s",(dob,session["user"],))
            else :
                cur.execute("UPDATE USERS SET dob=NULL WHERE user_id=%s",(session["user"],))
                
            if(gender!=None):
                cur.execute("UPDATE USERS SET gender=%s WHERE user_id=%s",(gender,session["user"],))
            else :
                cur.execute("UPDATE USERS SET gender=NULL WHERE user_id=%s",(session["user"],))
            mysql.connection.commit()
            cur.close()

        cur=mysql.connection.cursor()
        resultvalue=cur.execute("SELECT * FROM USERS WHERE user_id=%s", (session["user"],))
        
        row = cur.fetchone()
        gender = row[4]
        dob = row[3]
        mysql.connection.commit()
        cur.close()
        name = session["name"]
        mail=session["mail"]
        imageurl=session["image"]
        return render_template("profile.html", name = session["name"],mail=session["mail"],imageurl=session["image"], dob=dob , gender=gender)
    else:
        return redirect(url_for("home"))

@app.route("/booking")
def booking():
    if "user" in session:
        
        cur = mysql.connection.cursor()
        cur.execute("select * from counsellor")
        result = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template("booking.html",tb = result) 

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
        cur.execute("Select * from appointment where user_id=%s",(session["user"],))
        res=cur.fetchall()
        cur.close()
        if(len(res)>0):
            return render_template("alreadybooked.html")
        
        session["counsellor_id"] = id
        print(session["counsellor_id"])
        cur = mysql.connection.cursor()
        dct = {"Monday":[],"Tuesday":[],"Wednesday":[],"Thursday":[],"Friday":[],"Saturday":[],"Sunday":[]}
        cur.execute("select day_available,time_slot,flag from day_availability where counsellor_id = %s",(id,))
        result = cur.fetchall()
        for row in result:
            dct[row[0]].append([row[1],row[2]==1])
        
        # for row in result:
        #     dct[row].sort()
        print(dct)
        mysql.connection.commit()
        cur.close()
        l=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        # d={
        #     "Monday":[["12",True],["23",False]],
        #     "Tuesday":[["121",False],["34",True]],
        #     "Wednesday":[["12",True],["23",False]],
        #     "Thursday":[["12",True],["23",False]],
        #     "Friday":[["12",True],["23",False]],
        #     "Saturday":[["12",True],["23",False]],
        #     "Sunday":[["12",True],["23",False]]
        # }
        date_lst = []
        day_lst = []
        for i in range(1,8):
            Day_Date = datetime.datetime.today() + datetime.timedelta(days=i)
            date_lst.append(Day_Date.strftime('%Y-%m-%d'))
            day_lst.append(l[Day_Date.weekday()])
        return render_template("slot.html", ls=day_lst, d=dct,date_lst = date_lst, inc=datetime.timedelta(minutes=45))
    else:
        return redirect(url_for("home"))

@app.route("/mysession", methods = ["POST","GET"])
def mysession():
    if "user" in session:
        if request.method == "POST":
            slotDetail = request.form
            print((slotDetail['btnradio']))
            time,date,day = (slotDetail['btnradio']).split('@')
            print(day)
            # session["day"] = day
            # session["time"]=time
            counsellor_id = session["counsellor_id"]
            session["booked_counsellor"]=counsellor_id
            user_id = session["user"]
            cur = mysql.connection.cursor()
            
            if(counsellor_id=="1"):
                meetlink="https://meet.google.com/atr-jafq-gqt"
            if(counsellor_id=="2"):
                meetlink="https://meet.google.com/ddf-dmbb-kya"
            if(counsellor_id =="105700541288390913348"):
                meetlink ="https://meet.google.com/ddf-dmbb-kya"

            print(day,time)
            cur.execute("INSERT INTO appointment (Counsellor_Id,User_ID,Start_Time,Date,meet_link) VALUES(%s,%s,%s,%s,%s)",(counsellor_id,user_id,time,date,meetlink,))
            cur.execute("update day_availability set flag=1 where day_available = %s AND time_slot=%s  AND counsellor_id=%s",(day,time,counsellor_id,))
            print(cur.fetchall())
            mysql.connection.commit()
            cur.close()
        uid=session["user"]
        cur = mysql.connection.cursor()
        cur.execute("select * from ( SELECT * from appointment  natural join counsellor where user_id=%s) as a",(session["user"],))
        res=cur.fetchone()
        if (res!=0 and res!=None ):
            print(res)
            A_date=res[4]
            A_time=res[3]
            name=res[7]
            meet_link=res[5]
            A_counsellor=res[0]
            enable = False
           
        
            from datetime import date
            from datetime import datetime
            C_date = date.today()
            my_time = datetime.min.time()
            A_datetime = datetime.combine(A_date, my_time)
            A_datetime+=A_time
            C_datetime=datetime.now()
            print(type(C_datetime))
            # print(type(C_date))
            print(type(A_datetime),A_datetime)
            print(type(A_date), A_date)
            l=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            day=l[A_datetime.weekday()]
            print(day)
            
            #C_date = todays.strptime(date,"%Y-%m-%d")
            if(A_date==C_date and C_datetime-A_datetime>timedelta(seconds=1) and C_datetime-A_datetime <=timedelta(hours=1)):
                enable=True     

            return render_template("mysessions.html",C_datetime=C_datetime,A_datetime=A_datetime,time=A_time,date=A_date,name=name,meet_link=meet_link,enable=enable,A_day=day,A_counsellor=A_counsellor)
        return render_template("nosession.html")
    else:
        return redirect(url_for("home"))
@app.route("/delete", methods = ["POST"])
def delete():
    if request.method == "POST":
        bookingDetail = request.form
        print((bookingDetail['btndelete']))
        day,time,booked_counsellor = (bookingDetail['btndelete']).split('@')
        cur = mysql.connection.cursor()
        cur.execute("update day_availability set flag=0 where day_available = %s AND time_slot=%s AND counsellor_id=%s",(day,time,booked_counsellor,))
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM appointment WHERE user_id=%s",(session["user"],))
        cur.close()
        mysql.connection.commit()
        

    return redirect(url_for("mysession"))


@app.route("/logincounsellor")
def logincounsellor():
    if "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
    else:
        authorization_url, state = flowcounsellor.authorization_url()
        session["state"] = state
        print("counsellor")
        return redirect(authorization_url)

@app.route("/authorizecounsellor")
def authorizecounsellor():
    if "counsellorid" in session:
        return redirect(url_for("counsellor_session"))
    else:
        print("counsellorauth")
        flowcounsellor.fetch_token(authorization_response=request.url)

        if (not (session["state"] == request.args["state"])):
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
        
        cur=mysql.connection.cursor()
        resultvalue=cur.execute("SELECT * FROM Counsellor WHERE counsellor_id=%s", (session["counsellorid"],))
        if (resultvalue==0):
            print(resultvalue)
            cur.execute("INSERT INTO Counsellor(counsellor_id,email_id,name,image) VALUES(%s,%s,%s,%s)", (session["counsellorid"],session["counsellormail"],session["counsellorname"],session["counsellorimage"],))
            
            cur.execute("INSERT INTO day_availability VALUES (%s,'Friday','10:30:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Friday','11:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Friday','14:00:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Friday','14:45:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Monday','10:30:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Monday','11:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Monday','15:00:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Monday','15:45:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Saturday','01:00:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Sunday','12:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Thursday','10:30:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Thursday','11:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Thursday','14:00:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Tuesday','10:30:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Tuesday','11:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Wednesday','11:30:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Wednesday','12:15:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Wednesday','15:00:00',0)", (session["counsellorid"],))
            cur.execute("INSERT INTO day_availability VALUES (%s,'Wednesday','15:45:00',0)", (session["counsellorid"],))

            
            mysql.connection.commit()
        cur.close()

        return redirect(url_for("counsellor_session"))

@app.route("/counsellor_session")
def counsellor_session():
    if "counsellorid" not in session:
        return redirect(url_for("home"))
    
    cur = mysql.connection.cursor()
    cur.execute("select * from appointment where Counsellor_id=%s",(session["counsellorid"],))
    
    result = cur.fetchall()
    user=[]
    for i in range(len(result)):
        temp=[]
        temp.append(result[i][3])
        temp.append(result[i][4])
        temp.append(result[i][5])
        cur.execute("SELECT * FROM users WHERE user_id=%s",(result[i][2],))
        tempuser=cur.fetchall()
        temp.append(tempuser[0][2])
        temp.append(tempuser[0][1])
        temp.append(tempuser[0][3])
        temp.append(tempuser[0][4])
        temp.append(result[i][1])
        user.append(temp)
    mysql.connection.commit()
    # print(result)
    print(user)
    cur.close()
    return render_template("counsellor_sessions.html",data=user) 


# video calling ---



roomname=''

load_dotenv()
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_api_key_sid = os.environ.get('TWILIO_API_KEY_SID')
twilio_api_key_secret = os.environ.get('TWILIO_API_KEY_SECRET')
twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret,
                       twilio_account_sid)



def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation

    # a conversation with the given name does not exist ==> create a new one
    return twilio_client.conversations.conversations.create(
        friendly_name=name)


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
    #username = request.get_json(force=True).get('username')
    #id=request.get_json(force=True).get('appointmentxyz')
    #roomname=id
    # if not username:
    #     abort(401)
    # if not id:
    #     abort(401)
    if "user" in session:
        uid=session["user"]
        cur = mysql.connection.cursor()
        cur.execute(" SELECT * from appointment   where user_id=%s",(session["user"],))
        res=cur.fetchone()
        cur.close()
        roomname=res[0]
        conversation = get_chatroom(roomname)
        username=session["name"]
        #username=str(random.randint(300,500))
        try:
            conversation.participants.create(identity=username)
        except TwilioRestException as exc:
            # do not error if the user is already in the conversation
            if exc.status != 409:
                raise
        
        token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                            twilio_api_key_secret, identity=username)
        token.add_grant(VideoGrant(room=roomname))
        token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

        return {'token': token.to_jwt().decode(),
                'conversation_sid': conversation.sid}
    elif "counsellorid" in session:
        cid=session["counsellorid"]
        cur = mysql.connection.cursor()
        cur.execute(" SELECT * from appointment where counsellor_id=%s",(session["counsellorid"],))
        res=cur.fetchone()
        cur.close()
        roomname=res[0]
        conversation = get_chatroom(roomname)
        username=session["counsellorname"]
        #username=str(random.randint(300,500))
        try:
            conversation.participants.create(identity=username)
        except TwilioRestException as exc:
            # do not error if the user is already in the conversation
            if exc.status != 409:
                raise
        
        token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                            twilio_api_key_secret, identity=username)
        token.add_grant(VideoGrant(room=roomname))
        token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

        return {'token': token.to_jwt().decode(),
                'conversation_sid': conversation.sid}
    else:
        return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True,port=8080)
