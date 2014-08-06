Right now just the heroku websocket tutorial with minor modications to get it running locally and with updated libraries.

gunicorn -b localhost:5000 -k flask_sockets.worker app:app

redis-server