from typing import List, Any

from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class InventoryService:
    """
    Represents the implementation of a service for accessing to inventory.
    """

    # noinspection PyMethodMayBeStatic
    def get_items(self, env: OdooEnvWrapper, device_info: dict[str, Any], parent_id: [str, None], offset: int = 0, limit: int = 0) -> List:
        """
        Returns the list of items matching specified parent id.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param parent_id: Parent id.
        @param offset: Offset pagination parameter.
        @param limit: Limit pagination parameter.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def get_items_count(self, env: OdooEnvWrapper, device_info: dict[str, Any], parent_id: [str, None]) -> int:
        """
        Returns the number of items matching specified parent id.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param parent_id: Parent id.
        """
        return 0

    # noinspection PyMethodMayBeStatic
    def get_items_by_ids(self, env: OdooEnvWrapper, device_info: dict[str, Any], ids_list: List) -> List:
        """
        Returns the list of items matching specified ids list.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param ids_list: List of items ids to search.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def get_items_by_search_code(self, env: OdooEnvWrapper, device_info: dict[str, Any], search_data: dict[str, Any], search_mode: dict[str, Any]) -> List:
        """
        Returns the list of items matching specified search data.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param search_data: Object containing information for search (id, code, barcode, etc.).
        @param search_mode: Object containing information about search mode.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def get_items_by_string(self, env: OdooEnvWrapper, device_info: dict[str, Any], match_string: str, offset: int = 0, limit: int = 0) -> List:
        """
        Returns the list of items matching specified string.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param match_string: String to match.
        @param offset: Offset pagination parameter.
        @param limit: Limit pagination parameter.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def get_items_by_string_count(self, env: OdooEnvWrapper, device_info: dict[str, Any], match_string: str) -> int:
        """
        Returns the number of items matching specified string.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param match_string: String to match.
        """
        return 0
