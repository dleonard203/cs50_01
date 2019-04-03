import os

from flask import Flask, session, render_template, request, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import datetime
import json
#res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "e3j4VgqHagE14fcn1XjkXg","isbns": "9781632168146" })

#database_url = "postgres://ioovleludzhxle:a966a7d36f9e61edd437415d538afd38b89ab723d71177647d3766c32e0b2106@ec2-54-221-243-211.compute-1.amazonaws.com:5432/d3a4ekarkutr2s"

app = Flask(__name__)

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
#engine = create_engine(database_url)
db = scoped_session(sessionmaker(bind=engine))

def assert_login():
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            if not is_logged_in():
                session['messages'] = "Please login to view that page"
                return redirect(url_for('index')) 
            else:
                return f(*args, **kwargs)
        wrapped_f.__name__ = f.__name__
        return wrapped_f
    return wrap    


@app.route("/", methods = ["GET", "POST"])
def index(msg=''):
    if 'messages' in session:
        error_message = session['messages']
        session.pop('messages')
        return render_template('landing.html', msg=error_message)
    if msg != '':
        return render_template("landing.html", msg=msg)
    if request.method == "POST":
        return try_login(request.form)
    else:
        return render_template("landing.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return account_creation_handler(request.form)
    return render_template("register.html")

@app.route("/success")
def success(username):
    return render_template("success.html", username=username)

@app.route("/logout")
@assert_login()
def logout():
    name = session['username']
    session.pop('username')
    return render_template('goodbye.html', name=name)


@app.route('/welcome', methods=["GET"])
@assert_login()
def welcome():
    return render_template('welcome.html', username=session['username'])


def search(req):
    title = req.form['title'].upper()
    isbn = req.form['isbn'].upper()
    author = req.form['author'].upper()
    books = all_books()
    matches = []
    for book in books:
        if book[1].upper().find(isbn) > -1 and book[2].upper().find(title) > -1 and book[3].upper().find(author) > -1:
            matches.append(book)
    return matches


        

@app.route('/results', methods=["POST", "GET"])
@assert_login()
def results():
    books = search(request)
    if len(books) == 0:
        return render_template('results.html', msg = 'Sorry, no books meeting that criteria are available')
    else:
        return render_template('results.html', books = books)
    

@app.route('/book/<string:isbn>', methods=["POST", "GET"])
@assert_login()
def display_results(isbn):
    book = get_book_by_isbn(isbn)
    reviews = get_reviews_by_isbn(isbn)
    goodreads = goodreads_res(isbn)
    if goodreads.status_code == 200:
        content = json.loads(goodreads.content)
        rating = content['books'][0]['average_rating']
        review_count = content['books'][0]['reviews_count']
    else:
        rating = 'N/A'
        review_count = 'N/A'
    if request.method == "GET":
        return render_template('book_details.html', book = book, reviews=reviews, rating=rating, review_count=review_count)
    else:
        username = session['username']
        if user_reviewed(username, isbn):
            msg = 'Sorry, you have already reviewed this book'
        else:
            update_reviews(username, isbn, request.form['content'], request.form['rating'])
            msg = 'Thanks for your review, ' + username
            reviews = get_reviews_by_isbn(isbn)
        return render_template('book_details.html',  book = book, reviews=reviews, msg=msg, rating=rating, review_count=review_count)


@app.route('/api/<string:isbn>')
def goodreads_api(isbn):
    res = goodreads_res(isbn)
    if res.status_code == 200:
        api_content = json.loads(res.content)
        my_book = get_book_by_isbn(isbn)
        if my_book:
            return_dict = {'title': my_book[2], 'author': my_book[3], 'year': my_book[4], 'isbn': isbn, 'review_count': api_content['books'][0]['reviews_count'], 'average_score': api_content['books'][0]['average_rating']}
            return jsonify(return_dict)
    else:
        return not_found(isbn)

@app.route('/not_found')
def not_found(isbn):
    return render_template('not_found.html', isbn=isbn), 404


def goodreads_res(isbn):
    return requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "e3j4VgqHagE14fcn1XjkXg","isbns": isbn})

def get_book_by_isbn(isbn):
    book = db.execute('SELECT * FROM books where isbn = :isbn', {'isbn': isbn}).first()
    return list(book)

def all_books():
    return db.execute('SELECT * FROM books').fetchall()

def update_reviews(username, isbn, review, rating):
    db.execute("INSERT INTO reviews (isbn, username, date, content, rating) VALUES (:isbn, :username, :date, :content, :rating)",
    {'isbn': isbn, 'username': username, 'date': pretty_date(), 'content': review, 'rating': rating})
    db.commit()

def get_reviews_by_isbn(isbn):
    res = db.execute('SELECT * FROM reviews WHERE isbn = :isbn', {'isbn': isbn}).fetchall()
    cache = []
    for rev in res:
        cache.append(rev)
    return cache

def user_reviewed(username, isbn):
    res = db.execute("SELECT * FROM reviews where username = :username and isbn = :isbn", {"username": username, "isbn": isbn}).first()
    if res:
        return True
    return False

def pretty_date():
    res = str(datetime.datetime.now())[:10]
    final = res[5:7] + '/' + res[8:10] + '/' + res[0:4]
    return final


def is_logged_in():
    if 'username' not in session:
        return False 
    else:
        return True


def try_login(form):
    username = form.get("username")
    password = form.get("password")
    db_entry = db.execute("SELECT username, password from users where username = :username", {"username": username}).first()
    if db_entry is None:
        return index(msg = 'No user \'' + username + '\' found')
    elif db_entry[1] != password:
        return index(msg = 'Incorrect password')
    else:
        session['username'] = username
        return welcome()




    

def account_creation_handler(form):
    username = form.get("username")
    password = form.get("password")
    email = form.get("email")
    if username_taken(username):
        return render_template("register.html", err_msg = "Sorry, but the username " + username + " is already in use. Please pick another one.")
    else:
        create_account(username, password, email)
    return success(username)

def username_taken(username):
    sqla_res = db.execute("select count(*) from users where username = :username", {"username": username})
    res = sqla_res.first()[0]
    if res == 0:
        return False
    return True

def create_account(username, password, email):
    sql = "INSERT INTO users (username, password, email) VALUES (:username, :password, :email)"
    db.execute(sql, {"username": username, "password": password, "email": email})
    db.commit()