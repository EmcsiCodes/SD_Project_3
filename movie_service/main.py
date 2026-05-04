import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Movie Service")

RECOMMENDATION_SERVICE_URL = os.getenv(
    "RECOMMENDATION_SERVICE_URL",
    "http://localhost:8002"
)

MOVIES = {
    "1": {
        "title": "Inception",
        "description": "A skilled thief enters people's dreams to steal secrets."
    },
    "2": {
        "title": "The Matrix",
        "description": "A hacker discovers that reality is a simulated world."
    },
    "3": {
        "title": "Interstellar",
        "description": "A group of astronauts travel through a wormhole to save humanity."
    },
    "4": {
        "title": "The Dark Knight",
        "description": "Batman faces the Joker, a criminal mastermind spreading chaos."
    },
    "5": {
        "title": "Arrival",
        "description": "A linguist works to communicate with mysterious alien visitors."
    }
}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "movie-service"
    }


async def fetch_recommendations(movie_id: str):
    url = f"{RECOMMENDATION_SERVICE_URL}/recommendations/{movie_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    response.raise_for_status()
    data = response.json()

    return data["recommended_movie_ids"]


@app.get("/movies/{movie_id}")
async def get_movie_page(movie_id: str):
    movie = MOVIES.get(movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    recommended_movie_ids = await fetch_recommendations(movie_id)

    recommended_movies = []

    for recommended_id in recommended_movie_ids:
        recommended_movie = MOVIES.get(recommended_id)

        if recommended_movie is not None:
            recommended_movies.append({
                "id": recommended_id,
                "title": recommended_movie["title"],
                "description": recommended_movie["description"]
            })

    return {
        "movie": {
            "id": movie_id,
            "title": movie["title"],
            "description": movie["description"]
        },
        "similar_movies": recommended_movies
    }