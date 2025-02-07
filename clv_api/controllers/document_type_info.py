from enum import Enum


class BusinessLocationType(Enum):
    """
    Logical location type
    """
    SRC = 1  # SOURCE LOCATION
    DEST = 2  # DESTINATION LOCATION


class DocumentTypeInfo:
    """
    Information about document type
    """

    def __init__(self, odoo_sequence_code: str,
                 clv_api_name: str,
                 main_location_type: BusinessLocationType,
                 can_ignore_scan_locations: bool,
                 generate_fake_serial_if_empty: bool,
                 actual_lines_ignores_zero_qty_done: bool,
                 can_overwrite_fake_serial_numbers: bool):

        self._odoo_sequence_code = odoo_sequence_code
        self._clv_api_name = clv_api_name
        self._main_location_type = main_location_type
        self._can_ignore_scan_locations = can_ignore_scan_locations
        self._generate_fake_serial_if_empty = generate_fake_serial_if_empty
        self._actual_lines_ignores_zero_qty_done = actual_lines_ignores_zero_qty_done
        self._can_overwrite_fake_serial_numbers = can_overwrite_fake_serial_numbers

    @property
    def odoo_sequence_code(self) -> str:
        return self._odoo_sequence_code

    @property
    def clv_api_name(self) -> str:
        return self._clv_api_name

    @property
    def main_location_type(self) -> BusinessLocationType:
        return self._main_location_type

    @property
    def can_ignore_scan_locations(self) -> bool:
        return self._can_ignore_scan_locations

    @property
    def generate_fake_serial_if_empty(self) -> bool:
        return self._generate_fake_serial_if_empty

    @property
    def actual_lines_ignores_zero_qty_done(self) -> bool:
        return self._actual_lines_ignores_zero_qty_done

    @property
    def can_overwrite_fake_serial_numbers(self) -> bool:
        return self._can_overwrite_fake_serial_numbers
