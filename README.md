# Software Design Assignment 3 - Microservices

This project implements a simplified distributed movie recommendation system using **Python** and **FastAPI**.

The goal of the project is to show how a distributed system can continue working during partial failures or high latency.

The system contains three services:

1. **API Gateway**
2. **Movie Service**
3. **Recommendation Service**

The user sends requests to the API Gateway. The API Gateway forwards movie page requests to the Movie Service. The Movie Service returns movie information and calls the Recommendation Service to get similar movie recommendations.

---

## System Overview

The normal request flow is:

```text
User -> API Gateway -> Movie Service -> Recommendation Service
```

For example, when the user requests:

```text
GET /movies/1
```

the flow is:

1. The API Gateway receives the request.
2. The API Gateway forwards the request to the Movie Service.
3. The Movie Service finds the movie title and description.
4. The Movie Service calls the Recommendation Service for similar movie IDs.
5. The Movie Service builds a complete movie page response.
6. The API Gateway returns the response to the user.

---

## Services

### API Gateway

The API Gateway is the public entry point of the system.

It is responsible for routing requests to the Movie Service and returning clear error responses if the Movie Service is unavailable, too slow, or returns an error.

Main endpoint:

```text
GET /movies/{movie_id}
```

The API Gateway calls the Movie Service internally.

---

### Movie Service

The Movie Service is Service A from the assignment.

It stores basic movie data such as titles and descriptions.

It is responsible for returning a complete movie page. To do that, it calls the Recommendation Service and asks for similar movie IDs.

The Movie Service also contains the main resiliency logic:

- strict timeout
- fallback trending movies
- circuit breaker

If the Recommendation Service is healthy, the Movie Service uses real recommendation data.

If the Recommendation Service is failing or too slow, the Movie Service still returns a valid movie page using fallback trending movies.

---

### Recommendation Service

The Recommendation Service is Service B from the assignment.

It returns a list of recommended movie IDs for a given movie.

Main endpoint:

```text
GET /recommendations/{movie_id}
```

It also supports chaos mode through an environment variable:

```text
CHAOS_MODE=true
```

When chaos mode is enabled, the Recommendation Service randomly simulates failures by:

- returning HTTP 503 errors
- waiting between 3 and 10 seconds before responding

This allows the Movie Service timeout, fallback, and circuit breaker behavior to be tested.

---

## Resiliency Behavior

### Strict Timeout

The Movie Service waits only **1.5 seconds** for the Recommendation Service.

If the Recommendation Service takes longer than that, the request is cut off and the Movie Service uses fallback data.

This prevents the whole system from becoming slow just because one service is slow.

---

### Graceful Degradation

If the Recommendation Service is unavailable, broken, or too slow, the Movie Service does not return a broken response.

Instead, it returns a hardcoded list of trending movies.

So instead of failing completely, the system still gives the user a usable movie page.

Example fallback source:

```json
{
  "recommendation_source": "fallback-trending-timeout"
}
```

or:

```json
{
  "recommendation_source": "fallback-trending-service-unavailable"
}
```

---

### Circuit Breaker

The Movie Service has a circuit breaker around calls to the Recommendation Service.

The circuit breaker starts in the `CLOSED` state.

If the Recommendation Service fails several times, the circuit changes to `OPEN`.

When the circuit is open, the Movie Service does not call the Recommendation Service anymore. It immediately uses fallback trending movies.

After a recovery timeout, the circuit moves to `HALF_OPEN` and allows one test request.

If the Recommendation Service works again, the circuit returns to `CLOSED`.

The states are:

```text
CLOSED
OPEN
HALF_OPEN
```

This prevents repeated calls to a failing service and helps the system recover cleanly.

---

## Requirement Mapping

| Assignment Requirement | Implementation |
|---|---|
| API Gateway routes requests and handles failures | Implemented in `api_gateway/main.py` |
| Movie Service fetches titles and descriptions | Implemented in `movie_service/main.py` |
| Movie Service depends on Recommendation Service | Movie Service calls Recommendation Service over HTTP |
| Recommendation Service returns recommended movie IDs | Implemented in `recommendation_service/main.py` |
| User requests a movie page | `GET /movies/{movie_id}` |
| Service B chaos mode through environment variable | `CHAOS_MODE=true` |
| Random HTTP 503 failures | Implemented in Recommendation Service chaos mode |
| Network jitter between 3 and 10 seconds | Implemented in Recommendation Service chaos mode |
| Strict 1.5-second timeout | Implemented in Movie Service |
| Fallback trending movies | Implemented in Movie Service |
| Circuit breaker | Implemented in Movie Service |
| Circuit recovery | Circuit moves from `OPEN` to `HALF_OPEN`, then back to `CLOSED` after success |

---

## How the Codebase Works

The project is separated into three FastAPI applications.

The `api_gateway` service receives the external request. It does not store movie data itself. Its job is to forward the request to the Movie Service and handle Movie Service errors.

The `movie_service` contains the movie data and the resiliency logic. It calls the Recommendation Service with a 1.5-second timeout. If that call succeeds, the response contains recommendations from the Recommendation Service. If the call fails, times out, or the circuit breaker is open, it returns fallback trending movies.

The `recommendation_service` contains recommendation data. In normal mode, it returns recommended movie IDs immediately. In chaos mode, it randomly fails or becomes slow so the resiliency behavior of the Movie Service can be tested.

The most important part of the system is that the Movie Service does not fully depend on the Recommendation Service being healthy. Even if the Recommendation Service fails, the user can still receive a valid movie page.

---

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the services in three separate terminals:

```bash
uvicorn recommendation_service.main:app --reload --port 8002
```

```bash
uvicorn movie_service.main:app --reload --port 8001
```

```bash
uvicorn api_gateway.main:app --reload --port 8000
```

Then open:

```text
http://localhost:8000/movies/1
```

---

## Running with Chaos Mode

To start the Recommendation Service with chaos mode enabled in PowerShell:

```powershell
$env:CHAOS_MODE="true"
uvicorn recommendation_service.main:app --reload --port 8002
```

Then run the Movie Service and API Gateway normally.

Refresh this page several times:

```text
http://localhost:8000/movies/1
```

Some requests will use real recommendations. Other requests may use fallback trending movies because the Recommendation Service returned an error or responded too slowly.

---

## Useful Test URLs

API Gateway:

```text
http://localhost:8000/health
http://localhost:8000/movies/1
```

Movie Service:

```text
http://localhost:8001/health
http://localhost:8001/movies/1
http://localhost:8001/circuit-breaker
```

Recommendation Service:

```text
http://localhost:8002/health
http://localhost:8002/recommendations/1
```

---

## Example Successful Response

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
  ],
  "recommendation_source": "recommendation-service",
  "circuit_breaker": {
    "state": "CLOSED",
    "failure_count": 0,
    "failure_threshold": 3,
    "recovery_timeout_seconds": 10
  }
}
```

---

## Example Fallback Response

```json
{
  "movie": {
    "id": "1",
    "title": "Inception",
    "description": "A skilled thief enters people's dreams to steal secrets."
  },
  "similar_movies": [
    {
      "id": "1",
      "title": "Inception",
      "description": "A skilled thief enters people's dreams to steal secrets."
    },
    {
      "id": "2",
      "title": "The Matrix",
      "description": "A hacker discovers that reality is a simulated world."
    },
    {
      "id": "3",
      "title": "Interstellar",
      "description": "A group of astronauts travel through a wormhole to save humanity."
    }
  ],
  "recommendation_source": "fallback-trending-service-unavailable",
  "circuit_breaker": {
    "state": "OPEN",
    "failure_count": 3,
    "failure_threshold": 3,
    "recovery_timeout_seconds": 10
  }
}
```
---