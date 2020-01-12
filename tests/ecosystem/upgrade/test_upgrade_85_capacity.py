import logging

import pytest

from ocs_ci.framework.testlib import ManageTest
from ocs_ci.framework.pytest_customization.marks import (
    ignore_leftovers, pre_upgrade, post_upgrade,
    aws_platform_required, filter_insecure_request_warning
)
from ocs_ci.ocs import constants
from ocs_ci.ocs.exceptions import TimeoutExpiredError
from ocs_ci.utility.utils import TimeoutSampler
from tests.manage.mcg.helpers import (
    retrieve_test_objects_to_pod, sync_object_directory
)


logger = logging.getLogger(__name__)


class TestUpgradeWhenClusterNearlyFull(ManageTest):
    """
    Testing operator upgrade when cluster is 85% full - expected results: TBD

    1. deploy OCP cluster - without OCS - need 6 workers, 3 for ocs, 3 for other uses
    2. create "openshift-storage" namespace with proper label
    3. create catalogsouce by using deploy_with_olm.yaml with old image
    4. install OCS operator
    5. create ocs service
    6. expend cluster with 9 OSDs - *** future ***
    7. vdbench up to 85%
        a. create fixture for checking capacity (see function: check_ceph_pool_used_space)
        b. tag non-ocs worker with label: app-node=vdbench
        c. automated run for vdbench
    8. perform upgrade (run io during upgrade)
    9. verify test results: (some validation already created)
        a. operator successfully upgrade
        b. all pods in namespace "openshift-storage" upgraded
        c. space used is same as before upgrade
    10. create Jenkins job with separate pipeline for this job
    """

    @aws_platform_required
    @filter_insecure_request_warning
    @pre_upgrade
    def test_upgrade_cluster_nearly_full(self):
        # deploy ocp
        # deploy ocs
        # check cluster status
        # fill cluster to 85%
        # check cluster status
        # upgrade
        # check cluster status
        pass

    @post_upgrade
    def test_cluster_after_upgrade(self):
        # verify upgrade
        # compare capacity to capacity before upgrade
        pass




