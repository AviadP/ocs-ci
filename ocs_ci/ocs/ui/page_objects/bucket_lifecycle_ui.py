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

        # Navigate to Management tab
        self.do_click(self.bucket_tab["management_tab"])
        time.sleep(1)

        # Click on Lifecycle rules tab
        self.do_click(self.bucket_tab["lifecycle_rules_tab"])
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
            self.do_click(self.bucket_tab["incomplete_multipart_checkbox"])
            time.sleep(1)

            days = actions["abort_multipart"].get("days", 7)
            self.do_clear(self.bucket_tab["incomplete_multipart_days_input"])
            self.do_send_keys(self.bucket_tab["incomplete_multipart_days_input"], str(days))

        # TODO: Add other actions (expiration, transitions, etc.) when needed

        # Click create button
        self.do_click(self.bucket_tab["lifecycle_create_button"])
        time.sleep(3)

        logger.info(f"Successfully created lifecycle rule: {rule_name}")

    def edit_lifecycle_rule(self, rule_name, **kwargs):
        """
        Edit an existing lifecycle rule

        Args:
            rule_name (str): Name of the rule to edit
            **kwargs: New settings for the rule
        """
        pass

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
            time.sleep(2)

            # Get all rule rows
            rule_elements = self.get_elements(self.bucket_tab["lifecycle_rules_list"])

            # Extract rule names from the first column
            rule_names = []
            for rule in rule_elements:
                try:
                    # Get the name from the first td element
                    name_element = rule.find_element(By.XPATH, ".//td[@data-label='Name']")
                    rule_names.append(name_element.text)
                except NoSuchElementException:
                    logger.warning("Could not find name element in rule row")

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
        pass

    def toggle_rule_status(self, rule_name, enable=True):
        """
        Enable or disable a lifecycle rule

        Args:
            rule_name (str): Name of the rule
            enable (bool): True to enable, False to disable
        """
        pass
