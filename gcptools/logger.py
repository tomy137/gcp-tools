
##############################################
# Gestion des logs
##############################################

import os, logging, traceback

import google.cloud.logging
client = google.cloud.logging.Client()
client.get_default_handler()
client.setup_logging()


class GCP_Logger() :

	def __init__(self, gcp_tools):


		self.logger = logging.getLogger(gcp_tools.label)
		self.logger.setLevel(logging.DEBUG)

		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)

		if gcp_tools.is_locally_run() :
			ch.setFormatter(Offline_CustomFormatter())
		else :
			ch.setFormatter(Online_CustomFormatter())

		self.logger.addHandler(ch)

	def info(self, msg, **args):
		self.logger.info(msg)
	def debug(self, msg, **args):
		self.logger.debug(msg)
	def warn(self, msg, **args):
		self.logger.warn(msg)
	def error(self, msg, **args):
		self.logger.error(msg)

######
#	Colorisation et mise en forme : OFFLINE
######
class Offline_CustomFormatter(logging.Formatter):

	grey = "\x1b[90m"
	white = "\x1b[38;20m"
	yellow = "\x1b[33;20m"
	red = "\x1b[31;20m"
	bold_red = "\x1b[31;1m"
	reset = "\x1b[0m"

	format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

	FORMATS = {
		logging.DEBUG: grey + format + reset,
		logging.INFO: white + format + reset,
		logging.WARNING: yellow + format + reset,
		logging.ERROR: red + format + reset,
		logging.CRITICAL: bold_red + format + reset
	}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)

######
#	Colorisation et mise en forme : ONLINE
######
class Online_CustomFormatter(logging.Formatter):

	format = "%(message)s"

	FORMATS = {
		logging.DEBUG:format,
		logging.INFO:format,
		logging.WARNING:format,
		logging.ERROR:format,
		logging.CRITICAL:format
	}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)