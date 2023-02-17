import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class items (db.Model):
    __tablename__ = "bouk"
    id = db.Column(db.Integer, primary_key = True)
    isbn10 = db.Column(db.String, unique = True, nullable = False)
    isbn13 = db.Column(db.String, unique = True, nullable = False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    published_date = db.Column(db.String, unique = True, nullable = False)
    year = db.Column(db.Integer, nullable=False)
    average_rating = db.Column(db.String, unique = True, nullable = False)
    recount_view = db.Column(db.String, unique = True, nullable = False)
    reviews = db.relationship("Review", backref="book", lazy=True)


class Book (db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key = True)
    isbn = db.Column(db.String, unique = True, nullable = False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    reviews = db.relationship("Review", backref="book", lazy=True)


    def add_review(self, user_id, text, rating):
        r = Review(user_id = user_id, book_id = self.id, text = text, rating = rating)
        db.session.add(r)
        db.session.commit()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    fname = db.Column(db.String, nullable = False)
    lname = db.Column(db.String, nullable = False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique = True, nullable=False)

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    bookid = db.Column(db.Integer, db.ForeignKey("books.id"), nullable = False)
    text = db.Column(db.String, nullable = True)
    rating = db.Column(db.Integer, nullable = False)
 