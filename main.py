from flask import Flask, render_template, redirect,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import json
from flask_marshmallow import Marshmallow
import os,datetime
import random, string
from flask import Response
from datetime import date
import random 
app = Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'corona_data_api' 
ma = Marshmallow(app)


class corona_data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(50), unique=True)
    confirmed = db.Column(db.Integer)
    discharged = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    
    def __init__(self,state,confirmed,discharged,deaths):
        self.state =state
        self.confirmed = confirmed
        self.discharged =discharged
        self.deaths = deaths

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)   
    email = db.Column(db.String(100))
    api_key = db.Column(db.String(100))
    created_at = db.Column(db.String(50),default=datetime.datetime.utcnow) 
    def __init__(self,email,api_key):
        self.email = email
        self.api_key = api_key

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    confirmed = db.Column(db.Integer)
    active = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    death = db.Column(db.Integer)
    created = db.Column(db.String(100), default=datetime.datetime.utcnow)
    def __init__(self,confirmed,active,recovered,death):
        self.confirmed = confirmed
        self.active = active
        self.recovered = recovered
        self.death = death
        
        
class corona_dataAPI(ma.Schema):
    class Meta:
        fields = ("id", "state", "confirmed","discharged","deaths")

class UsersAPI(ma.Schema):
    class Meta:
        fields = ("id", "email","api_key")      

class CaseAPI(ma.Schema):
    class Meta:
        fields = ("id","confirmed","recovered","death")
        
        
corona_data_schema = corona_dataAPI()
corona_datas_schema = corona_dataAPI(many=True)
users_schema =  UsersAPI(many=True)
user_schema = UsersAPI()
Case_schema = CaseAPI(many=True)

    
       
@app.route('/')
def index():
    response = {"message" :"Server is upto the mark!"}
    return response
        
@app.route('/api/all/<api_key>')
def all_db(api_key):
    check_api = Users.query.filter_by(api_key = api_key).first()
    if check_api:
        data = corona_data.query.all()
        response = corona_datas_schema.dump(data)
        return jsonify(response)
    else:
        response = {"error": "incorrect API key"}
        return response


@app.route('/api/state/<state>')
def show(state):
    result = corona_data.query.filter_by(state=state.lower()).first()
    response = corona_data_schema.dump(result)
    return jsonify(response)



@app.route('/api/users')
def all_users():
    data = Users.query.all()
    response = users_schema.dump(data)
    return jsonify(response)

@app.route('/api/users/<id>')
def user(id):
    data = Users.query.filter_by(id = id).first()
    db.session.delete(data)
    db.session.commit()
    response = {'message':'Deleted', 'status':200}
    return jsonify(response)



@app.route('/users/<email>')
def global_api(email):
    api_key = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
    user = Users.query.all()
    last_id = (user[len(user) -1 ].id)
    print(len(user))
    user = Users(email = email, api_key = api_key)
    db.session.add(user)
    db.session.commit()  
    response = {
            'email' :email,
            'api_key' : api_key,
            'status' : 200
        }
    
    return response

@app.route('/collect')
def collect():
    url = "https://covid19ind.zaoapp.net/"
    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'html.parser')
    real_data = []
    for tr in soup.find_all('td', {'class', 'text-center'}):
        real_data.append(tr.text)
    final_array = ([real_data[i:i + 3] for i in range(0, len(real_data), 3)])
    states = ['Kerala','Maharashtra','Karnataka','Telengana','Gujarat','Uttar Pradesh','Rajasthan','Delhi','Punjab','Haryana',
 'Tamil Nadu','Madhya Pradesh','Jammu and Kashmir','Ladakh','Andhra Pradesh','West Bengal','Chandigarh','Bihar','Chhattisgarh',
 'Uttarakhand','Goa','Himachal Pradesh','Odisha','Andaman and Nicobar Islands','Manipur','Mizoram','Puducherry']
    count = 0
    for result in final_array:
        confirmed = result[0]
        discharged = result[1]
        deaths = result[2]
        state = states[count]
        save_data = corona_data(state=state,confirmed=confirmed, deaths=deaths, discharged=discharged)
        db.session.add(save_data)
        db.session.commit()     
        count = count + 1   
    
    response = {"message" :"Scraped Successfully!"}
        

    return response

@app.route('/api/delete')
def delete():
    data = corona_data.query.all()
    for i in data:
        db.session.delete(i)
        db.session.commit()
    response = {"message" : "Deleted"}
    return response

@app.route("/api/active_Case/all")
def all_Case():
    data = Case.query.all()
    response = Case_schema.dump(data)
    return jsonify(response)

@app.route('/api/active_Case')
def activeCase():
    url = "https://covid19ind.zaoapp.net/"
    data = requests.get(url)
    soup = BeautifulSoup(data.text, 'html.parser')
    active_Case = []
    for span in soup.find_all("h1"):
        active_Case.append( span.text)
    for i in range(0,1):
        active_Case.pop(i)
    active_Case.pop(0)
    
    confirmed = active_Case[0]
    active = active_Case[1]
    recovered = active_Case[2]
    death = active_Case[3]
    
    case = Case(confirmed = confirmed, active = active,recovered =recovered,death = death)
    db.session.add(case)
    db.session.commit()
    response = {"message" : "Data scraped successfully",'status': 200}
    return response

@app.route('/api/active_Case/delete/<id>')
def delete_active(id):
    case = Case.query.filter_by(id=id).first()
    if case is None:
        response = {"message" : "no such case"}
        return response
    db.session.delete(case)
    db.session.commit()
    response = {"message" : "Deleted"}
    return response
        
   










###################################################
###################################################
### ALL ROUTES WRITTEN HERE ######################
###################################################
###################################################
#
#
# 
# 
# @app.route('/')
# @app.route('/api/state/<api_key>/<state>')
# @app.route('/api/users')
# @app.route('/api/users/<id>')
# @app.route('/users/<email>')
# @app.route('/collect')
# @app.route('/api/delete')
# @app.route('/api/active_Case')
###################################################



    


if __name__ == '__main__':
    app.debug = True
    app.run()     