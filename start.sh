#!/bin/bash
# start.sh
# Run FastAPI with Gunicorn and Uvicorn workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT
