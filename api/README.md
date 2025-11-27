# Chile House Pricing API

FastAPI-based REST API for serving house price predictions.

## Setup

Install dependencies:
```bash
pip install fastapi uvicorn pydantic
```

## Running the API

Development mode with auto-reload:
```bash
uvicorn api.app.main:app --reload --port 8000
```

Or from the api directory:
```bash
cd api
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Endpoints

- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `POST /api/v1/predict` - Predict house price (coming soon)

## Testing

```bash
pytest api/tests/
```
