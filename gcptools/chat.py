
import requests

def send(webhook_url, message) :

	requests.post(webhook_url, json={'text':message})