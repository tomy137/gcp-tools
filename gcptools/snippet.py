import base64, json, pytz, datetime

from tzlocal import get_localzone
from dateutil.parser import parse, parserinfo

################################################################################
###			Encode et décode des JSON compressés en base64
################################################################################

def encode_b64_json(params):
	return base64.urlsafe_b64encode(json.dumps(params).encode()).decode()

def decode_b64_json(b64_params):
	return json.loads(base64.urlsafe_b64decode(b64_params.encode()).decode()) if b64_params else None

################################################################################
###		Renvoi un datetime depuis un string
################################################################################
def date_to_datetime(date,us=False):

	fr_timezone = pytz.timezone("Europe/Paris")

	## On test avec les patterns classiques
	try :
		return parse(str(date)).astimezone(fr_timezone) if us else parse(str(date))

	except Exception as e:
		pass

	## C'est peut-être un timestamp :
	try :
		int_date = int(str(date)[:10])
		return datetime.datetime.fromtimestamp(int_date).astimezone(fr_timezone) if us else datetime.datetime.fromtimestamp(int_date)
	except Exception as e:
		pass

	## On ne sait pas faire...
	raise Exception("Sorry, impossible de convertir cette date : {}".format(date))

## Retourne un datetime en accord avec le créneau horaire
def datetime_now():
	fr_timezone = pytz.timezone("Europe/Paris")
	return datetime.datetime.now().replace(tzinfo=None,microsecond=0) if get_localzone().zone == "Europe/Paris" else datetime.datetime.utcnow().astimezone(fr_timezone).replace(tzinfo=None,microsecond=0)
