import os
import logging
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

REDIS_URL = 'localhost:6379'
REDIS_CHAN = 'chat'

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)

class ChatBackend(object):
	def __init__(self):
		self.clients = []
		self.pubsub = redis.pubsub()
		self.pubsub.subscribe(REDIS_CHAN)

	def __iter_data(self):
		for message in self.pubsub.listen():
			data = message.get('data')
			if message['type'] == 'message':
				app.logger.info('Sending Message')
				yield data
	
	def register(self, client):
		self.clients.append(client)

	def send(self, client, data):
		try:
			client.send(data)
		except Exception:
			self.clients.remove(client)

	def run(self):
		for data in self.__iter_data():
			for client in self.clients:
				gevent.spawn(self.send, client, data)

	def start(self):
		gevent.spawn(self.run)

chats = ChatBackend()
chats.start()

@app.route('/')
def hello():
	return render_template('index.html')

@sockets.route('/submit')
def inbox(ws):
	while not ws.closed:
		try:
			message = ws.receive()

			if message:
				app.logger.info('Inserting message')
				redis.publish(REDIS_CHAN, message)
		except WebSocketError:
			return ''
		#  Sleep to prevent 'constant' context-switches
		gevent.sleep(0.1)
@sockets.route('/receive')
def outbox(ws):
	chats.register(ws)

	while not ws.closed:
		# Context switch while `ChatBackend.start` is running in the background.
		gevent.sleep()