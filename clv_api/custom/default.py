from typing import Any, List

from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


def after_get_document(
        env: OdooEnvWrapper,
        device_info: dict[str, Any],
        doc: dict[str, Any]
) -> dict[str, Any]:
    """
    A post-processing function that is executed after retrieving a single document.
    By default, this function returns the document unchanged.
    @param env: Odoo Environment object.
    @param device_info: Information about the device that is requesting data.
    @param doc: The document retrieved by the main logic of Warehouse 15 module.
    """

    # This is default implementation of 'after_get_document' function.
    return doc


def after_get_document_descriptions(
    env: OdooEnvWrapper,
    device_info: dict[str, Any],
    docs: List[dict[str, Any]]
) -> List[dict[str, Any]]:
    """
    A post-processing function that is executed after retrieving a list of document descriptions.
    By default, this function returns the list of documents unchanged.
    @param env: Odoo Environment object.
    @param device_info: Information about the device that is requesting data.
    @param docs: A list of documents retrieved by the main logic of Warehouse 15 module.
    """

    # This is default implementation of 'after_get_document_descriptions' function.
    return docs
