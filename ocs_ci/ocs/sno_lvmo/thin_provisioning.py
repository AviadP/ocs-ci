import logging

from ocs_ci.ocs.ocp import OCP
from ocs_ci.ocs.constants import OPENSHIFT_STORAGE_NAMESPACE, LVMCLUSTER

log = logging.getLogger(__name__)


class LVMCluster(object):
    def __init__(self):
        self.lvm = OCP(namespace=OPENSHIFT_STORAGE_NAMESPACE, resource_name=LVMCLUSTER)

    def get_lvm_cluster(self):
        return self.lvm.get()
