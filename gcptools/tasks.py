import os 
import json
import unidecode
import datetime
import time 
import math
import traceback

from google.cloud import tasks_v2
from google.protobuf import duration_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from google.api_core.exceptions import AlreadyExists, FailedPrecondition

class GCP_TASKS() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools
		self.client = tasks_v2.CloudTasksClient()

		self.set_params()
	
	############################################################################
	#	Mise à jour des paramètres
	############################################################################
	def set_params(self, params={}):
		for p in ['PROJECT_NAME', 'LOCATION' ] :
			setattr( self, p.lower(), params.get(p) or os.environ.get(p) )
			if not getattr(self, p.lower(), None) : raise f"Pas de paramètre {p}"
	
		self.parent = f"projects/{self.project_name}/locations/{self.location}"

	############################################################################
	#	Ajoute une tâche à une liste
	############################################################################
	def send(self, queue_name, **params) :

		queue = self.client.queue_path(self.project_name, self.location, queue_name)

		self.gcp_tools.logger.debug(f"project={self.project_name}, location={self.location}, queue_name={queue_name}, queue={queue}")

		http_method = params.get('http_method') or "GET"
		http_method = tasks_v2.HttpMethod.POST if http_method=="POST" else tasks_v2.HttpMethod.GET

		if params.get('payload') :
			payload = json.dumps(params['payload'])
			payload = payload.encode()
		else : payload = None

		headers = params.get('headers') or {}

		relative_uri = params.get('relative_uri')
		simple_url = params.get('url')
		if not relative_uri and not simple_url : raise Exception(f"Task has no relative_uri and no simple_url")

		if simple_url :
			
			task = {	'http_request': {
								'http_method': http_method,
								'url': simple_url,
								'headers': headers
							}
						}
		
			if payload :
				task['http_request']['body'] = payload
				task['http_request']['headers'] = {'Content-type': 'application/json'}

			url_prefix = simple_url

		else :

			service = params.get('service')
			if service : raise Exception(f"Task has relative_uri but no service")

			task = {	'app_engine_http_request': {
								'http_method': http_method,
								'relative_uri': relative_uri,
								'app_engine_routing' : { "service" : service },
								'headers': headers
							}
						}

			if payload :
				task['app_engine_http_request']['body'] = payload
				task['app_engine_http_request']['headers'] = {'Content-type': 'application/json'}

			url_prefix = f"{service} / {relative_uri}"

		### DOC : https://googleapis.dev/python/cloudtasks/latest/tasks_v2beta3/types.html#google.cloud.tasks_v2beta3.types.Task.dispatch_deadline
		if params.get('timeout') :
			task['dispatch_deadline'] = duration_pb2.Duration().FromSeconds(60*int(params['timeout']))

		if params.get('name') :
			task_name = unidecode.unidecode( "projects/{}/locations/{}/queues/{}/tasks/{}".format(self.project,self.location,queue_name,params['name']) ).replace(' ','')
			task["name"] = task_name

		if params.get('time_delta') :
			task["name"] = task.get('name') or ''
			task["name"] += f"_{self.delta(params['time_delta'])}"
		
		log_prefix = f"Task [{http_method.name} - {queue_name}] {url_prefix}"
			
		if params.get('schedule_delta') :
			task['schedule_time'] = self.apply_time_delta(params['schedule_delta'])

		if params.get('avoid_duplicate') :

			self.already_existing_tasks = params.get('already_existing_tasks')

			if not self.already_existing_tasks :
				self.already_existing_tasks = self.get_already_existing_tasks(queue_name)

			for t in self.already_existing_tasks :

				if relative_uri and relative_uri == self.gcp_tools.rgetattr(t,'app_engine_http_request','relative_uri') :
					self.gcp_tools.logger.warn(f'{log_prefix} Relative URL already in list')
					return False
				if simple_url and simple_url == self.gcp_tools.rgetattr(t,'http_request','url') :
					self.gcp_tools.logger.warn(f'{log_prefix} URL already in list')
					return False

		retry = True

		while retry :

			try :
				self.gcp_tools.logger.debug(f"Created {log_prefix} - SHOOT ! (parent={queue}, task={task})")
				response = self.client.create_task( parent=queue, task=task )
				task_id = response.name.split('/')[-1]
				self.gcp_tools.logger.info(f"Created {log_prefix}, id={task_id}")
				return True

			##########
			### Gestion des erreurs classiques
			##########
			except AlreadyExists:
				self.gcp_tools.logger.error(f'{log_prefix} already exist')
				return False
			except FailedPrecondition :
				self.gcp_tools.logger.error(f"La file d'attente '{queue_name}' n'existe pas. {log_prefix} ")
				return False

			except Exception as e :
				if 'List group requests per minute per region' in str(e) :
					self.gcp_tools.logger.warn("List group requests per minute per region -- Wait 30s and retry")
					time.sleep(30)
				else :
					self.gcp_tools.logger.error(f"Problème sur cette tâche {log_prefix} : {str(e)}")
					raise e


	def apply_time_delta(self, my_delta) :
		#########
		###	Si un delta est indiqué on l'applique
		#########

		now = datetime.datetime.utcnow()

		if 'm' in my_delta :
			minutes = int(my_delta.split('m')[0])
			new_date = now + datetime.timedelta(minutes=minutes)
		elif 's' in my_delta :
			seconds = int(my_delta.split('s')[0])
			new_date = now + datetime.timedelta(seconds=seconds)
		elif 'h' in my_delta :
			hours = int(my_delta.split('s')[0])
			new_date = now + datetime.timedelta(hours=hours)

		timestamp = Timestamp()
		timestamp.FromDatetime(new_date)

		return timestamp


	##########################################################
	###	Fabrique un custom timestamp pour les tâches
	##########################################################
	def delta(self, my_delta) :
		#########
		###	Si un delta est indiqué on l'applique
		#########

		now = datetime.datetime.now()

		if 'm' in my_delta :
			minutes = int(my_delta.split('m')[0])
			return "{}{:02}{:02}{:02}{:02}".format(now.year,now.month,now.day,now.hour,int(math.ceil(float(int(now.strftime('%M')) + 1) / minutes)))
		if 'h' in my_delta :
			hours = int(my_delta.split('h')[0])
			return "{}{:02}{:02}{:02}".format(now.year,now.month,now.day,int(math.ceil(float(int(now.strftime('%H')) + 1) / hours)))


	########################################################
	# Récupère la liste des tâches d'une file d'attente
	########################################################
	def get_already_existing_tasks(self, queue_name) :

		try :
			self.gcp_tools.logger.debug(f"🗺 get_already_existing_tasks({queue_name})")
			waiting_queue_name = self.client.queue_path(self.project_name, self.location, queue_name)
			#self.gcp_tools.logger.debug(f"🗺 get_already_existing_tasks({queue_name}) - Queue récupérée : {waiting_queue_name}")
			tasks = self.client.list_tasks(parent=waiting_queue_name)
			#self.gcp_tools.logger.debug(f"🗺 get_already_existing_tasks({queue_name}) - Tâches récupérées.")
			return tasks
		except Exception as e: 
			self.gcp_tools.logger.error(f"🗺 get_already_existing_tasks({queue_name}) - {str(e)}")
			self.gcp_tools.logger(traceback.format_exc())
			raise e


