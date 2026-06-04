from models import db, User, Movie, UserMovies
from api.omdb_api import fetch_movie, get_imdb_url


class DataManager():
    """
    Handles database operations for all three tables
    """

    def create_user(self, name):
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit()

    def get_users(self):
        return User.query.all()

    def get_user_by_id(self, user_id):
        return User.query.get(user_id)

    def get_user_by_name(self, user_name):
        return User.query.filter_by(name=user_name).first()

    def get_movies(self, user_id):
        # Join Movies with the UserMovies table
        # and filter by user_id
        result = db.session.query(Movie, UserMovies.rating) \
            .join(UserMovies, Movie.id == UserMovies.movie_id) \
            .filter(UserMovies.user_id == user_id) \
            .all()

        return result

    def get_movie(self, movie_id):
        movie = Movie.query.get(movie_id)
        return movie

    def get_user_movie_link(self, movie_id, user_id):
        link = UserMovies.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        return link

    def add_movie(self, user_id, title):
        # check that user exists
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User does not exist.")

        # first fetch API information to get the correct title and the rating
        data = fetch_movie(title)
        if data is None:
            return False

        title = data.get("Title", title)
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
                imdb_url=get_imdb_url(title)
            )
            db.session.add(movie)
            db.session.commit()  # Commit so the movie gets an ID (movie.id)!

        # check if the user already has the movie in its list
        link = self.get_user_movie_link(movie.id, user_id)
        if not link:
            # create the link between User and Movie
            link = UserMovies(user_id=user_id, movie_id=movie.id,
                                  rating=rating)
            db.session.add(link)
            db.session.commit()
            return True
        else:
            return False

    def delete_movie(self, user_id, movie_id):
        """
        Removes a movie from a user's list.
        If there is no user left who links to it, remove the movie
        """
        # Delete the link between User and Movie
        link = self.get_user_movie_link(movie_id, user_id)
        if link:
            db.session.delete(link)
            db.session.commit()

        # delete the movie if nobody links to it
        remaining_links = UserMovies.query.filter_by(movie_id=movie_id).count()
        if remaining_links == 0:
            movie = Movie.query.get(movie_id)
            if movie:
                db.session.delete(movie)
                db.session.commit()

        return True

    def update_movie(self, movie_id, user_id, rating):
        """
        Updates the user based movie ranking
        """
        link = self.get_user_movie_link(movie_id, user_id)
        if not link:
            return False

        link.rating = rating
        db.session.commit()
        return True