import os
import requests
from dotenv import load_dotenv

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

OMDB_MOVIE_URL = f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&t="


def fetch_movie(movie_name):
    """
    fetches a movie via OMDB API and returns it as a dictionary
    if exists else None
    """
    try:
        res = requests.get(OMDB_MOVIE_URL + movie_name)
        if res.status_code == 200:
            data = res.json()
            if data.get("Response") == 'True':
                return data
        else:
            return None
    except Exception as e:
        print(e)
        return None


def get_imdb_url(movie_name):
    """
    returns the deeplink to the movie from https://www.imdb.com/
    if exists else "N/A"
    """
    movie = fetch_movie(movie_name)
    if movie is not None:
        return f"https://www.imdb.com/title/{movie['imdbID']}"
    return "N/A"


def main():
    movie_name = input('\nEnter movie name: ')
    movie = fetch_movie(movie_name)
    if movie is not None:
        for key, value in movie.items():
            print(f"{key}: {value}")
        print(get_imdb_url(movie_name))
    else:
        print('\nMovie not found!')


if __name__ == "__main__":
    main()