import os

from .logger import GCP_Logger
from .sql import GCP_SQL
from .sql2 import GCP_SQL2
from .storage import GCP_Storage
from .snippet import encode_b64_json, decode_b64_json, date_to_datetime, datetime_now
from .compute import GCP_Compute
from .tasks import GCP_TASKS
from .chat import send

class GCP_Tools(object):

	def __init__(self, **args):

		self.label = os.environ.get('DB_USER') or "DEFAULT"
		self.logger = GCP_Logger(self)
		self.sql = GCP_SQL(self)
		self.sql2 = GCP_SQL2(self)
		self.storage = GCP_Storage(self)
		self.compute = GCP_Compute(self)
		self.tasks = GCP_TASKS(self)

		self.logger.debug(f"Correctement initialisé.")

		self.encode_b64_json = encode_b64_json
		self.decode_b64_json = decode_b64_json
		self.date_to_datetime = date_to_datetime
		self.datetime_now = datetime_now

		self.send_chat = send

	##
	#	Vérifie si l'app est lancée en local ou sur un GCP
	##
	def is_locally_run(self) :
		return not(os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GAE_RUNTIME') or os.environ.get('FORCE_CLOUD'))