import os
import random
import time

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Recommendation Service")

RECOMMENDATIONS = {
    "1": ["2", "3", "4"],
    "2": ["1", "3", "5"],
    "3": ["1", "4", "5"],
    "4": ["1", "2", "5"],
    "5": ["2", "3", "4"],
}


def is_chaos_mode_enabled():
    return os.getenv("CHAOS_MODE", "false").lower() == "true"


def apply_chaos_mode():
    if not is_chaos_mode_enabled():
        return

    random_value = random.random()

    if random_value < 0.33:
        raise HTTPException(
            status_code=503,
            detail="Recommendation Service chaos mode: simulated HTTP 503 failure"
        )

    if random_value < 0.66:
        delay = random.randint(3, 10)
        time.sleep(delay)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "recommendation-service",
        "chaos_mode": is_chaos_mode_enabled()
    }


@app.get("/recommendations/{movie_id}")
def get_recommendations(movie_id: str):
    apply_chaos_mode()

    recommended_ids = RECOMMENDATIONS.get(movie_id, ["1", "2", "3"])

    return {
        "movie_id": movie_id,
        "recommended_movie_ids": recommended_ids,
        "chaos_mode": is_chaos_mode_enabled()
    }