from models import db, User, Movie


class DataManager():
    """
    Handels database operations
    """
    def get_users(self):
        return User.query.all()

    def get_movies(self, user_id):
        return Movie.query.filter_by(user_id=user_id).all()

    def add_movie(self, movie):
        db.session.add(movie)
        db.session.commit()

    def delete_movie(self, movie_id):
        pass

    def update_movie(self, movie_id):
        pass