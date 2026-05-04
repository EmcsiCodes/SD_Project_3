from fastapi import FastAPI

app = FastAPI(title="Recommendation Service")

RECOMMENDATIONS = {
    "1": ["2", "3", "4"],
    "2": ["1", "3", "5"],
    "3": ["1", "4", "5"],
    "4": ["1", "2", "5"],
    "5": ["2", "3", "4"],
}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "recommendation-service"
    }


@app.get("/recommendations/{movie_id}")
def get_recommendations(movie_id: str):
    recommended_ids = RECOMMENDATIONS.get(movie_id, ["1", "2", "3"])

    return {
        "movie_id": movie_id,
        "recommended_movie_ids": recommended_ids
    }