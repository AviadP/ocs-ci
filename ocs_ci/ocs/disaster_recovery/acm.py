import logging
import time

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from ocs_ci.ocs.ocp import OCP
from ocs_ci.ocs.ui.base_ui import login_ui, BaseUI
from ocs_ci.ocs.ui.views import locators
from ocs_ci.utility.utils import get_ocp_version


log = logging.getLogger(__name__)


class AcmPageNavigator(BaseUI):
    """
    ACM Page Navigator Class

    """

    def __init__(self, driver):
        super().__init__(driver)
        self.ocp_version = get_ocp_version()
        self.acm_page_nav = locators[self.ocp_version]["acm_page"]

    def navigate_welcome_page(self):
        """
        Navigate to ACM Welcome Page

        """
        log.info("Navigate into Home Page")
        self.choose_expanded_mode(mode=True, locator=self.acm_page_nav["Home"])
        self.do_click(locator=self.acm_page_nav["Welcome_page"])

    def navigate_overview_page(self):
        """
        Navigate to ACM Overview Page

        """
        log.info("Navigate into Overview Page")
        self.choose_expanded_mode(mode=True, locator=self.acm_page_nav["Home"])
        self.do_click(locator=self.acm_page_nav["Overview_page"])

    def navigate_clusters_page(self):
        """
        Navigate to ACM Clusters Page

        """
        log.info("Navigate into Clusters Page")
        self.choose_expanded_mode(
            mode=True, locator=self.acm_page_nav["Infrastructure"]
        )
        self.do_click(locator=self.acm_page_nav["Clusters_page"])

    def navigate_bare_metal_assets_page(self):
        """
        Navigate to ACM Bare Metal Assets Page

        """
        log.info("Navigate into Bare Metal Assets Page")
        self.choose_expanded_mode(
            mode=True, locator=self.acm_page_nav["Infrastructure"]
        )
        self.do_click(locator=self.acm_page_nav["Bare_metal_assets_page"])

    def navigate_automation_page(self):
        """
        Navigate to ACM Automation Page

        """
        log.info("Navigate into Automation Page")
        self.choose_expanded_mode(
            mode=True, locator=self.acm_page_nav["Infrastructure"]
        )
        self.do_click(locator=self.acm_page_nav["Automation_page"])

    def navigate_infrastructure_env_page(self):
        """
        Navigate to ACM Infrastructure Environments Page

        """
        log.info("Navigate into Infrastructure Environments Page")
        self.choose_expanded_mode(
            mode=True, locator=self.acm_page_nav["Infrastructure"]
        )
        self.do_click(locator=self.acm_page_nav["Infrastructure_environments_page"])

    def navigate_applications_page(self):
        """
        Navigate to ACM Applications Page

        """
        log.info("Navigate into Applications Page")
        self.do_click(locator=self.acm_page_nav["Applications"])

    def navigate_governance_page(self):
        """
        Navigate to ACM Governance Page

        """
        log.info("Navigate into Governance Page")
        self.do_click(locator=self.acm_page_nav["Governance"])

    def navigate_credentials_page(self):
        """
        Navigate to ACM Credentials Page

        """
        log.info("Navigate into Governance Page")
        self.do_click(locator=self.acm_page_nav["Credentials"])


class AcmAddClusters(AcmPageNavigator):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_nav = locators[self.ocp_version]["acm_page"]

    def open_clusters_page(self):
        self.navigate_clusters_page()
        time.sleep(3)
        self.do_click(self.page_nav["Import_cluster"])
        time.sleep(3)
        self.do_send_keys(
            self.page_nav["Import_cluster_enter_name"], text="Cluster-One"
        )
        time.sleep(3)
        self.do_click(self.page_nav["Import_mode"])
        # visibility = Select(self.driver.find_element_by_css_selector('button[class="pf-c-select__toggle"]'))
        log.info("PASS STEP 1")
        time.sleep(3)
        self.do_click(self.page_nav["choose_kubeconfig"])
        time.sleep(10)

        # visibility.select_by_value("2")


def verify_running_acm():
    mch_cmd = OCP(namespace="open-cluster-management")
    acm_status = mch_cmd.exec_oc_cmd(
        "get mch -o jsonpath='{.items[].status.phase}'", out_yaml_format=False
    )
    assert acm_status == "Running", f"ACM status is {acm_status}"
    acm_version = mch_cmd.exec_oc_cmd(
        "get mch -o jsonpath='{.items[].status.currentVersion}'", out_yaml_format=False
    )
    log.info(f"ACM Version Detected: {acm_version}")


def get_acm_url():
    mch_cmd = OCP(namespace="open-cluster-management")
    url = mch_cmd.exec_oc_cmd(
        "get route -ojsonpath='{.items[].spec.host}'", out_yaml_format=False
    )
    log.info(f"ACM console URL: {url}")

    return f"https://{url}"


def validate_page_title(driver, title):
    WebDriverWait(driver, 60).until(ec.title_is(title))
    log.info(f"page title: {title}")


def login_to_acm():
    url = get_acm_url()
    log.info(f"URL: {url}, {type(url)}")
    driver = login_ui(url)
    acm_title = "Red Hat Advanced Cluster Management for Kubernetes"
    validate_page_title(driver, title=acm_title)

    return driver


def copy_kubeconfig(file):
    try:
        with open(file, "r") as f:
            txt = f.readlines()
            print(txt)
            return txt

    except FileNotFoundError:
        log.error("file not found")


def test_import_clusters_with_acm():
    verify_running_acm()
    driver = login_to_acm()
    acm_nav = AcmAddClusters(driver)
    acm_nav.open_clusters_page()


# steps for import clusters:
# 1. login acm url
# 2. check if Infrastructure is expended or not
# 3. expend if not
# 4. click on "Clusters" (link name: a.pf-c-nav__link)
# 5. verify correct url
# 6. click "Import cluster" (button id="importCluster")
# 7. in "Name" field, insert free text - imported cluster name. need to get it from configuration file
# 8. verify that "Import mode" field is "Run import commands manually"
# 9. click "Save import and generate code"
# 10. verify new url
# 11. click on "copy command"
