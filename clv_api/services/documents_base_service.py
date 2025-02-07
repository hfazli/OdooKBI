from typing import List, Any

from ..wrappers.clv_doc_wrapper import ClvDocWrapper
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class DocumentsBaseService:
    """
    Represents the basic implementation of a service for accessing to documents.
    """

    # noinspection PyMethodMayBeStatic
    def get_document_descriptions_count(self, env: OdooEnvWrapper, device_info: dict[str, Any]) -> int:
        """
        Returns the number of documents available to work with.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        """
        return 0

    # noinspection PyMethodMayBeStatic
    def get_document_descriptions(self, env: OdooEnvWrapper, device_info: dict[str, Any], offset: int, limit: int) -> List:
        """
        Returns the list of documents description available to work with.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param offset: Offset pagination parameter.
        @param limit: Limit pagination parameter.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def get_document(self, env: OdooEnvWrapper, device_info: dict[str, Any], search_code: str, search_mode: str) -> [dict[str, Any] | None]:
        """
        Returns the list of documents description available to work with.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param search_code: String to search (id, code or barcode).
        @param search_mode: Searching mode ('byCode' or 'byBarcode').
        """
        return None

    def set_document(self, env: OdooEnvWrapper, device_info: dict[str, Any], doc: ClvDocWrapper) -> None:
        """
        Processes document completed on the mobile device.
        @param env: Odoo Environment object.
        @param device_info: Information about the device that is requesting data.
        @param doc: Document completed on the mobile device.
        """
        pass
