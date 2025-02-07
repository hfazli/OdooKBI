from typing import Any, List

from .clv_doc_line_wrapper import ClvDocLineWrapper
from ..utils.type_checker import TypeChecker


class ClvDocWrapper:
    """
    Wraps Cleverence document dictionary object, providing more convenient access to frequently used attributes.
    """

    def __init__(self, doc: dict[str, Any]):
        self._doc = doc

        # Setting None in the other fields for lazy initialization

        self._actual_lines = None

    def __iter__(self):
        return iter(self._doc)

    def __getattr__(self, item):
        return getattr(self._doc, item)

    def __getitem__(self, item):
        return self._doc[item]

    @property
    def actual_lines(self) -> List[ClvDocLineWrapper]:
        """
        Returns actual lines of Cleverence document.
        """
        if self._actual_lines is None:
            lines = self._doc.get('actualLines')
            if lines is None:
                lines = []
            self._actual_lines = [ClvDocLineWrapper(line) for line in lines]

        return self._actual_lines

    @property
    def auto_apply_inventory_adjustment(self) -> bool:
        """
        Returns value of 'autoApplyInventoryAdjustment' field of Cleverence document.
        """
        # Field names from Warehouse 15 should follow camelCase convention,
        # but older versions mistakenly return them in PascalCase.
        # For backward compatibility, both formats are supported.
        value = TypeChecker.get_as_bool(self._doc.get('autoApplyInventoryAdjustment'))
        return value or TypeChecker.get_as_bool(self._doc.get('AutoApplyInventoryAdjustment'))

    @property
    def created_on_device(self) -> bool:
        """
        Indicates that the document was created on a mobile device without a supporting document in Odoo.
        """
        # The simplest way is to check id of the document.
        return self.id.startswith('new_')

    @property
    def customer_vendor_id(self) -> str:
        """
        Returns id of the customer (or vendor) to whom this Cleverence document is assigned.
        """
        return TypeChecker.get_as_str(self._doc.get('customerVendorId'))

    @property
    def device_id(self) -> str:
        """
        Returns id of the device on which Cleverence document was completed.
        """
        return TypeChecker.get_as_str(self._doc.get('deviceId'))

    @property
    def document_type_name(self) -> str:
        """
        Returns name of type of Cleverence document.
        """
        return TypeChecker.get_as_str(self._doc.get('documentTypeName'))

    @property
    def id(self) -> str:
        """
        Returns id of Cleverence document.
        """
        return TypeChecker.get_as_str(self._doc.get('id'))

    @property
    def name(self) -> str:
        """
        Returns name of Cleverence document.
        """
        return TypeChecker.get_as_str(self._doc.get('name'))

    @property
    def scan_locations(self) -> bool:
        """
        Returns value of 'scanLocations' field of Cleverence document.
        """
        return TypeChecker.get_as_bool(self._doc.get('scanLocations'))

    @property
    def rewrite_all_stock(self) -> bool:
        """
        Returns value of 'rewriteAllStock' field of Cleverence document.
        """
        # Field names from Warehouse 15 should follow camelCase convention,
        # but older versions mistakenly return them in PascalCase.
        # For backward compatibility, both formats are supported.
        value = TypeChecker.get_as_bool(self._doc.get('rewriteAllStock'))
        return value or TypeChecker.get_as_bool(self._doc.get('RewriteAllStock'))

    @property
    def rewrite_counted(self) -> bool:
        """
        Returns value of 'rewriteCounted' field of Cleverence document.
        """
        # Field names from Warehouse 15 should follow camelCase convention,
        # but older versions mistakenly return them in PascalCase.
        # For backward compatibility, both formats are supported.
        value = TypeChecker.get_as_bool(self._doc.get('rewriteCounted'))
        return value or TypeChecker.get_as_bool(self._doc.get('RewriteCounted'))

    @property
    def user_id(self) -> str:
        """
        Returns id of the user who completed Cleverence document.
        """
        return TypeChecker.get_as_str(self._doc.get('userId'))

    @property
    def warehouse_id(self) -> str:
        """
        Returns id of the warehouse specified in Cleverence document.
        """
        # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
        warehouse_id = TypeChecker.get_as_str(self._doc.get('warehouseId'))
        warehouse_external_id = TypeChecker.get_as_str(self._doc.get('warehouseExternalId'))
        return warehouse_id or warehouse_external_id
