import logging

# from ocs_ci.ocs import constants, defaults
from ocs_ci.framework import config
from ocs_ci.ocs.ocs_upgrade import OCSUpgrade


log = logging.getLogger(__name__)


class LVMOUpgrade(OCSUpgrade):
    def __init__(
        self,
        namespace,
        vrsion_before_upgrade,
        ocs_registry_image,
        upgrade_in_current_source,
    ):
        super().__init__(
            namespace,
            vrsion_before_upgrade,
            ocs_registry_image,
            upgrade_in_current_source,
        )

    original_ocs_version = config.ENV_DATA.get("ocs_version")
    upgrade_in_current_source = config.UPGRADE.get("upgrade_in_current_source", False)

    def run_lvmo_upgrade(self):
        print("1")

    # Pre upgrade preparations
    # Functions / methods that can be used here:
    #   OCSUpgrade.get_pre_upgrade_image()
    #   OCSUpgrade.get_csv_name_pre_upgrade(resource_name=defaults.LVM_OPERATOR_NAME)
    # Upgrade
    # post upgrade validation
