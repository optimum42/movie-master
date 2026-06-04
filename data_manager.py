from models import db, User, Movie, UserMovies
from api.omdb_api import *


class DataManager():
    """
    Handles database operations for a Many-to-Many Movie Architecture
    """

    def create_user(self, name):
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()

    def get_users(self):
        return User.query.all()

    def get_movies(self, user_id):
        # Join Movies with the UserMovies table
        # and filter by user_id
        return Movie.query.join(UserMovies).filter(
            UserMovies.user_id == user_id).all()

    def add_movie(self, user_id, title):
        # 1. Check that user exists
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User does not exist.")

        # 2. Check if the movie already exists globally in the database
        # We use ilike to ignore case sensitivity
        movie = Movie.query.filter(Movie.title.ilike(title)).first()
        if movie:
            return False

        # fetch movie details from the API and create it
        data = fetch_movie(title)
        if data is None:
            return False

        movie = Movie(
            title=data.get("Title", title),
            # Use the title from the API (often cleaner)
            director=data.get("Director"),
            # Safely convert Year to an integer, if present
            year=int(data.get("Year")) if data.get("Year",
                                                   "").isdigit() else None,
            rating=data.get("imdbRating"),
            poster=data.get("Poster"),
            imdb_url=get_imdb_url(title)
        )
        db.session.add(movie)
        db.session.commit()  # Commit so the movie gets an ID (movie.id)!

        # 4. Check if THIS user already has the movie in THEIR list
        existing_link = UserMovies.query.filter_by(user_id=user_id,
                                                   movie_id=movie.id).first()

        if not existing_link:
            # 5. Create the link between User and Movie
            new_link = UserMovies(user_id=user_id, movie_id=movie.id)
            db.session.add(new_link)
            db.session.commit()
            return True
        else:
            return False


    def delete_movie(self, user_id, movie_id):
        """
        Removes a movie from a user's list.
        Optional: Deletes the movie completely if no user has it anymore.
        """
        # 1. Delete the link between User and Movie
        link = UserMovies.query.filter_by(user_id=user_id,
                                          movie_id=movie_id).first()
        if link:
            db.session.delete(link)
            db.session.commit()

        # 2. Cleanup (Optional, but recommended):
        # Does anyone else still have this movie in their list?
        remaining_links = UserMovies.query.filter_by(movie_id=movie_id).count()
        if remaining_links == 0:
            # No one has the movie anymore -> delete completely from the database
            movie = Movie.query.get(movie_id)
            if movie:
                db.session.delete(movie)
                db.session.commit()

        return True

    def update_movie(self, movie_id, **kwargs):
        """
        Updates global movie data.
        Since the movie is now shared globally, this changes it for ALL users!
        """
        movie = Movie.query.get(movie_id)
        if not movie:
            return False

        # Iterate over the provided key-value pairs and update attributes
        for key, value in kwargs.items():
            if hasattr(movie, key):
                setattr(movie, key, value)

        db.session.commit()
        return True