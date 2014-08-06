gunicorn -b localhost:5000 -k flask_sockets.worker app:app

redis-server