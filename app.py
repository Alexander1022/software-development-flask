from flask import Flask
from flask import render_template, request, redirect, jsonify, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import json
import os.path

from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "asdfghjkjytrewsdcv"

db = SQLAlchemy(app)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_token(token):
    s = Serializer(app.secret_key)
    try:
        s.loads(token)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    return True

class User(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __init__(self, **kwargs):
        if 'password' in kwargs:
            kwargs['password'] = hash_password(kwargs['password'])
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return '<User %r>' % self.username

    def verify_password(self, password):
        return self.password == hash_password(password)

    def generate_token(self):
        s = Serializer(app.secret_key, expires_in=600)
        return s.dumps({'username': self.username})

    @staticmethod
    def find_by_token(token):
        if not token:
            return None

        try:
            s = Serializer(app.secret_key)
            payload = s.loads(token)
            return User.query.filter_by(username=payload.get('username')).first()
        except SignatureExpired:
            return None

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	author = db.Column(db.String(100), nullable=False)
	content = db.Column(db.String(500), nullable=False)
	#author = db.relationship('User', foreign_keys='User.id')
	timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

db.create_all()

@app.route('/')
def index():
    return render_template('mainpage.html')

@app.route('/posts')
def posts():
    return render_template('posts.html')

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        #res = Post.query.all()
        return render_template('login.html')
    else:
        data = json.loads(request.data.decode('ascii'))
        username = data['username']
        password = data['password']
        
        user = User.query.filter_by(username=username).first()

        if not user or not user.verify_password(password):#hash_password(password)?
            return jsonify({'token': None})

        token = user.generate_token()
        return jsonify({'token': token.decode('ascii')})
        return redirect('/')
        flash('You are now logged in', 'success')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    else:
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Already taken username')
        try:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            #return render_template('register.html')            
            flash('You are now registered and can log in', 'success')
            return redirect('login')


        except Exception as error: 
            return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True)



