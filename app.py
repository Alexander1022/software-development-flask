from flask import Flask
from flask import render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

import hashlib
import json
import os.path

from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    else:
        username = request.form['username']
        password = request.form['password']

        try:
            db.session.add(User(username=username, password=password))
            db.session.commit()
            return redirect('/')
            flash('Регистрира се! Вече можеш да влезеш!', 'success')

        except Exception as error: 
            print(error)
            return redirect(request.url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        data = json.loads(request.data.decode('ascii'))
        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if not user or not user.verify_password(password):
            return jsonify({'token': None})

        token = user.generate_token()
        return jsonify({'token': token.decode('ascii')})

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Моля влезте!', 'danger')
            return redirect(url_for('login'))
    return wrap

    
if __name__ == '__main__':
    app.run(debug=True)