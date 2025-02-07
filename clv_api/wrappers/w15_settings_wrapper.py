from typing import Any

from ..utils.type_checker import TypeChecker


class W15SettingsWrapper:
    """
    Wraps Odoo Environment object providing easy access to the settings of Warehouse 15 module.
    """

    def __init__(self, env: Any):
        self._config_params = env['ir.config_parameter'].sudo()

    @property
    def warehouse15_connected(self) -> bool:
        """
        Returns value of 'clv_api.clv_warehouse15_connected' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_warehouse15_connected'))

    @warehouse15_connected.setter
    def warehouse15_connected(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_warehouse15_connected' setting.
        """
        self._config_params.set_param('clv_api.clv_warehouse15_connected', value)

    @property
    def check_connection_failed(self) -> bool:
        """
        Returns value of 'clv_api.clv_check_connection_failed' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_check_connection_failed'))

    @check_connection_failed.setter
    def check_connection_failed(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_check_connection_failed' setting.
        """
        self._config_params.set_param('clv_api.clv_check_connection_failed', value)

    @property
    def default_scan_locations(self) -> bool:
        """
        Returns value of 'clv_api.clv_default_scan_locations' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_default_scan_locations'))

    @default_scan_locations.setter
    def default_scan_locations(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_default_scan_locations' setting.
        """
        self._config_params.set_param('clv_api.clv_default_scan_locations', value)

    @property
    def allow_only_lowest_level_locations(self) -> bool:
        """
        Returns value of 'clv_api.clv_allow_only_lowest_level_locations' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_allow_only_lowest_level_locations'))

    @allow_only_lowest_level_locations.setter
    def allow_only_lowest_level_locations(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_allow_only_lowest_level_locations' setting.
        """
        self._config_params.set_param('clv_api.clv_allow_only_lowest_level_locations', value)

    @property
    def auto_create_backorders(self) -> bool:
        """
        Returns value of 'clv_api.clv_auto_create_backorders' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_auto_create_backorders'))

    @auto_create_backorders.setter
    def auto_create_backorders(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_auto_create_backorders' setting.
        """
        self._config_params.set_param('clv_api.clv_auto_create_backorders', value)

    @property
    def scan_serials_on_allocation(self) -> bool:
        """
        Returns value of 'clv_api.clv_scan_serials_on_allocation' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_scan_serials_on_allocation'))

    @scan_serials_on_allocation.setter
    def scan_serials_on_allocation(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_scan_serials_on_allocation' setting.
        """
        self._config_params.set_param('clv_api.clv_scan_serials_on_allocation', value)

    @property
    def ship_expected_actual_lines(self) -> bool:
        """
        Returns value of 'clv_api.clv_ship_expected_actual_lines' setting.
        """
        return TypeChecker.get_as_bool(self._config_params.get_param('clv_api.clv_ship_expected_actual_lines'))

    @ship_expected_actual_lines.setter
    def ship_expected_actual_lines(self, value: bool) -> None:
        """
        Sets value of 'clv_api.clv_ship_expected_actual_lines' setting.
        """
        self._config_params.set_param('clv_api.clv_ship_expected_actual_lines', value)

    def unlink_all(self) -> None:
        """
        Unlinks all Warehouse 15 settings from Odoo database.
        """
        self._config_params.search([('key', '=', 'clv_api.clv_warehouse15_connected')]).unlink()
        self._config_params.search([('key', '=', 'clv_api.clv_check_connection_failed')]).unlink()

        self._config_params.search([('key', '=', 'clv_api.clv_default_scan_locations')]).unlink()
        self._config_params.search([('key', '=', 'clv_api.clv_allow_only_lowest_level_locations')]).unlink()
        self._config_params.search([('key', '=', 'clv_api.clv_auto_create_backorders')]).unlink()
        self._config_params.search([('key', '=', 'clv_api.clv_scan_serials_on_allocation')]).unlink()
        self._config_params.search([('key', '=', 'clv_api.clv_ship_expected_actual_lines')]).unlink()
