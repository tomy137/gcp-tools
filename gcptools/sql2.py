import os
import mysql.connector

class GCP_SQL2() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools
		self.init_bdd()
		self.cursor = None
	
	def execute(self, SQL, commit=False) :

		if not self.mydb or not self.cursor : self.init_bdd()
		
		self.gcp_tools.logger.debug(f"📃 SQL2 : {SQL}")
		self.cursor.execute(SQL)
		if commit : self.mydb.commit()
		return self.cursor

	def init_bdd(self) :
		
		## Récupération des paramètres 
		DB_USER = os.environ.get("DB_USER")
		DB_PASS = os.environ.get("DB_PASS")
		DB_NAME = os.environ.get("DB_NAME")
		DB_HOST = os.environ.get("DB_HOST") or 'localhost'
		PROJECT_NAME = os.environ.get("PROJECT_NAME") 
		SQL_INSTANCE_NAME = os.environ.get("SQL_INSTANCE_NAME")
	
		params = {  'host' : DB_HOST or 'localhost',
					'user' : DB_USER,
					'password' : DB_PASS,
					'database' : DB_NAME,
					'charset' : 'utf8mb4'
		}

		if not self.gcp_tools.is_locally_run() :
			params['unix_socket'] = f"/cloudsql/{PROJECT_NAME}:europe-west1:{SQL_INSTANCE_NAME}"
		
		self.mydb = mysql.connector.connect(**params)
		
		self.cursor = self.mydb.cursor(buffered=True)
		if self.mydb : self.gcp_tools.logger.debug("SQL2 - Connexion effectuée avec succès")

	def to_one_dict(self, cursor) :
		return dict(zip(cursor.column_names, cursor.fetchone()))
			
	def to_list_of_dict(self, cursor) :
		return [ dict(zip(cursor.column_names, row)) for row in cursor.fetchall() ]
			
	def close(self) :
		self.mydb.close()
		self.cursor = None
		self.gcp_tools.logger.debug("SQL2 - Déconnecté")