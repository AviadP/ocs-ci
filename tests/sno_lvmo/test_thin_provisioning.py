import logging

from ocs_ci.ocs.sno_lvmo.thin_provisioning import LVMCluster

log = logging.getLogger(__name__)


def test_validate_lvm_cluster():
    lvm = LVMCluster()
    log.debug(lvm)
    assert lvm.get_lvm_cluster(), "No LVM Cluster found"
