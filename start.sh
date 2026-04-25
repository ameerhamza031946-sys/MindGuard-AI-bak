#!/bin/bash
# start.sh
export PYTHONPATH=$PYTHONPATH:.
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --timeout 120
