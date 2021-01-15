from flask import Flask, render_template
from static_info import Posts, Users
app = Flask(__name__)

user_posts = Posts()
p_users = Users()

@app.route('/')
def index():
    return render_template('mainpage.html')

@app.route('/posts')
def posts():
    return render_template('posts.html', user_posts = user_posts)

@app.route('/users')
def users():
    return render_template('users.html', users = p_users)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)