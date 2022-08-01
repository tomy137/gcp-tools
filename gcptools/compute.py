## Ressemble beaucoup à services, mais là c'est pour les VMs
import os, datetime, time

from google.cloud import compute_v1

class GCP_Compute() :

	def __init__(self, gcp_tools):

		self.gcp_tools = gcp_tools
		self.instance_client = compute_v1.InstancesClient()
		self.PROJECT_NAME = os.environ['PROJECT_NAME']
		self.instances = []

	def get_vms(self, zone):
		self.zone = zone
		self.instances = [i for i in self.instance_client.list(project=self.PROJECT_NAME, zone=self.zone)]

	def get_vm(self, name, zone=None):
		if len(self.instances)==0 : self.get_vms(zone=zone)

		_list = [ i for i in self.instances if i.name==name ]
		if len(_list) == 1 : return VM(instance=_list[0], gcp_compute=self)
		else :
			self.gcp_tools.logger.warn(f"Pas de VM avec le nom {name}")
			return None


class VM() :

	def __init__(self, instance, gcp_compute) :
		self.instance = instance
		self.name = self.instance.name
		self.status = self.instance.status
		self.gcp_compute = gcp_compute
		self.gcp_tools = self.gcp_compute.gcp_tools

	def start(self) :
		if "RUNNING" in str(self.status) :
			self.gcp_tools.logger.debug(f"VM {self.name} already running.")
			return True
		operation = self.gcp_compute.instance_client.start( project=self.gcp_compute.PROJECT_NAME, zone=self.gcp_compute.zone, instance=self.name )
		self.wait_for_extended_operation(operation, f"start {self.name}")

	def stop(self) :
		if "TERMINATED" in str(self.status) :
			self.gcp_tools.logger.debug(f"VM {self.name} already stopped.")
			return True
		operation = self.gcp_compute.instance_client.stop( project=self.gcp_compute.PROJECT_NAME, zone=self.gcp_compute.zone, instance=self.name )
		self.wait_for_extended_operation(operation, f"stop {self.name}")


	def wait_for_extended_operation(self, operation, verbose_name):

		t0 = datetime.datetime.now()

		kwargs = {"project": self.gcp_compute.PROJECT_NAME, "operation": operation.name}

		## DOCS : https://cloud.google.com/compute/docs/samples/compute-instances-operation-check
		if operation.zone:
		    client = compute_v1.ZoneOperationsClient()
		    # Operation.zone is a full URL address of a zone, so we need to extract just the name
		    kwargs["zone"] = operation.zone.rsplit("/", maxsplit=1)[1]
		elif operation.region:
		    client = compute_v1.RegionOperationsClient()
		    # Operation.region is a full URL address of a region, so we need to extract just the name
		    kwargs["region"] = operation.region.rsplit("/", maxsplit=1)[1]
		else:
		    client = compute_v1.GlobalOperationsClient()


		finished_operation = client.wait(**kwargs)

		self.gcp_tools.logger.debug(f"{verbose_name} - Opération terminée - Status : {finished_operation.status} - Temps écoulé : {datetime.datetime.now()-t0}")

		if operation.error :
			self.gcp_tools.logger.warn( f"Error during {verbose_name} : {operation.error}" )





