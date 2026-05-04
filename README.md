# Software Design Assignment 3 - Microservices

This project implements a simple microservice-based movie system using Python and FastAPI.


At this stage, the system contains two services:

1. Recommendation Service
2. Movie Service

The Movie Service calls the Recommendation Service to get similar movie recommendations.

---

## Project Structure

```text
sd-assignment-3/
  recommendation_service/
    main.py

  movie_service/
    main.py

  requirements.txt
  README.md
  .gitignore
```

---

## Services

## Recommendation Service

The Recommendation Service returns recommended movie IDs for a given movie.

Base URL:

```text
http://localhost:8002
```

Endpoints:

```text
GET /health
GET /recommendations/{movie_id}
```

Example request:

```bash
curl http://localhost:8002/recommendations/1
```

Example response:

```json
{
  "movie_id": "1",
  "recommended_movie_ids": ["2", "3", "4"]
}
```

---

## Movie Service

The Movie Service returns movie information together with similar movies.

Base URL:

```text
http://localhost:8001
```

Endpoints:

```text
GET /health
GET /movies/{movie_id}
```

Example request:

```bash
curl http://localhost:8001/movies/1
```

Example response:

```json
{
  "movie": {
    "id": "1",
    "title": "Inception",
    "description": "A skilled thief enters people's dreams to steal secrets."
  },
  "similar_movies": [
    {
      "id": "2",
      "title": "The Matrix",
      "description": "A hacker discovers that reality is a simulated world."
    },
    {
      "id": "3",
      "title": "Interstellar",
      "description": "A group of astronauts travel through a wormhole to save humanity."
    },
    {
      "id": "4",
      "title": "The Dark Knight",
      "description": "Batman faces the Joker, a criminal mastermind spreading chaos."
    }
  ]
}
```

---

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Project

You need two terminals.

### Terminal 1 - Run Recommendation Service

```bash
uvicorn recommendation_service.main:app --reload --port 8002
```

### Terminal 2 - Run Movie Service

```bash
uvicorn movie_service.main:app --reload --port 8001
```

---

## Testing

Test the Recommendation Service:

```bash
curl http://localhost:8002/health
```

```bash
curl http://localhost:8002/recommendations/1
```

Test the Movie Service:

```bash
curl http://localhost:8001/health
```

```bash
curl http://localhost:8001/movies/1
```

---

## Environment Variables

The Movie Service uses this environment variable to know where the Recommendation Service is running:

```text
RECOMMENDATION_SERVICE_URL
```

Default value:

```text
http://localhost:8002
```

PowerShell example:

```powershell
$env:RECOMMENDATION_SERVICE_URL="http://localhost:8002"
```

---

## Current Request Flow

```text
User
  |
  v
Movie Service
  |
  v
Recommendation Service
```

For example, when this request is made:

```text
GET /movies/1
```

The Movie Service:

1. Finds movie `1`
2. Calls the Recommendation Service
3. Gets recommended movie IDs
4. Converts those IDs into movie objects
5. Returns the movie page response

---

## Current Phase Status

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Basic Recommendation Service | Done |
| Phase 2 | Movie Service calls Recommendation Service | Done |

---

## Git Commit

Recommended commit for this phase:

```bash
git add .
git commit -m "Phase 2: add movie service dependency"
```