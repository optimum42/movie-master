from models import db, User, Movie, UserMovies
from api import omdb_api

import random
from data import blockbusters


class DataManager:
    """
    Handles the database operations
    """

    def user_exists(self, user_name):
        """ checks if the user exists in the database already """
        user = User.query.filter_by(name=user_name).first()
        return user is not None

    def get_user(self, user_id):
        return User.query.get(user_id)

    def create_user(self, name):
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()

    def get_users(self):
        return User.query.all()

    def get_movies(self, user_id, search_query=None, sort_by=None):
        """ Returns all user movies that match the search query """

        # Join Movies with the UserMovies table and filter by user_id
        query = db.session.query(Movie, UserMovies.rating) \
             .join(UserMovies, Movie.id == UserMovies.movie_id) \
             .filter(UserMovies.user_id == user_id)

        # filter by title if the search query is not empty
        if search_query:
            query = query.filter(Movie.title.like("%" + search_query + "%"))

        # # finally sort by the given option
        if sort_by == "title":
            query = query.order_by(Movie.title.asc())
        elif sort_by == "rating":
            query = query.order_by(UserMovies.rating.desc())

        return query.all()

        # result = db.session.query(Movie, UserMovies.rating) \
        #     .join(UserMovies, Movie.id == UserMovies.movie_id) \
        #     .filter(UserMovies.user_id == user_id) \
        #     .all()
        #
        # return result

    def get_movie(self, movie_id, column=""):
        """
        Returns the value of the specified tabel column if it exists,
        else returns the whole movie object
        """
        movie = Movie.query.get(movie_id)
        if column in movie.__table__.columns:
            return movie.__getattribute__(column)
        else:
            return movie

    def get_movie_rating(self, movie_id, user_id):
        """ Returns the rating of a movie for a user """
        link = UserMovies.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if link is None:
            return None
        return link.rating

    def add_movie(self, user_id, title):
        """ Adds a movie to a user's list """
        # check that the user exists
        user = User.query.get(user_id)
        if not user:
            raise Exception(f"User ID '{user_id}' does not exist.")

        # fetch API information to get the correct title and the rating
        data = omdb_api.fetch_movie(title)
        if data is None:
            return False

        title = data.get("Title", title) or title
        rating = data.get("imdbRating", 0)

        # check if the movie already exists globally in the database
        movie = Movie.query.filter_by(title=title).first()

        if not movie:
            movie = Movie(
                title=title,
                director=data.get("Director"),
                year=int(data.get("Year"))
                    if data.get("Year", "").isdigit() else None,
                poster=data.get("Poster"),
                imdb_url=omdb_api.get_imdb_url(title)
            )
            db.session.add(movie)
            db.session.commit()  # Commit so the movie gets an ID (movie.id)!

        # check if the user already has the movie in its list
        link = UserMovies.query.filter_by(user_id=user_id, movie_id=movie.id).first()
        if not link:
            # create the link between User and Movie
            link = UserMovies(user_id=user_id, movie_id=movie.id, rating=rating)
            db.session.add(link)
            db.session.commit()
            return True
        else:
            return False

    def delete_movie(self, user_id, movie_id):
        """ Removes a movie from a user's list """

        # Delete the link between User and Movie, the movie stays in the database
        UserMovies.query.filter_by(user_id=user_id, movie_id=movie_id).delete()
        db.session.commit()


    def user_movie_exists(self, user_id, movie_id):
        """ Checks if the user has already added the movie to their list """
        link = UserMovies.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        return link is not None

    def update_movie(self, movie_id, user_id, rating):
        """ Updates the user's based movie ranking """
        if not self.user_movie_exists(user_id, movie_id):
            return False

        link = UserMovies.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if link is None:
            return False

        link.rating = rating
        db.session.commit()
        return True

    def add_random_movies(self, user_id, movie_number):
        """ Adds random movies to the database """
        added_number = 0
        for i in range(movie_number):
            title = random.choice(blockbusters.TOP_MOVIES)
            if self.add_movie(user_id, title):
                added_number += 1

        return added_number

    def delete_user(self, user_id):
        """ Deletes a user and all its movie links from the database """

        # check if the user exists
        if self.get_user(user_id) is None:
            return False

        # Delete all movie links for the user
        UserMovies.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        # Delete the user
        User.query.filter_by(id=user_id).delete()
        db.session.commit()

        return True
