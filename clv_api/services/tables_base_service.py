from typing import List, Any

from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class TablesBaseService:
    """
    Represents the basic implementation of a service for accessing data from tables.
    """

    # noinspection PyMethodMayBeStatic
    def get_rows_count(self, env: OdooEnvWrapper, device_info: dict[str, Any], query: dict[str, Any]) -> int:
        """
        Returns the number of rows matching the query.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param query: Description of the query to the table.
        """
        return 0

    # noinspection PyMethodMayBeStatic
    def get_rows(self, env: OdooEnvWrapper, device_info: dict[str, Any], query: dict[str, Any], offset: int = 0, limit: int = 0) -> List:
        """
        Returns rows corresponding to the query and pagination parameters.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param query: Description of the query to the table.
        @param offset: Offset pagination parameter.
        @param limit: Limit pagination parameter.
        """
        return []
