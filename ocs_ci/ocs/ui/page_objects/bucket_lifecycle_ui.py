import logging
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ocs_ci.ocs.ui.page_objects.confirm_dialog import ConfirmDialog
from ocs_ci.ocs.ui.page_objects.object_storage import ObjectStorage

logger = logging.getLogger(__name__)


class BucketLifecycleUI(ObjectStorage, ConfirmDialog):
    """
    A class for bucket lifecycle policy UI operations
    """

    def verify_lifecycle_policy_in_backend(self, bucket_name, mcg_obj, expected_policy=None):
        """
        Verify lifecycle policy exists in backend S3 API

        Args:
            bucket_name (str): Name of the bucket
            mcg_obj: MCG object with S3 client
            expected_policy (LifecyclePolicy, optional): Expected policy to compare

        Returns:
            dict: The lifecycle configuration from backend
        """
        try:
            response = mcg_obj.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            logger.info(f"Retrieved lifecycle configuration: {response}")

            if expected_policy:
                expected_dict = expected_policy.as_dict()
                # Remove ResponseMetadata for comparison
                response.pop("ResponseMetadata", None)
                assert response == expected_dict, f"Policy mismatch. Expected: {expected_dict}, Got: {response}"

            return response
        except Exception as e:
            logger.error(f"Failed to get lifecycle configuration: {e}")
            return None

    def navigate_to_bucket_lifecycle(self, bucket_name):
        """
        Navigate to a specific bucket's lifecycle rules page

        Args:
            bucket_name (str): Name of the bucket
        """
        logger.info(f"Navigating to lifecycle rules for bucket: {bucket_name}")

        # Navigate to buckets page first
        self.navigate_buckets_page()

        # Search for the bucket
        self.do_send_keys(self.generic_locators["search_resource_field"], bucket_name)
        time.sleep(2)

        # Click on the bucket name to enter bucket details
        self.do_click(f"//tr//a[contains(text(), '{bucket_name}')]", By.XPATH)
        time.sleep(2)

        # Navigate to Management tab (automatically goes to Lifecycle rules)
        self.do_click(self.bucket_tab["management_tab"])
        time.sleep(2)

        logger.info("Navigated to lifecycle rules page")

    def create_lifecycle_rule(self, **kwargs):
        """
        Create a new lifecycle rule

        Args:
            rule_name (str): Name for the rule
            scope (str): 'whole_bucket' or 'targeted'
            prefix (str, optional): Object key prefix filter
            tags (dict, optional): Object tag filters
            min_size (str, optional): Minimum object size filter
            max_size (str, optional): Maximum object size filter
            actions (dict): Dictionary of lifecycle actions
        """
        rule_name = kwargs.get("rule_name")
        scope = kwargs.get("scope", "whole_bucket")
        actions = kwargs.get("actions", {})

        logger.info(f"Creating lifecycle rule: {rule_name}")

        # Click create lifecycle rule button
        self.do_click(self.bucket_tab["create_lifecycle_rule_button"])
        time.sleep(2)

        # Enter rule name
        self.do_send_keys(self.bucket_tab["rule_name_input"], rule_name)

        # Select rule scope
        if scope == "whole_bucket" or scope == "global":
            self.do_click(self.bucket_tab["rule_scope_global"])
        else:
            self.do_click(self.bucket_tab["rule_scope_targeted"])
            # TODO: Add prefix, tags, size filters when needed

        time.sleep(1)

        # Handle incomplete multipart uploads action
        if "abort_multipart" in actions:
            # First click the accordion to expand the section
            self.do_click(self.bucket_tab["incomplete_multipart_checkbox"])
            time.sleep(1)

            # Then click the checkbox to enable the policy
            self.do_click(self.bucket_tab["incomplete_multipart_enable_checkbox"])
            time.sleep(2)  # Wait for the days input field to appear

            # Wait for the days input field to be available
            self.page_has_loaded()

            days = actions["abort_multipart"].get("days", 7)
            self.do_clear(self.bucket_tab["incomplete_multipart_days_input"])
            self.do_send_keys(self.bucket_tab["incomplete_multipart_days_input"], str(days))

        # TODO: Add other actions (expiration, transitions, etc.) when needed

        # Wait a moment for the form to be ready and click create button
        time.sleep(2)

        # Scroll to ensure the Create button is visible
        create_button = self.get_elements(self.bucket_tab["lifecycle_create_button"])[0]
        self.driver.execute_script("arguments[0].scrollIntoView();", create_button)
        time.sleep(1)

        self.do_click(self.bucket_tab["lifecycle_create_button"])
        time.sleep(3)

        # Navigate back to the lifecycle rules list page to verify creation
        # Click the Management tab again to go back to the rules list
        self.do_click(self.bucket_tab["management_tab"])
        time.sleep(2)

        logger.info(f"Successfully created lifecycle rule: {rule_name}")

    def delete_lifecycle_rule(self, rule_name):
        """
        Delete a lifecycle rule

        Args:
            rule_name (str): Name of the rule to delete
        """
        logger.info(f"Deleting lifecycle rule: {rule_name}")

        try:
            # Click kebab menu for the specific rule
            kebab_locator = self.bucket_tab["rule_kebab_menu"].format(rule_name)
            self.do_click(kebab_locator)
            time.sleep(1)

            # Click delete option
            self.do_click(self.bucket_tab["delete_rule_option"])
            time.sleep(1)

            # Confirm deletion (assuming there's a confirmation dialog)
            # This might need adjustment based on actual UI
            self.confirm_action()

            logger.info(f"Successfully deleted lifecycle rule: {rule_name}")

        except Exception as e:
            logger.error(f"Failed to delete lifecycle rule {rule_name}: {e}")
            raise

    def get_lifecycle_rules_list(self):
        """
        Get list of all lifecycle rules for current bucket

        Returns:
            list: List of rule names
        """
        try:
            # Wait for rules table to load
            time.sleep(3)

            # Ensure we're on the right page
            self.page_has_loaded()

            # Get all rule rows using multiple possible locators
            rule_elements = self.get_elements(self.bucket_tab["lifecycle_rules_list"])

            # If no elements found with primary locator, try alternatives
            if not rule_elements:
                # Try alternative table selectors
                alternative_locators = [
                    "//table//tbody/tr",
                    "//table//tr[position()>1]",  # Skip header row
                    "//div[contains(@class, 'rules')]//tr",
                    "//tbody/tr",
                ]

                for alt_locator in alternative_locators:
                    rule_elements = self.get_elements((alt_locator, By.XPATH))
                    if rule_elements:
                        logger.info(f"Found rules using alternative locator: {alt_locator}")
                        break

            # Extract rule names from the rows
            rule_names = []
            for rule in rule_elements:
                try:
                    # Try multiple ways to get the rule name
                    name_element = None

                    # Method 1: data-label='Name'
                    try:
                        name_element = rule.find_element(By.XPATH, ".//td[@data-label='Name']")
                    except NoSuchElementException:
                        pass

                    # Method 2: First td element
                    if not name_element:
                        try:
                            name_element = rule.find_element(By.XPATH, ".//td[1]")
                        except NoSuchElementException:
                            pass

                    # Method 3: Any element with rule name pattern
                    if not name_element:
                        try:
                            name_element = rule.find_element(
                                By.XPATH,
                                ".//*[contains(text(), 'rule') or contains(text(), 'multipart')]",
                            )
                        except NoSuchElementException:
                            pass

                    if name_element and name_element.text.strip():
                        rule_names.append(name_element.text.strip())
                    else:
                        logger.warning(f"Could not extract rule name from row: {rule.get_attribute('outerHTML')[:200]}")

                except Exception as row_error:
                    logger.warning(f"Error processing rule row: {row_error}")

            logger.info(f"Found {len(rule_names)} lifecycle rules: {rule_names}")
            return rule_names

        except Exception as e:
            logger.error(f"Failed to get lifecycle rules list: {e}")
            return []

    def get_rule_details(self, rule_name):
        """
        Get details of a specific lifecycle rule

        Args:
            rule_name (str): Name of the rule

        Returns:
            dict: Rule details including status, scope, filters, and actions
        """
        # TODO: Implement rule details retrieval when needed
        logger.info(f"Getting details for rule: {rule_name}")
        return {}

    def toggle_rule_status(self, rule_name, enable=True):
        """
        Enable or disable a lifecycle rule

        Args:
            rule_name (str): Name of the rule
            enable (bool): True to enable, False to disable
        """
        # TODO: Implement rule status toggle when needed
        action = "enable" if enable else "disable"
        logger.info(f"Toggling rule '{rule_name}' to {action}")
        raise NotImplementedError("Rule status toggle not yet implemented")
