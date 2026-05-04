import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="API Gateway")

MOVIE_SERVICE_URL = os.getenv(
    "MOVIE_SERVICE_URL",
    "http://localhost:8001"
)

MOVIE_SERVICE_TIMEOUT_SECONDS = 3.0


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway"
    }


@app.get("/movies/{movie_id}")
async def get_movie_page(movie_id: str):
    url = f"{MOVIE_SERVICE_URL}/movies/{movie_id}"

    try:
        async with httpx.AsyncClient(timeout=MOVIE_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.get(url)

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Movie not found"
            )

        response.raise_for_status()

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Movie Service did not respond in time"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Movie Service is unavailable"
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="Movie Service returned an error"
        )