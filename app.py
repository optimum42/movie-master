import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, flash
from models import db
from data_manager import DataManager

load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv("APP_SECRET_KEY")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Link the database and the app.
data_manager = DataManager()


### Flask Routes
@app.route('/')
def index():
    """ Renders the home page that shows all users """
    users = []
    try:
        users = data_manager.get_users()

    except Exception as e:
        db.session.rollback()
        flash(f"Error getting users: {str(e)}", "error")

    return render_template('index.html', users=users)


@app.route('/users/<int:user_id>/movies')
def show_movies(user_id):
    """ Renders the movies page that shows all movies for the given user """
    try:
        # get command line params
        search_query = request.args.get('search')
        sort_by = request.args.get('sort')

        user = data_manager.get_user(user_id)
        movies = data_manager.get_movies(user_id, search_query, sort_by)

        return render_template('movies.html',
                               movies=movies, user=user)

    except Exception as e:
        db.session.rollback()
        flash(f"Error getting movies: {str(e)}", "error")

        return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """ Adds a movie to the database """

    title = request.form.get('title')
    if title.startswith('***'):
        # hidden feature ***n that seeds the library with n random movies
        try:
            add_random_movies(user_id, int(title[3:]))
        except ValueError:
            flash("To randomly add movies type '***X' where X is a number between 1 and 100.",
                  "error")
    else:
        try:
            # normal add_movie flow
            if data_manager.add_movie(user_id, title):
                flash(f"Movie '{title}' successfully added!",
                      "success")
            else:
                flash(f"Movie '{title}' not found or already exist!",
                      "error")

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding the movie: {str(e)}", "error")

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/random/<int:movie_number>')
def add_random_movies(user_id, movie_number):
    """ Adds n random movies to the database for the given user """
    try:
        if movie_number < 1 or movie_number > 100:
            flash("To randomly add movies type '***X' where X is a number between 1 and 100.",
                  "error")
        else:
            movies_added = data_manager.add_random_movies(user_id, movie_number)
            if movies_added > 0:
                msg = f"{movies_added} Random movies added successfully!" \
                    if movies_added > 1 else "1 Random movie added successfully!"
                flash(msg,"success")
            else:
                flash("No movies were added.",
                      "error")

    except ValueError:
        flash("To randomly add movies type '***X' where X is a number between 1 and 100.",
              "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding the movie: {str(e)}", "error")

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users', methods=['POST'])
def add_user():
    """ Adds a user to the database """
    try:
        user_name = request.form.get('name')
        if data_manager.user_exists(user_name):
            flash(f"Error: A user with the name '{user_name}' "
                  f"already exists!","error")
        else:
            data_manager.create_user(user_name)
            flash(f"User '{user_name}' was added successfully.",
                  "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding the user: {str(e)}", "error")

    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete',
           methods=['POST'])
def delete_movie(user_id, movie_id):
    """ Deletes a movie link from the users movie list """
    try:
        title = data_manager.get_movie(movie_id, "title")
        data_manager.delete_movie(user_id, movie_id)
        flash(f"The movie '{title}' was successfully removed from the list.",
              "success")

    except Exception as e:
        # In case a database error occurs (e.g., connection issues)
        db.session.rollback()
        flash(f"Error deleting the movie: {str(e)}", "error")

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update')
def show_update_form(user_id, movie_id):
    """ Shows the update form template for updating a users movie rating """

    try:
        movie = data_manager.get_movie(movie_id)
        rating = data_manager.get_movie_rating(movie_id, user_id)

        return render_template('update_movie.html',
                           movie=movie, user_id=user_id, rating=rating)

    except Exception as e:
        # In case a database error occurs (e.g., connection issues)
        db.session.rollback()
        flash(f"Error getting movie info: {str(e)}", "error")

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update',
           methods=['POST'])
def update_movie(user_id, movie_id):
    """ Updates a movie rating from the users movie list """

    try:
        new_rating = request.form.get('rating')
        rating_val = float(new_rating) if new_rating else None
        data_manager.update_movie(movie_id, user_id, rating_val)

        title = data_manager.get_movie(movie_id, "title")
        flash(f"The rating for '{title}' was updated successfully!",
              "success")

    except ValueError:
        flash("Invalid rating. Please enter a valid number.",
              "error")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating the movie: {str(e)}", "error")

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users/<int:user_id>/delete')
def authorize_delete_user(user_id):
    """ Authorizes the user to delete their account """
    return render_template('password.html', user_id=user_id,
                           callback=url_for('delete_user', user_id=user_id))


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """ Deletes a user from the database """
    try:
        password = request.form.get('password')
        if password != os.getenv("ADMIN_PASSWORD"):
            flash("Incorrect password.", "error")
            return redirect(url_for('authorize_delete_user', user_id=user_id))

        data_manager.delete_user(user_id)
        flash("User successfully removed.",
              "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting the user: {str(e)}", "error")

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Only run once on the empty database
#    with app.app_context():
#       db.drop_all()
#       db.create_all()

    app.run(debug=True , host='0.0.0.0', port=5001)