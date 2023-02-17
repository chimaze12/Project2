import os, requests
from flask import Flask, session, render_template, jsonify, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import text
from urllib.request import urlopen
import json
#import google.auth
#from google.oauth2.credentials import Credentials
#from googleapiclient.discovery import build


#Google Books API Key
GOOGLE_API_KEY = "AIzaSyCbr52PvXpVGoQwlkrLpy-P6hgLZ9O6t3o"
#postgres url
DATABASE_URL = "postgresql://postgres:8253657022@localhost:5432/postgis_33_sample"

app = Flask(__name__)

#Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

# Set up Google Books API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_BOOKS_API_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

@app.route("/", methods=['GET','POST'])
def index():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute(text("SELECT * FROM users WHERE username = :username and password = :password"),
        {"username": username, "password": password} ).fetchone()
        #check if user exist in the database
        if user is None or username is None or password is None:
            return render_template("error.html", message = "username and password does not match")
        else:
            #log the user in
            session["user_id"] = user.username
            return render_template("search.html", username = username)
    #if user has not logged out
    elif session.get("user_id") is not None:
        return render_template("search.html", username = session.get("user_id"))
    # GET request
    else:
        return render_template("index.html")

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        f = request.form.get("fname")
        l = request.form.get("lname")
        u = request.form.get("username")
        p = request.form.get("password")
        cp = request.form.get("confirmpassword")
        e = request.form.get("email")
        # if a field is left empty by the user(tested)
        if u == "" or p == "" or e == "" or cp == "" or f == "" or l == "":
            return render_template("signup.html", message = "Please fill all fields to sign up")
        # if passwords don't match(tested)
        if p != cp:
            return render_template("signup.html", message = "Passwords don't match")
        # if username already exists in database(tested)
        if db.execute(text("SELECT username FROM users WHERE username = :username"),
            {"username": u}).rowcount > 0:
            return render_template("signup.html", message = "Username already exists")
        # unique email check(tested)
        if db.execute(text("SELECT email FROM users WHERE email = :email"),
            {"email": e}).rowcount > 0:
            return render_template("signup.html", message = "Email already exists please use another email")
        # register user into database(tested)
        else:
            db.execute(text("INSERT into users(username, password, email, fname, lname) VALUES (:username,:password,:email,:fname,:lname)"),
            {"username": u, "password": p,"email": e, "fname": f, "lname": l})
            db.commit()
            return render_template("signup.html", text = "Registeration successfull!")

    # Get Request
    return render_template("signup.html")

# logout feature
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return render_template("index.html")

# Search page functionality
@app.route("/search", methods=['GET','POST'])
def search():
    if session.get("user_id") is None:
        render_template("error.html", message = "Login Required")
    if request.method == 'POST':
        user_search = request.form.get("search")
        # user is searching by title
        if request.form.get("inlineRadioOptions") == "option1":
            book_search = db.execute(text("SELECT * FROM books WHERE LOWER(title) LIKE LOWER(:s)"), { "s": '%' + user_search + '%'}).fetchall()
            return render_template("search.html", username = session["user_id"], result = book_search)
        # user is searching by ISBN
        elif request.form.get("inlineRadioOptions") == "option2":
            book_search = db.execute(text("SELECT * FROM books WHERE isbn LIKE LOWER(:s)"), { "s": '%' + user_search + '%'}).fetchall()
            return render_template("search.html", username = session["user_id"], result = book_search)
        # user is searching by author name
        else:
             book_search = db.execute(text("SELECT * FROM books WHERE LOWER(author) LIKE LOWER(:s)"), { "s": '%' + user_search + '%'}).fetchall()
             return render_template("search.html", username = session["user_id"], result = book_search)
    return render_template("search.html", username = session["user_id"])
#book page functionality
@app.route("/book/<string:isbn>", methods=['GET','POST'])
def book(isbn):
    # is user logged in or not
    if session.get("user_id") is None:
        return render_template("error.html", message="Login Required")
    # check if book is in database
    if db.execute(text('SELECT * FROM books WHERE isbn = :isbn'),{"isbn": isbn}).rowcount == 0:
        return render_template("error.html", message="Error 404: Page not found")

    book = db.execute(text('SELECT * FROM books WHERE isbn = :isbn'), {"isbn": isbn}).fetchone()

    if book is None:
        return jsonify({"error": "Book not found"}), 404

    # From Google books reads getting average rating and number of ratings and other keys
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"key": GOOGLE_API_KEY, "q": f"isbn:{isbn}"})
    book_info = res.json()['items'][0]['volumeInfo']
    avg_rating = book_info.get("averageRating")
    rating_count = book_info.get("ratingsCount")
    title_google = book_info['title']
    published_date = book_info['publishedDate']
    author_name = book_info['authors'][0]
    isbn_13 = book_info['industryIdentifiers'][0]['identifier']
    
    jsonobj = {
        "title": title_google,
        "author": author_name,
        "published_date": published_date,
        "isbn_10": book.isbn,
        "isbn_13": isbn_13,
        "review_count": rating_count or None,
        "average_rating": avg_rating or None,
    }
    
    description_google= book_info.get("description")

    if request.method == 'POST':
        u_id = db.execute(text('SELECT * FROM users WHERE username = :u'), {"u": session["user_id"]}).fetchone()
        u_id = u_id.id
        # user has already submitted a review
        if db.execute(text("SELECT * FROM reviews WHERE userid = :u_id"), {"u_id":u_id}).fetchone():
            return render_template("error.html", message="Can't review the same book twice")
        else:
            rating = request.form.get("rating")
            review = request.form.get("review")
            db.execute(text("INSERT into reviews (userid, bookid, rating, text) VALUES (:u_id,:b_id,:rating,:review)"),
            {"u_id": u_id, "b_id": book.id,"rating": rating, "review": review})
            db.commit()
            reviews = db.execute(text('SELECT * FROM reviews WHERE bookid = :b_id'), {"b_id": book.id}).fetchall()
            texxt = "Review submitted"
            return render_template("book.html", book = book, jsonobj=jsonobj, username = session["user_id"], isbn = isbn, reviews = reviews,
            avg_rating = avg_rating,rating_count  = rating_count, text = text)

    reviews = db.execute(text('SELECT * FROM reviews WHERE bookid = :b_id'), {"b_id": book.id}).fetchall()
    return render_template("book.html", book = book, jsonobj=jsonobj, username = session["user_id"], isbn = isbn, reviews = reviews,
    avg_rating = avg_rating,rating_count  = rating_count)



if __name__ == "__main__":
    app.run(debug=True)
