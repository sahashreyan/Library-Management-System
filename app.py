from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor
from models.models import *
from datetime import datetime, date, timedelta
from matplotlib import pyplot as plt
import numpy as np
import io
import base64

app = Flask(__name__)
app.secret_key = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def start_db():
    with app.app_context():
        db.init_app(app)
        db.create_all()

with app.app_context():
    start_db()


librarian_credentials = {
    "username": "admin",
    "password": "password123"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/librarian-login', methods=['GET', 'POST'])
def librarian_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == librarian_credentials['username'] and password == librarian_credentials['password']:
            session['logged_in'] = True
            session['admin'] = True
            return redirect(url_for('librarian_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('librarian_login'))
    return render_template('librarian_login.html')

    

@app.route('/librarian-dashboard',methods = ['GET', 'POST'])
def librarian_dashboard():
    if session.get('logged_in') and session.get('admin'):
        if request.method == 'GET':
            requests = Requests.query.all()
            return render_template('librarian_dashboard.html',requests=requests)          
    else:
        return redirect(url_for('librarian_login'))

@app.route('/approve-bookrequest/<int:id>', methods = ['GET', 'POST']) # type: ignore
def approve_request(id):
    if request.method == 'GET':
        requested_book_id = Requests.query.filter_by(id=id).first().book_id
        if session.get('logged_in') and session.get('admin'):
            if(Book.query.filter_by(id=requested_book_id).first().available_copies == 0):
                return redirect(url_for('librarian_dashboard',message='Book not available'))
            else:
                bookrequest = Requests.query.filter_by(id=id).first()
                bookrequest.status = 'Approved'
                user_id = bookrequest.user_id
                username = bookrequest.username
                book_id = bookrequest.book_id
                book_title = bookrequest.book_title
                section_name = bookrequest.section_name
                number_of_days = bookrequest.number_of_days
                borrowed_date = bookrequest.request_date
                return_date = borrowed_date + timedelta(days=number_of_days)
                book = Book.query.filter_by(id=book_id).first()
                book.available_copies = book.available_copies - 1
                new_bookrequest = BorrowedBook(user_id=user_id,username=username,book_id=book_id, book_title = book_title, section_name=section_name, number_of_days = number_of_days ,borrowed_date=borrowed_date,return_date=return_date)
                db.session.add(new_bookrequest)
                db.session.commit()
                return redirect(url_for('librarian_dashboard'))
        else:
            return redirect(url_for('index'))
   
    
@app.route('/reject-request/<int:id>', methods = ['GET', 'POST']) # type: ignore
def reject_request(id):
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            book_request = Requests.query.filter_by(id=id).first()
            book_request.status = 'Rejected'
            db.session.commit()
            return redirect(url_for('librarian_dashboard'))
        else:
            return redirect(url_for('index'))
        
@app.route('/revoke-requests', methods = ['GET', 'POST']) # type: ignore
def revoke_requests():
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            borrowed_books = BorrowedBook.query.all()
            for book in borrowed_books:
                if book.return_date < datetime.utcnow().date():
                    book.returned = True
                    getbook = Book.query.filter_by(id=book.book_id).first()
                    getbook.available_copies = getbook.available_copies + 1
                    db.session.commit()
            return redirect(url_for('librarian_dashboard'))  
        else:
            return redirect(url_for('index'))  
@app.route('/add-user', methods=['GET', 'POST']) # type: ignore
def add_user():
    if request.method == 'POST':
        if session.get('logged_in') and not session.get('admin'):
            username = request.form['username']
            password = request.form['password']
            user = User(username=username, password = password)
            if user.username not in [u.username for u in User.query.all()]:
                db.session.add(user)
                db.session.commit()
                message = 'User added successfully'
                return redirect(url_for('add_user',message=message,type="success"))
            else:
                message = 'User already exists'
                return redirect(url_for('add_user',message=message))
        else:
            return redirect(url_for('index'))
    if request.method == "GET":
        if request.args.get('message'):
            message = request.args.get('message')
            if request.args.get('type'):
                return render_template('add_user.html',message = message,type="success")
            else:
                return render_template('add_user.html',message = message)
        return render_template('add_user.html') 
    
@app.route('/delete-user/<int:id>', methods = ['GET', 'POST']) # type: ignore
def delete_user(id):
    if request.method == 'GET':
        if session.get('logged_in') and not session.get('admin'):
            user = User.query.filter_by(id=id).first()
            user_borrowed_book = BorrowedBook.query.filter_by(user_id=id).all()
            user_requests = Requests.query.filter_by(user_id=id).all()
            if user_borrowed_book or user_requests:
                for book in user_borrowed_book:
                    db.session.delete(book)
                for user_request in user_requests:
                    db.session.delete(user_request)
            db.session.delete(user)
            db.session.commit()
            message = 'User deleted successfully'
            return redirect(url_for('view_users',message=message,type="success"))
        else:
            return redirect(url_for('index'))

@app.route('/delete-book/<int:id>', methods = ['GET', 'POST']) # type: ignore
def delete_book(id):
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            book = Book.query.filter_by(id=id).first()
            book_requests = Requests.query.filter_by(book_id=id).all()
            book_borrowed_books = BorrowedBook.query.filter_by(book_id=id).all()
            if book_requests or book_borrowed_books:
                for book_request in book_requests:
                    db.session.delete(book_request)
                for borrowed_book in book_borrowed_books:
                    db.session.delete(borrowed_book)
            db.session.delete(book)
            db.session.commit()
            message = 'Book deleted successfully'
            return redirect(url_for('librarian_view_books',message=message,type="success"))
        else:
            return redirect(url_for('index'))

@app.route('/delete-section/<int:id>', methods = ['GET', 'POST']) # type: ignore
def delete_section(id):
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            section = Section.query.filter_by(id=id).first()
            section_books = Book.query.filter_by(section=section.name).all()
            if section_books:
                for book in section_books:
                    book_requests = Requests.query.filter_by(book_id=book.id).all()
                    book_borrowed_books = BorrowedBook.query.filter_by(book_id=book.id).all()
                    if book_requests or book_borrowed_books:
                        for book_request in book_requests:
                            db.session.delete(book_request)
                        for borrowed_book in book_borrowed_books:
                            db.session.delete(borrowed_book)
                    db.session.delete(book)
            db.session.delete(section)
            db.session.commit()
            message = 'Section deleted successfully'
            return redirect(url_for('view_sections',message=message,type="success"))
        else:
            return redirect(url_for('index'))
    
@app.route('/add-book', methods=['GET', 'POST']) # type: ignore
def add_book():
    if request.method=='GET':
        if session.get('logged_in') and session.get('admin'):
            section = Section.query.all()
            return render_template('add_book.html',sections=section)
        else:
            return redirect(url_for('index'))
    if request.method == 'POST':
        isbn = request.form.get("isbn")
        title = request.form.get('title')
        author = request.form.get('author')
        section = request.form.get('section')
        content = request.form.get('content')
        copies = request.form.get('copies')
        available_copies = request.form.get('available_copies')
        book=Book.query.filter_by(isbn=isbn).first()
        if book:
            message= 'Book already exists'
            return redirect(url_for('add_book',message=message))
        else:
            book = Book(isbn=isbn, title=title, author=author, section=section, content=content, copies=copies, available_copies=available_copies)
            db.session.add(book)
            db.session.commit()
            message= 'Book added successfully'
            return redirect(url_for('add_book',message=message,type="success"))

                
        
    
@app.route('/add-section', methods=['GET', 'POST']) # type: ignore
def add_section():
    if request.method == 'POST':
        if session.get('logged_in') and session.get('admin'):
            name = request.form['name']
            name = name.upper()
            description = request.form['description']
            section= Section.query.filter_by(name=name).first()
        else:
            return redirect(url_for('index'))
        if section:
            message= 'Section already exists'
            return redirect(url_for('add_section',message=message))
        else:
            section = Section(name=name, description=description) # type: ignore
            db.session.add(section)
            db.session.commit()
            message= 'Section added successfully'
            return redirect(url_for('add_section',message=message,type="success"))
    if request.method == "GET":
        if request.args.get('message'):
            message = request.args.get('message')
            if request.args.get('type'):
                return render_template('add_section.html',message=message,type="success")
            else:
                return render_template('add_section.html', message=message)
        return render_template('add_section.html')

@app.route('/librarian-view-books', methods = ['GET', 'POST']) 
def librarian_view_books():
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            message = request.args.get('message')
            books = Book.query.all()
            if message:
                return render_template('librarian_view_books.html',books=books,message=message)
            else:
                return render_template('librarian_view_books.html',books=books)
        else:
            return redirect(url_for('index'))

@app.route('/view-sections', methods = ['GET', 'POST'])
def view_sections():
    if request.method == 'GET':
        message = request.args.get('message')
        sections = Section.query.all()
        for section in sections:
            section.total_book = len(Book.query.filter_by(section=section.name).all())
        if message:
            return render_template('view_sections.html',sections=sections,message=message)
        else:
            return render_template('view_sections.html',sections=sections)

@app.route('/view-users', methods = ['GET', 'POST'])
def view_users():
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            message = request.args.get('message')
            users = User.query.all()
            for user in users:
                user.total_borrowed_books = len(BorrowedBook.query.filter_by(user_id=user.id).all())
                user.total_returned_books = len(BorrowedBook.query.filter_by(user_id=user.id,returned=True).all()) 
            if message:
                return render_template('view_users.html',users=users,message=message)
            else:
                return render_template('view_users.html',users=users)
        else:
            return redirect(url_for('index'))
    
@app.route('/edit-book/<int:id>', methods = ['GET', 'POST']) # type: ignore
def edit_book(id):
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            book = Book.query.filter_by(id=id).first()
            section = Section.query.all()
            return render_template('edit_book.html',book=book,sections=section)
        else:
            return redirect(url_for('index'))
    if request.method == 'POST':
        isbn = request.form.get("isbn")
        title = request.form.get('title')
        author = request.form.get('author')
        section = request.form.get('section')
        content = request.form.get('content')
        copies = request.form.get('copies')
        available_copies = request.form.get('available_copies')
        book = Book.query.filter_by(id=id).first()
        book.isbn = isbn
        book.title = title
        book.author = author
        book.section = section
        book.content = content
        book.copies = copies
        book.available_copies = available_copies

        borrowedbook = BorrowedBook.query.filter_by(book_id=id).all()
        for book in borrowedbook:
            book.section_name = section
            book.book_title = title
        
        requestedbook = Requests.query.filter_by(book_id=id).all()
        for book in requestedbook:
            book.section_name = section
            book.book_title = title

        db.session.commit()
        return redirect(url_for('librarian_view_books'))
    
@app.route('/edit-section/<int:id>', methods = ['GET', 'POST'])
def edit_section(id):
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            section = Section.query.filter_by(id=id).first()
            return render_template('edit_section.html',section=section)
        else:
            return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        section = Section.query.filter_by(id=id).first()
        section.name = name
        section.description = description

        requestedbook = Requests.query.filter_by(section_name=section.name).all()   
        for book in requestedbook:
            book.section_name = name

        borrowedbook = BorrowedBook.query.filter_by(section_name=section.name).all()
        for book in borrowedbook:
            book.section_name = name

        db.session.commit()
        return redirect(url_for('view_sections'))
    
@app.route('/view-feedbacks', methods = ['GET', 'POST']) # type: ignore
def view_feedbacks():
    if request.method == 'GET':
        if session.get('logged_in') and session.get('admin'):
            feedbacks = Feedback.query.all()
            return render_template('view_feedbacks.html',feedbacks=feedbacks)
        else:
            return redirect(url_for('index'))

    
@app.route('/librarian-charts', methods=['GET', 'POST'])
def librarian_charts():
    sections = Section.query.all()
    section_names = [section.name for section in sections]
    book_count = [len(section.books) for section in sections]
    BorrowedBook_count = [len(section.Borrowed_book) for section in sections]
    return render_template('librarian_charts.html',section_name=section_names,book_count=book_count,borrowed_books = BorrowedBook_count)

    

@app.route('/user-signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password = password) # type: ignore
        if user.username not in [u.username for u in User.query.all()]:
            db.session.add(user)
            db.session.commit()
            message = 'User added successfully'
            return redirect(url_for('user_login'))
        else:
            message = 'User already exists'
            return redirect(url_for('user_login'))
    return render_template('user_signup.html')



    
@app.route('/user-login', methods=['GET', 'POST']) # type: ignore
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.username == username and user.password == password:
                session['logged_in'] = True
                session['id']=user.id
                user = session.get('logged_in')
                return redirect(url_for('user_dashboard'))
            else:
                message = 'Invalid credentials'
                return redirect(url_for('user_login',message=message))
        else:
            message = 'User does not exist, please signup'
            return redirect(url_for('user_signup', message=message))
    if request.method == 'GET':
        if request.args.get('message'):
            message = request.args.get('message')
            if request.args.get('type'):
                return render_template('user_login.html',message=message,type="success")
            else:
                return render_template('user_login.html', message=message)
        return render_template('user_login.html')
    

@app.route('/user-dashboard', methods=['GET', 'POST']) # type: ignore
def user_dashboard():
    if session.get('logged_in'):
        if request.method == 'GET':
            user = User.query.filter_by(id=session.get('id')).first()

            borrowed_count = BorrowedBook.query.filter_by(returned = False,user_id = session.get('id')).count()
            completed_count = BorrowedBook.query.filter_by(returned = True,user_id = session.get('id')).count()

            sections = db.session.query(BorrowedBook.section_name, db.func.count(BorrowedBook.id)).filter_by(user_id=session.get('id')).group_by(BorrowedBook.section_name).all()
            section_names = [section[0] for section in sections]
            section_counts = [section[1] for section in sections]

            return render_template('user_dashboard.html',user=user, borrowed_count=borrowed_count, completed_count=completed_count,section_names=section_names,section_counts=section_counts)
    else:
        message = 'Please login to access this page'
        return redirect(url_for('user_login'),message=message)
           
@app.route('/user-view-books', methods = ['GET', 'POST']) 
def user_view_books():
    if request.method == 'GET':
        books = Book.query.all()
        if message := request.args.get('message'):
            return render_template('user_view_books.html',books=books,message = message)
        else:
            return render_template('user_view_books.html',books=books)

@app.route('/user-view-sections', methods = ['GET', 'POST']) 
def user_view_sections():
    if request.method == 'GET':
        user = User.query.filter_by(id=session.get('id')).first()
        sections = Section.query.all()
        for section in sections:
            section.total_book = len(Book.query.filter_by(section=section.name).all())
        return render_template('user_view_sections.html',sections=sections,user=user)

        
    
@app.route('/request-book/<int:id>', methods = ['GET', 'POST']) # type: ignore
def request_book(id):
    user_id = session.get('id')
    if request.method == 'GET':
        if not session.get('logged_in'):
            return redirect(url_for('user_login'))
        elif Book.query.filter_by(id=id).first().available_copies == 0:
            return redirect(url_for('user_view_books',message="Book not available"))
        elif Requests.query.filter_by(user_id=user_id,book_id=id,status='Pending').first():
            return redirect(url_for('user_view_books',message="You have already requested this book"))
        elif BorrowedBook.query.filter_by(user_id=user_id,book_id=id,returned=False).first():
            message = 'You have already borrowed this book'
            return redirect(url_for('user_view_books',message=message))
        elif len(BorrowedBook.query.filter_by(user_id=user_id,returned = False).all())+len(Requests.query.filter_by(user_id = user_id, status = 'Pending').all())==5: 
            message = 'You are not allowed to request for more books'
            return redirect(url_for('user_view_books',message=message))
        else:
            book = Book.query.filter_by(id=id).first()
            section_name = Book.query.filter_by(id=id).first().section
            return render_template('request_book.html',book=book, user_id=user_id,section_name=section_name)
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        username = User.query.filter_by(id=user_id).first().username
        book_id = request.form.get('book_id')
        book_title = Book.query.filter_by(id=id).first().title
        section_name = request.form.get('section_name')
        number_of_days = request.form.get('number_of_days')
        status = 'Pending'
        new_request = Requests(user_id=user_id,username = username,book_id=book_id, book_title = book_title, section_name=section_name, number_of_days = number_of_days ,status=status)
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('user_dashboard'))

@app.route('/mybooks/<int:id>', methods = ['GET', 'POST']) # type: ignore
def my_books(id):
    if request.method == 'GET':
        if session.get('logged_in'):
            user = User.query.filter_by(id=id).first()
            borrowedbooks = BorrowedBook.query.filter_by(user_id=id).all()
            return render_template('mybooks.html',borrowedbooks=borrowedbooks, user=user)
        else:
            return redirect(url_for('user_login'))

@app.route('/read-book/<int:id>', methods = ['GET', 'POST']) # type: ignore
def read_book(id):
    if request.method == 'GET':
        if session.get('logged_in'):
            user = session.get('id')
            bookid = BorrowedBook.query.filter_by(id=id).first().book_id
            book = Book.query.filter_by(id = bookid).first()
            return render_template('read_book.html',book=book, user=user)
        else:
            return redirect(url_for('user_login'))


@app.route('/return-book/<int:id>', methods = ['GET', 'POST']) # type: ignore
def return_book(id):
    if request.method == 'GET':
        if session.get('logged_in'):
            book = BorrowedBook.query.filter_by(id=id).first()
            book.author = Book.query.filter_by(id=book.book_id).first().author
            return render_template('feedback.html',book = book)
        else:
            return redirect(url_for('user_login'))
    if request.method == 'POST':
        user_id = session.get('id')
        username = User.query.filter_by(id=user_id).first().username
        book_id = BorrowedBook.query.filter_by(id=id).first().book_id
        book_title = request.form.get('book_title')
        book_author = request.form.get('book_author')
        section_name = request.form.get('section_name')
        feedback = request.form.get('feedback')
        feedback_date = datetime.utcnow().date()
        new_feedback = Feedback(user_id=user_id,username=username,book_id=book_id, book_title = book_title, book_author=book_author, section_name=section_name, feedback=feedback, feedback_date=feedback_date)
        db.session.add(new_feedback)
        borrowedbook = BorrowedBook.query.filter_by(id=id).first()
        borrowedbook.returned = True
        borrowedbook.return_date = datetime.utcnow().date()
        book = Book.query.filter_by(id=book_id).first()
        book.available_copies = book.available_copies + 1
        db.session.commit()
        return redirect(url_for('my_books',id=user_id))

@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

