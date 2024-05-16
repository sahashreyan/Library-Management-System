from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
db = SQLAlchemy()
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    __tablename__ = 'Book'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer, nullable=False, unique=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(100), db.ForeignKey('Section.name'), nullable=False)
    content = db.Column(db.Text(), nullable=True)
    copies = db.Column(db.Integer, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)
    section_rel = db.relationship('Section', backref='books')


class Section(db.Model):
    __tablename__ = 'Section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique = True)
    description = db.Column(db.Text(), nullable=True)
    
class BorrowedBook(db.Model):
    __tablename__ = 'BorrowedBook'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('Book.id'), nullable=False)
    book_title = db.Column(db.String(100), nullable=False)
    section_name = db.Column(db.String(100), db.ForeignKey('Section.name'), nullable=False)
    borrowed_date = db.Column(db.Date, nullable=False)
    number_of_days = db.Column(db.Integer, nullable=False)
    returned = db.Column(db.Boolean, nullable=False, default=False)
    return_date = db.Column(db.Date, nullable=True)

    section_rel = db.relationship('Section', backref=db.backref('Borrowed_book', lazy=True))
    user = db.relationship('User', backref=db.backref('Borrowed_book', lazy=True))
    book = db.relationship('Book', backref=db.backref('Borrowed_book', lazy=True))


class Requests(db.Model):
    __tablename__ = 'Requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('Book.id'), nullable=False)
    book_title = db.Column(db.String(100), nullable=False)
    section_name = db.Column(db.String(100), db.ForeignKey('Section.name'), nullable=False)
    request_date = db.Column(db.Date, nullable=False,default=datetime.utcnow().date())
    number_of_days = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)

    book = db.relationship('User', backref=db.backref('Requests', lazy=True))
    section = db.relationship('Section', backref=db.backref('Requests', lazy=True))

class Feedback(db.Model):
    __tablename__ = 'Feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('Book.id'), nullable=False)
    book_title = db.Column(db.String(100), nullable=False)
    book_author = db.Column(db.String(100), nullable=False)
    section_name = db.Column(db.String(100), db.ForeignKey('Section.name'), nullable=False)
    feedback = db.Column(db.Text(), nullable=False)
    feedback_date = db.Column(db.Date, nullable=False,default=datetime.utcnow().date())

    user = db.relationship('User', backref=db.backref('Feedback', lazy=True))
    



