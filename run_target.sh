#!/usr/bin/bash

source venv/bin/activate

gunicorn --error-logfile ./error.log --access-logfile ./access.log --capture-output -w 1 --threads 100  -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b '127.0.0.1:5000' 'app:app'

