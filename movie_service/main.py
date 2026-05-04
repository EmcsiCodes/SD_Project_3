import os
import time

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Movie Service")

RECOMMENDATION_SERVICE_URL = os.getenv(
    "RECOMMENDATION_SERVICE_URL",
    "http://localhost:8002"
)

RECOMMENDATION_TIMEOUT_SECONDS = 1.5

CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT_SECONDS = 10

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


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_at = None

    def can_call_service(self):
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            elapsed_time = time.monotonic() - self.opened_at

            if elapsed_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True

            return False

        if self.state == "HALF_OPEN":
            return True

        return False

    def record_success(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self):
        if self.state == "HALF_OPEN":
            self.trip()
            return

        self.failure_count += 1

        if self.failure_count >= self.failure_threshold:
            self.trip()

    def trip(self):
        self.state = "OPEN"
        self.opened_at = time.monotonic()

    def get_status(self):
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout
        }


circuit_breaker = CircuitBreaker(
    failure_threshold=CIRCUIT_FAILURE_THRESHOLD,
    recovery_timeout=CIRCUIT_RECOVERY_TIMEOUT_SECONDS
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "movie-service"
    }


@app.get("/circuit-breaker")
def get_circuit_breaker_status():
    return circuit_breaker.get_status()


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
    if not circuit_breaker.can_call_service():
        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-circuit-open"
        }

    url = f"{RECOMMENDATION_SERVICE_URL}/recommendations/{movie_id}"

    try:
        async with httpx.AsyncClient(timeout=RECOMMENDATION_TIMEOUT_SECONDS) as client:
            response = await client.get(url)

        response.raise_for_status()
        data = response.json()

        circuit_breaker.record_success()

        return {
            "movie_ids": data["recommended_movie_ids"],
            "source": "recommendation-service"
        }

    except httpx.TimeoutException:
        circuit_breaker.record_failure()

        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-timeout"
        }

    except httpx.HTTPStatusError:
        circuit_breaker.record_failure()

        return {
            "movie_ids": TRENDING_MOVIE_IDS,
            "source": "fallback-trending-http-error"
        }

    except httpx.RequestError:
        circuit_breaker.record_failure()

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
        "recommendation_source": recommendation_result["source"],
        "circuit_breaker": circuit_breaker.get_status()
    }