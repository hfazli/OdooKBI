from datetime import datetime
from typing import Any

from ..utils.type_checker import TypeChecker


class ClvDocLineWrapper:
    """
    Wraps Cleverence document line dictionary object, providing more convenient access to frequently used attributes.
    """

    def __init__(self, line: dict[str, Any]):
        self._line = line

        # Setting None in the other fields for lazy initialization

        self._actual_quantity = None
        self._barcode = None
        self._bound_document_line_uid = None
        self._expiration_date = None
        self._first_storage_id = None
        self._inventory_item_id = None
        self._inventory_item_name = None
        self._second_storage_id = None
        self._serial_number = None
        self._series_name = None
        self._uid = None
        self._unit_of_measure_id = None

    def __iter__(self):
        return iter(self._line)

    def __getattr__(self, item):
        return getattr(self._line, item)

    def __getitem__(self, item):
        return self._line[item]

    @property
    def actual_quantity(self) -> float:
        """
        Returns actual quantity specified in document line.
        """
        if self._actual_quantity is None:
            self._actual_quantity = TypeChecker.get_as_float(self._line.get('actualQuantity'))
        return self._actual_quantity

    @actual_quantity.setter
    def actual_quantity(self, value: float) -> None:
        self._actual_quantity = value
        self._line['actualQuantity'] = value

    @property
    def barcode(self) -> str:
        """
        Returns barcode specified in document line.
        """
        if self._barcode is None:
            self._barcode = TypeChecker.get_as_str(self._line.get('barcode'))
        return self._barcode

    @property
    def bound_document_line_uid(self) -> str:
        """
        Returns if of bound document line.
        """
        if self._bound_document_line_uid is None:
            # noinspection SpellCheckingInspection
            self._bound_document_line_uid = TypeChecker.get_as_str(self._line.get('bindedDocumentLineUid'))
        return self._bound_document_line_uid

    @property
    def expiration_date(self) -> [datetime, bool]:
        """
        Returns expiration date specified in document line or False if expiration date is not specified.
        """
        if self._expiration_date is None:
            # Correct field is 'expirationDate'. 'expiryDate' and 'expiredDate' is left for backward compatibility
            value = self._line.get('expirationDate') or self._line.get('expiryDate') or self._line.get('expiredDate')
            if not value:
                self._expiration_date = False
            else:
                value = TypeChecker.get_as_datetime(value)
                # We interpret '0001-01-01 00:00:00' as the expiration date is not set
                if value == datetime.min:
                    value = False
                self._expiration_date = value
        return self._expiration_date

    @property
    def first_storage_id(self) -> str:
        """
        Returns source ("from") location id specified in document line.
        """
        if self._first_storage_id is None:
            self._first_storage_id = TypeChecker.get_as_str(self._line.get('firstStorageId'))
        return self._first_storage_id

    @property
    def inventory_item_id(self) -> str:
        """
        Returns inventory item id specified in document line.
        """
        if self._inventory_item_id is None:
            self._inventory_item_id = TypeChecker.get_as_str(self._line.get('inventoryItemId'))
        return self._inventory_item_id

    @property
    def inventory_item_name(self) -> str:
        """
        Returns inventory item name specified in document line.
        """
        if self._inventory_item_name is None:
            self._inventory_item_name = TypeChecker.get_as_str(self._line.get('inventoryItemName'))
        return self._inventory_item_name

    @property
    def second_storage_id(self) -> str:
        """
        Returns destination ("to") location id specified in document line.
        """
        if self._second_storage_id is None:
            self._second_storage_id = TypeChecker.get_as_str(self._line.get('secondStorageId'))
        return self._second_storage_id

    @property
    def serial_number(self) -> str:
        """
        Returns serial number specified in document line.
        """
        if self._serial_number is None:
            self._serial_number = TypeChecker.get_as_str(self._line.get('serialNumber'))
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value: str) -> None:
        """
        Sets serial number specified in document line.
        """
        self._serial_number = value
        self._line['serialNumber'] = value

    @property
    def series_name(self) -> str:
        """
        Returns series name (batch/lot) specified in document line.
        """
        if self._series_name is None:
            self._series_name = TypeChecker.get_as_str(self._line.get('seriesName'))
        return self._series_name

    @property
    def uid(self) -> str:
        """
        Returns unique identifier of document line.
        """
        if self._uid is None:
            self._uid = TypeChecker.get_as_str(self._line.get('uid'))
        return self._uid

    @property
    def unit_of_measure_id(self) -> str:
        """
        Returns unit of measure id specified in document line.
        """
        if self._unit_of_measure_id is None:
            self._unit_of_measure_id = TypeChecker.get_as_str(self._line.get('unitOfMeasureId'))
        return self._unit_of_measure_id

    @property
    def from_location_id(self) -> str:
        return self.first_storage_id

    @property
    def to_location_id(self) -> str:
        return self.second_storage_id or self.first_storage_id
