import os

from sqlalchemy import create_engine
from sqlalchemy.sql import text


class GCP_SQL() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools
		self.init_bdd()
		self.keep = False

	def execute(self, SQL, keep=None) :
		
		with self.engine.connect() as con:
			k = con.execute(text(SQL).execution_options(autocommit=True))
			self.gcp_tools.logger.debug(f"📃 SQL : {SQL}")
		
		if keep == None : keep = self.keep
		if not keep : self.engine.dispose()
		return k

	def close(self) :
		self.engine.dispose()

	def init_bdd(self) :

		DB_USER = os.environ.get("DB_USER")
		DB_PASS = os.environ.get("DB_PASS")
		DB_NAME = os.environ.get("DB_NAME")
		DB_HOST = os.environ.get("DB_HOST") or 'localhost'
		PROJECT_NAME = os.environ.get("PROJECT_NAME") or 'reactiometre'
		SQL_INSTANCE_NAME = os.environ.get("SQL_INSTANCE_NAME") or 'tmf-reactiometre-bdd'

		if None in [DB_USER, DB_PASS, DB_NAME, PROJECT_NAME, SQL_INSTANCE_NAME] :
			self.gcp_tools.logger.warn("L'une des variables d'environnement suivante n'est pas initialisée, on ne charge pas le module SQL. Liste : DB_USER, DB_PASS, DB_NAME, PROJECT_NAME, SQL_INSTANCE_NAME")
			return None

		if self.gcp_tools.is_locally_run() :
			self.gcp_tools.logger.debug("🚲 Démarrage de l'app SQL en local 🚲 -- Attention a bien avoir démarré le proxy !")
			SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"	

		else :
			self.gcp_tools.logger.debug("🛰 Démarrage de l'app SQL sur l'environnement Google 🛰")
			SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@/{DB_NAME}?unix_socket=/cloudsql/{PROJECT_NAME}:europe-west1:{SQL_INSTANCE_NAME}&charset=utf8mb4"

		self.engine = create_engine(SQLALCHEMY_DATABASE_URI)


	def to_one_dict(self, sql_execution, clean=False) :
		if not sql_execution : return None
		j = sql_execution._asdict()
		return { k:j[k] for k in j if (j[k]==0 or j[k]) } if clean else j

	def to_list_of_dict(self, sql_execution, clean=False) :

		if not sql_execution : return None

		t = [ o._asdict() for o in sql_execution ]
		if not clean : return t

		t_ = []
		for j in t : t_.append( { k:j[k] for k in j if (j[k]==0 or j[k]) } )
		return t_

	def just_one_value(self, sql_execution) :
		v = sql_execution.one_or_none()
		return v[0] if v else None


	def insert_or_update(self, table=None, **args) :

		values_labels = [ f'{k}' for k in args if (args[k]==0 or args[k]) ]
		# DOCS : https://stackoverflow.com/a/41970663/2373259
		values_values = [ args[k] for k in args if (args[k]==0 or args[k]) ]
		values_values = [ "\"{}\"".format(k.replace('"',r'\"')) if ( not 'float' in str(type(k)) and not 'int' in str(type(k)) and not k.isnumeric() ) else "\"{}\"".format(k) for k in values_values ] #💩

		values_labels = ', '.join( values_labels )
		values_values = ', '.join( values_values )

		update_assignements = ', '.join( f"{k} = VALUES({k})" for k in args )

		_SQL = f"INSERT INTO {table} ({values_labels}) VALUES ({values_values})\
				ON DUPLICATE KEY UPDATE {update_assignements}"

		self.gcp_tools.logger.debug(f"insert_or_update - SQL = {_SQL}")

		self.execute(_SQL)

		# "

		# INSERT INTO gcd_data (gcd_id, post_title, post_content, post_date_gmt,
		#                       post_modified_gmt, post_url, post_type)
		#     VALUES (1024, 'Hello World', 'How Are You?', '', '', 'www.google.com', 'product')
		#     ON DUPLICATE KEY UPDATE
		#         post_title = VALUES(post_title),
		#         post_content = VALUES(post_content,
		#         post_date_gmt = VALUES(post_date_gmt),
		#         post_modified_gmt = VALUES(post_modified_gmt),
		#         post_url = VALUES(post_url),
		#         post_type = VALUES(post_type);
