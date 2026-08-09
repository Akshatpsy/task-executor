# Distributed Task Executor

A distributed task execution engine built with Python, PostgreSQL, RabbitMQ, and FastAPI.

## Deployment / Live Demo

For a portfolio deployment, we recommend deploying the API to a service like [Railway](https://railway.app/).

1. Push your project to a GitHub repository.
2. Go to Railway, click "New Project" -> "Deploy from GitHub repo" and select your repository.
3. Configure the following environment variables in the Railway dashboard:
   - `DATABASE_URL`
   - `RABBITMQ_URL`
4. Set the start command to run the API: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`

*Note: The scheduler and worker are designed to run as separate background processes. In a free-tier portfolio deployment, you can deploy just the API as the live, interactive component while demonstrating the scheduler and worker functionality via recorded testing evidence. As a result, tasks submitted via the live demo will intentionally remain in the 'pending' or 'queued' state.*
