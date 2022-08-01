import urllib.parse, urllib.request, traceback, os
from google.cloud import storage
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO

class GCP_Storage() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools


	##############################################################################
	#	Télécharge dans Google Storage un fichier via son URL
	#	ARGS :
	#		convert_webp : True / False - Conversion des images WEBP en PNG
	##############################################################################
	def upload_from_url (self, target_url, destination_blob_name, **args):

		try:

			answer = { 'src_url':target_url, 'url': None, 'record_status': None }

			STORAGE_NAME = os.environ['STORAGE_NAME']

			## On vérifie qu'on ne demande pas de stocker un truc déjà stocké
			if STORAGE_NAME in target_url :

				self.gcp_tools.logger.debug(f"gcp_download_from_url - target_url='{target_url}' / destination_blob_name='{destination_blob_name}' / Déjà téléchargé. On ne fait rien. ")
				answer['url'] = target_url
				answer['record_status'] = 'Done'

				return answer

			## On charche le module GCP Storage
			storage_client = storage.Client()
			bucket = storage_client.bucket(STORAGE_NAME)

			## On pré-charge le fichier

			file_type, file_extension, file_mime_type, media_width, media_height = self.detect_file_type(destination_blob_name, target_url )

			## Verrue pour cette histoire de WEBP
			if file_extension=="webp" and args.get('convert_webp') :
				file_bytes = self.to_png_bytes(target_url)
				file_type = 'picture'
				file_extension = 'png'
				file_mime_type = 'image/png'

			else :
				file_bytes = urllib.request.urlopen(target_url).read()


			blob = bucket.blob(destination_blob_name)
			blob.upload_from_string(file_bytes, file_mime_type)

			answer['url'] = blob.public_url
			answer['record_status'] = 'Done'
			if media_width : answer['width'] = media_width
			if media_height : answer['height'] = media_height

			self.gcp_tools.logger.debug(f"gcp_download_from_url - Correctement téléchargé : {answer}")

			return answer

		except Exception as e:

			self.gcp_tools.logger.warn(f"gcp_download_from_url - target_url='{target_url}' / destination_blob_name='{destination_blob_name}' / {e} ")
			print(traceback.format_exc())
			raise e



	##################################################################################
	#	Convertie le fichier webp en png
	##################################################################################
	def to_png_bytes(self, _img) :

		img = Image.open(BytesIO(_img))

		self.gcp_tools.logger.debug(f"Cette image ({image_url}) est en {img.format}, on la convertie à la volée en PNG.")

		img.convert("RGB")

		with BytesIO() as f:
			img.save(f, format='PNG')
			return f.getvalue()



	##################################################################################
	#	Détection du type de fichier par filename
	#	file_type, file_extension, file_mime_type = detect_file_type(filename)
	##################################################################################
	def detect_file_type(self, file_name, file_url) :

		extension = file_name.lower().split('.')[-1]

		if any(ext in extension for ext in ['jpg','jpeg','gif','png','webp']):

			file_type = 'picture'

			web_file = urllib.request.urlopen(file_url)
			picture = Image.open(BytesIO(web_file.read()))
			picture_format = picture.format.lower()
			picture_mimetype = picture.get_format_mimetype()
			picture_width = int(picture.width)
			picture_height = int(picture.height)

			return file_type, picture_format, picture_mimetype, picture_width, picture_height

		elif any(ext in extension for ext in ['mp4']):

			return 'video', 'mp4', 'video/mp4', None, None

		else :

			self.gcp_tools.logger.warn(f"detect_file_type - Extension unknown : {extension} / filename : {filename}")
			return 'unknown', extension, 'unknown/unknown'