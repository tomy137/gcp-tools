from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import time, os
###################################################################################
#
#	Management des applications GCP
#
###################################################################################
class GCP_Services_Manager() :

	def __init__(self):

		self.PROJECT_NAME = os.environ.get('PROJECT_NAME') or "reactiometre"

		self.appsId=self.PROJECT_NAME
		credentials = GoogleCredentials.get_application_default()
		appengine = discovery.build('appengine', 'v1', credentials=credentials, cache_discovery=False)
		self.apps = appengine.apps()

	##############################################################################
	#	Tous les get classiques
	##############################################################################
	def get_service(self, service_name) :
		return self.apps.services().get(appsId=self.appsId,servicesId=service_name).execute()

	# NE FONCTIONNE PAS DANS UNE APP
	# def get_services(self) :
	# 	return self.apps.services().list(appsId=self.apps).execute()['services']

	def get_service_versions(self, service_name) :
		return self.apps.services().versions().list(appsId=self.appsId,servicesId=service_name).execute()['versions']


	def get_serving_versions(self, service_name) :
		return [ v for v in self.get_service_versions(service_name) if v['servingStatus']=="SERVING" ]


	def get_serving_version(self, service_name) :

		service = self.get_service(service_name)
		serving_allocations = service['split']['allocations']
		serving_services_ids = []

		for version_id in serving_allocations :
			if serving_allocations['version_id'] > 0 :
				serving_services_ids.append(version_id)


		serving_versions = [ v for v in self.get_service_versions(service_name) if v['servingStatus']=="SERVING" ]
		if not len(serving_versions) == 1 : raise Exception(f"Service {service_name} - Plusieurs versions sont en train de servir !")
		return serving_versions[0]

	def get_not_serving_version(self, service_name) :
		not_serving_versions = self.get_not_serving_versions(service_name)
		if len(not_serving_versions) == 1 : return not_serving_versions[0]
		raise Exception(f"Service {service_name} - Il y a plus d'une version en pause ! On ne peut pas relancer. ")

	def get_not_serving_versions(self, service_name) :
		return [ v for v in self.get_service_versions(service_name) if v['servingStatus']!="SERVING" ]

	def clean_up_unused_versions(self, service_name) :
		not_serving_versions = self.get_not_serving_versions(service_name)
		serving_versions = self.get_serving_version(service_name)

		if len(serving_versions) == 0 : raise Exception(f"Service {service_name} - Aucune version ne sert le service, pas le moment de faire le ménage !")

		for v in not_serving_versions :
			self.remove_version(v)


	def remove_version(self, version) :
		service_name = self.get_service_name_from_version(version)
		print(f"Service {service_name} - Suppression de la version inutile {version['id']}")
		self.apps.services().versions().delete(appsId=self.PROJECT_NAME,servicesId=service_name,versionsId=version['id']).execute()

	def pause_service(self, service_name) :

		self.clean_up_unused_versions( service_name )
		self.stop_version( self.get_serving_version( service_name ) )

	def run_service(self, service_name) :
		self.start_version( self.get_not_serving_version(service_name) )


	def get_service_name_from_version(self, version) :
		return version['name'].split('/')[3]

	def stop_version(self, version) :
		service_name = self.get_service_name_from_version(version)
		print(f"Service {service_name} - Mise en pause de la version {version['id']}")
		self.apps.services().versions().patch(appsId=self.appsId,servicesId=service_name,versionsId=version['id'],body = {'servingStatus': 'STOPPED'},updateMask='servingStatus').execute()

	def start_version(self, version) :
		service_name = self.get_service_name_from_version(version)
		print(f"Service {service_name} - Relance de la version {version['id']}")
		self.apps.services().versions().patch(appsId=self.appsId,servicesId=service_name,versionsId=version['id'],body = {'servingStatus': 'SERVING'},updateMask='servingStatus').execute()


	######################################################################################
	#	Gestion au niveau des instances
	######################################################################################

	def restart_version(self, version) :
		service_name = self.get_service_name_from_version(version)
		print(f"Service {service_name} - Reboot de la version {version['id']}")

		for instance in self.get_instances(version) :
			self.remove_instance(instance)

	def get_instances(self, version) :
		service_name = self.get_service_name_from_version(version)
		return self.apps.services().versions().instances().list(appsId=self.appsId,servicesId=service_name,versionsId=version['id']).execute()['instances']

	def remove_instance(self, instance) :
		service_name = self.get_service_name_from_instance(instance)
		version_id = self.get_version_id_from_instance(instance)
		self.apps.services().versions().instances().delete(appsId=self.appsId,servicesId=service_name,versionsId=version_id,instancesId=instance['id']).execute()

	def get_service_name_from_instance(self, instance) :
		return instance['name'].split('/')[3]

	def get_version_id_from_instance(self, instance) :
		return instance['name'].split('/')[5]





class GCP_Service() :

	def __init__(self, service_name, gcp_manager=None):
		self.service_name = service_name
		if not gcp_manager : self.gcp_manager = GCP_Services_Manager()
		self.refresh()

	def refresh(self) :

		self.service = self.gcp_manager.get_service(self.service_name)
		self.targeted_versions_ids = [ v for v in self.service['split']['allocations'] if self.service['split']['allocations'][v]>0 ]
		self.versions = self.gcp_manager.get_service_versions(self.service_name)
		self.serving_versions_ids = [ v['id'] for v in self.gcp_manager.get_serving_versions(self.service_name) ]
		self.targeted_and_serving_versions = [ v for v in self.versions if v['id'] in self.targeted_versions_ids and v['id'] in self.serving_versions_ids ]

	def clean(self) :

		deletables_versions = [ v for v in self.versions if not v['id'] in self.targeted_versions_ids ]
		for v in deletables_versions :	self.gcp_manager.remove_version(v)

	def pause(self) :

		targeted_versions = [ v for v in self.versions if v['id'] in self.targeted_versions_ids ]
		for v in targeted_versions : self.gcp_manager.stop_version(v)

	def start(self) :

		targeted_versions = [ v for v in self.versions if v['id'] in self.targeted_versions_ids ]
		for v in targeted_versions : self.gcp_manager.start_version(v)

	def restart(self) :

		for v in self.targeted_and_serving_versions :
			self.gcp_manager.restart_version(v)