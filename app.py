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


@app.route('/users/<int:user_id>/movies')
def get_movies(user_id):
    # 1. Fetch the user (still needed for the template: user.name, user.id)
    # get_or_404 is useful here in case someone types an invalid ID into the URL
    user = User.query.get_or_404(user_id)

    # 2. Load the movies EXCLUSIVELY via the DataManager
    movies = data_manager.get_movies(user_id)

    # 3. Render the template with the data
    return render_template('movies.html', movies=movies, user=user)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    title = request.form.get('title')

    try:
        if data_manager.add_movie(user_id, title) == True:
            flash(f"Movie '{title}' successfully added!",
                  "success")
        else:
            flash(f"Movie '{title}' not found or already exist!",
                  "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users', methods=['POST'])
def add_user():
    user_name = request.form.get('name')

    existing_user = User.query.filter_by(name=user_name).first()

    if existing_user:
        # Add "error" as a category
        flash(
            f"Error: A user with the name '{user_name}' already exists!",
            "error")
    else:
        data_manager.create_user(user_name)
        # Add "success" as a category
        flash(f"User '{user_name}' was added successfully.", "success")

    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete',
           methods=['POST'])
def delete_movie(user_id, movie_id):
    try:
        # The DataManager handles the entire database logic
        # (Deleting the link and cleaning up orphaned movies if necessary)
        data_manager.delete_movie(user_id, movie_id)

        flash("The movie was successfully removed from the list.", "success")
    except Exception as e:
        # In case a database error occurs (e.g., connection issues)
        db.session.rollback()
        flash(f"Error deleting the movie: {str(e)}", "error")

    # After deletion, we redirect the user back to their movie list
    return redirect(url_for('get_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update',
           methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    # Load movie and user from the database
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # If the form was submitted:
        new_rating = request.form.get('rating')

        try:
            # Convert string to float
            rating_val = float(new_rating) if new_rating else None

            # Use DataManager to update the 'rating' attribute
            data_manager.update_movie(movie_id, rating=rating_val)

            flash(
                f"The rating for '{movie.title}' was updated successfully!",
                "success")
            return redirect(url_for('get_movies', user_id=user_id))

        except ValueError:
            flash("Invalid rating. Please enter a valid number.",
                  "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")

    # If it's a GET request: Render the HTML form
    return render_template('update_movie.html', movie=movie, user=user)


if __name__ == '__main__':
    # Only run once on empty database
    # with app.app_context():
    #    db.drop_all()
    #    db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001)