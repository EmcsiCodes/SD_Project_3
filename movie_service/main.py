import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Movie Service")

RECOMMENDATION_SERVICE_URL = os.getenv(
    "RECOMMENDATION_SERVICE_URL",
    "http://localhost:8002"
)

RECOMMENDATION_TIMEOUT_SECONDS = 1.5

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

TRENDING_MOVIE_IDS = ["1", "2", "3"]


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "movie-service"
    }


def build_movie_list(movie_ids):
    movies = []

    for movie_id in movie_ids:
        movie = MOVIES.get(movie_id)

        if movie is not None:
            movies.append({
                "id": movie_id,
                "title": movie["title"],
                "description": movie["description"]
            })

    return movies


async def fetch_recommendations(movie_id: str):
    url = f"{RECOMMENDATION_SERVICE_URL}/recommendations/{movie_id}"

    try:
        async with httpx.AsyncClient(timeout=RECOMMENDATION_TIMEOUT_SECONDS) as client:
            response = await client.get(url)

        response.raise_for_status()
        data = response.json()

        return {
            "movie_ids": data["recommended_movie_ids"],
            "source": "recommendation-service"
        }

    except httpx.TimeoutException:
        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-timeout"
        }

    except httpx.HTTPStatusError:
        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-http-error"
        }

    except httpx.RequestError:
        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-service-unavailable"
        }


@app.get("/movies/{movie_id}")
async def get_movie_page(movie_id: str):
    movie = MOVIES.get(movie_id)

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    recommendation_result = await fetch_recommendations(movie_id)

    similar_movies = build_movie_list(recommendation_result["movie_ids"])

    return {
        "movie": {
            "id": movie_id,
            "title": movie["title"],
            "description": movie["description"]
        },
        "similar_movies": similar_movies,
        "recommendation_source": recommendation_result["source"]
    }