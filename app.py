from flask import Flask
from flask import render_template, request, redirect, jsonify, flash, get_flashed_messages, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import hashlib, json, os.path
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(30))

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

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

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
    form = LoginForm()
    
    if request.method == 'GET':
        return render_template('login.html')

    else:
        data = json.loads(request.data.decode('ascii'))
        username = data['username']
        password = data['password']
        
        user = User.query.filter_by(username=username).first()

        if not user or not user.verify_password(password): #hash_password(password)?
            return jsonify({'token': None})

        token = user.generate_token()
        #return jsonify({'token': token.decode('ascii')})
        return redirect('/')
        flash('Успешно влезнахте!', 'success')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    else:
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Ниикнеймът е зает :( Опитайте с друг.')
        try:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()            
            flash('Вие се регистрирахте успешно!')
            return redirect('login')

        except Exception as error: 
            return redirect(request.url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

if __name__ == '__main__':
    app.run(debug=True)



