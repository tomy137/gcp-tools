import os

from sqlalchemy import create_engine
from sqlalchemy.sql import text


class GCP_SQL() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools
		self.init_bdd()

	def execute(self, SQL, keep=False) :
		with self.engine.connect() as con:
			k = con.execute(text(SQL))
		if not keep : self.engine.dispose()
		return k

	def init_bdd(self) :

		db_user = os.environ.get("DB_USER")
		db_pass = os.environ.get("DB_PASS")
		db_name = os.environ.get("DB_NAME")

		if self.gcp_tools.is_locally_run() :
			self.gcp_tools.logger.debug("🚲 Démarrage de l'app en local 🚲 -- Attention a bien avoir démarré le proxy !")
			SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}?charset=utf8mb4"

		else :
			self.gcp_tools.logger.debug("🛰 Démarrage de l'app sur l'environnement Google 🛰")
			SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket=/cloudsql/reactiometre:europe-west1:tmf-reactiometre-bdd&charset=utf8mb4"

		self.engine = create_engine(SQLALCHEMY_DATABASE_URI)



	def to_list_of_dict(self, sql_execution) :

		return [ o._asdict() for o in sql_execution ]

	def just_one_value(self, sql_execution) :

		v = sql_execution.one_or_none()
		return v[0] if v else None


	def insert_or_update(self, table=None, **args) :

		values_labels = [ f'{k}' for k in args if args[k] ]
		# DOCS : https://stackoverflow.com/a/41970663/2373259
		values_values = [ args[k] for k in args if args[k] ]
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
