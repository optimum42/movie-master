import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, flash
from sqlalchemy import or_
from data_manager import DataManager
from models import db, Movie, User

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("APP_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Link the database and the app. This is the reason you need to import db from models

data_manager = DataManager() # Create an object of your DataManager class


@app.route('/')
def index():
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users/<user_id>/movies')
def list_user_movies(user_id):
    search_query = request.args.get('search')
    sort_by = request.args.get('sort')

    # base query by joining the author
    query = Movie.query.join(User)

    # search filter (title OR author)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(or_(
            Movie.title.ilike(search_term),
            User.name.ilike(search_term)
        ))

    # sorting filter
    if sort_by == 'title':
        query = query.order_by(Movie.title)
    elif sort_by == 'author':
        query = query.order_by(User.name)

    # execute the query
    movies = query.all()

    return render_template('movies.html', movies=movies)


@app.route('/add_user', methods=['POST'])
def add_user():
    user_name = request.form.get('name')

    existing_user = User.query.filter_by(name=user_name).first()

    if existing_user:
        # Füge "error" als Kategorie hinzu
        flash(
            f"Fehler: Ein User mit dem Namen '{user_name}' existiert bereits!",
            "error")
    else:
        data_manager.create_user(user_name)
        # Füge "success" als Kategorie hinzu
        flash(f"User '{user_name}' wurde erfolgreich hinzugefügt.", "success")

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Only run once on empty database
#    with app.app_context():
#        db.drop_all()
#        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001)