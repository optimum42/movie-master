import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, flash
from data_manager import DataManager
from models import db, User

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv("APP_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Link the database and the app.
data_manager = DataManager()


@app.route('/')
def index():
    """ Renders the home page that shows all users """
    try:
        users = data_manager.get_users()
        return render_template('index.html', users=users)

    except Exception as e:
        db.session.rollback()
        flash(f"Error getting users: {str(e)}", "error")


@app.route('/users/<int:user_id>/movies')
def get_movies(user_id):
    """ Renders the movies page that shows all movies for the given user """
    try:
        # get command line params
        search_query = request.args.get('search')
        sort_by = request.args.get('sort')

        user = data_manager.get_user_by_id(user_id)
        movies = data_manager.get_movies(user_id, search_query, sort_by)
        return render_template('movies.html',
                               movies=movies, user=user)
    except Exception as e:
        db.session.rollback()
        flash(f"Error getting movies: {str(e)}", "error")


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """ Adds a movie to the database """
    try:
        title = request.form.get('title')

        if data_manager.add_movie(user_id, title) == True:
            flash(f"Movie '{title}' successfully added!",
                  "success")
        else:
            flash(f"Movie '{title}' not found or already exist!",
                  "error")

        return redirect(url_for('get_movies', user_id=user_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding the movie: {str(e)}", "error")


@app.route('/users', methods=['POST'])
def add_user():
    """ Adds a user to the database """
    try:
        user_name = request.form.get('name')
        existing_user = data_manager.get_user_by_name(user_name)
        if existing_user:
            # Add "error" as a category
            flash(f"Error: A user with the name '{user_name}' "
                  f"already exists!","error")
        else:
            data_manager.create_user(user_name)
            # Add "success" as a category
            flash(f"User '{user_name}' was added successfully.",
                  "success")

        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding the user: {str(e)}", "error")



@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete',
           methods=['POST'])
def delete_movie(user_id, movie_id):
    """ Deletes a movie link from the users movie list """
    try:
        # The DataManager handles the entire database logic
        # (Deleting the link and cleaning up orphaned movies if necessary)
        data_manager.delete_movie(user_id, movie_id)

        flash("The movie was successfully removed from the list.",
              "success")

        # After deletion, we redirect the user back to their movie list
        return redirect(url_for('get_movies', user_id=user_id))

    except Exception as e:
        # In case a database error occurs (e.g., connection issues)
        db.session.rollback()
        flash(f"Error deleting the movie: {str(e)}", "error")


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update')
def show_update_form(user_id, movie_id):
    """ Shows the update form template for updating a users movie rating """

    try:
        movie = data_manager.get_movie(movie_id)
        link = data_manager.get_user_movie_link(movie_id, user_id)

        return render_template('update_movie.html',
                           movie=movie, user_id=user_id, rating=link.rating)

    except Exception as e:
        # In case a database error occurs (e.g., connection issues)
        db.session.rollback()
        flash(f"Error getting movie info: {str(e)}", "error")


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update',
           methods=['POST'])
def update_movie(user_id, movie_id):
    """ Updates a movie link from the users movie list """

    try:
        new_rating = request.form.get('rating')
        rating_val = float(new_rating) if new_rating else None
        data_manager.update_movie(movie_id, user_id, rating_val)

        movie = data_manager.get_movie(movie_id)
        flash(
            f"The rating for '{movie.title}' was updated successfully!",
            "success")
        return redirect(url_for('get_movies', user_id=user_id))

    except ValueError:
        flash("Invalid rating. Please enter a valid number.",
              "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating the movie: {str(e)}", "error")


if __name__ == '__main__':
    # Only run once on empty database
#    with app.app_context():
#       db.drop_all()
#       db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001)