# Setup for backend

### Setting up the backend (Dockerised)

1. Ensure you have `docker` installed.
2. Run `docker build -t backend .`
3. After Docker has been built, run `docker compose up` to get the backend running.

### Testing

1. Make sure you have `pytest` and `pytest-cov` with pip (or pip3).
2. Run `pytest --cov=. --cov-report=html` inside the `/backend`
3. Inside the `/htmlcov` folder inside `/backend`, click on `index.html`.
