from typing import Any

from .odoo_model_wrapper import OdooModelWrapper
from .w15_settings_wrapper import W15SettingsWrapper


class OdooEnvWrapper:
    """
    Wraps Odoo Environment object providing easy access for frequently used fields, models and methods.
    """

    def __init__(self, env: Any, odoo_version: int):
        self._env = env
        self._odoo_version = odoo_version

        # Setting None in the other fields for lazy initialization

        self._w15_settings_wrapper = None

        self._locations = None
        self._lots = None
        self._partners = None
        self._product_templates = None
        self._products = None
        self._stock_inventories = None
        self._stock_inventory_lines = None
        self._stock_move_lines = None
        self._stock_moves = None
        self._stock_pickings = None
        self._stock_quants = None
        self._warehouses = None

    def __iter__(self):
        return iter(self._env)
    
    def __getattr__(self, item):
        return getattr(self._env, item)

    def __getitem__(self, item):
        return self._env[item]

    @property
    def odoo_version(self) -> int:
        """
        Returns major version of Odoo server.
        """
        return self._odoo_version

    @property
    def w15_settings(self) -> W15SettingsWrapper:
        """
        Returns object providing access to the settings of Warehouse 15 module.
        """
        if self._w15_settings_wrapper is None:
            self._w15_settings_wrapper = W15SettingsWrapper(self._env)
        return self._w15_settings_wrapper

    @property
    def storage_locations_enabled(self) -> bool:
        """
        Determines if storage locations is enabled in Odoo 'stock' (Inventory) module.
        """
        # 'stock' (Inventory) module allows enabling and disabling storage locations tracking.
        # Here's a tricky way to define if storage locations enabled.
        return self._env.user.has_group('stock.group_stock_multi_locations')

    @property
    def expiration_dates_tracking_enabled(self) -> bool:
        """
        Determines if expiration dates tracking is enabled in Odoo 'stock' (Inventory) module.
        """
        return self._env['ir.module.module'].sudo().search_count([
            ('name', '=', 'product_expiry'),
            ('state', '=', 'installed')
        ]) > 0

    @property
    def locations(self) -> OdooModelWrapper:
        if self._locations is None:
            self._locations = self._create_locations_wrapper(self._env, self.odoo_version)
        return self._locations

    @property
    def lots(self) -> OdooModelWrapper:
        if self._lots is None:
            self._lots = self._create_lots_wrapper(self._env, self.odoo_version)
        return self._lots

    @property
    def partners(self) -> OdooModelWrapper:
        """
        Providing access to all active and not blacklisted contacts from Odoo database.
        """
        if self._partners is None:
            self._partners = self._create_partners_wrapper(self._env, self.odoo_version)
        return self._partners

    @property
    def product_templates(self) -> OdooModelWrapper:
        if self._product_templates is None:
            self._product_templates = self._create_product_templates_wrapper(self._env, self.odoo_version)
        return self._product_templates

    @property
    def products(self) -> OdooModelWrapper:
        if self._products is None:
            self._products = self._create_products_wrapper(self._env, self.odoo_version)
        return self._products

    @property
    def stock_inventories(self) -> OdooModelWrapper:
        if self._stock_inventories is None:
            self._stock_inventories = self._create_stock_inventories_wrapper(self._env, self.odoo_version)
        return self._stock_inventories

    @property
    def stock_inventory_lines(self) -> OdooModelWrapper:
        if self._stock_inventory_lines is None:
            self._stock_inventory_lines = self._create_stock_inventory_lines_wrapper(self._env, self.odoo_version)
        return self._stock_inventory_lines

    @property
    def stock_move_lines(self) -> OdooModelWrapper:
        if self._stock_move_lines is None:
            self._stock_move_lines = self._create_stock_move_lines_wrapper(self._env, self.odoo_version)
        return self._stock_move_lines

    @property
    def stock_moves(self) -> OdooModelWrapper:
        if self._stock_moves is None:
            self._stock_moves = self._create_stock_moves_wrapper(self._env, self.odoo_version)
        return self._stock_moves

    @property
    def stock_pickings(self) -> OdooModelWrapper:
        if self._stock_pickings is None:
            self._stock_pickings = self._create_stock_pickings_wrapper(self._env, self.odoo_version)
        return self._stock_pickings

    @property
    def stock_quants(self) -> OdooModelWrapper:
        if self._stock_quants is None:
            self._stock_quants = self._create_stock_quants_wrapper(self._env, self.odoo_version)
        return self._stock_quants

    @property
    def warehouses(self) -> OdooModelWrapper:
        """
        Providing access to all active warehouses of all active companies from Odoo database.
        """
        if self._warehouses is None:
            self._warehouses = self._create_warehouses_wrapper(self._env, self.odoo_version)
        return self._warehouses

    @classmethod
    def _create_locations_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['stock.location'], [('active', '=', True), ('warehouse_id', '!=', False)])

    @classmethod
    def _create_lots_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 16:
            return OdooModelWrapper(env['stock.lot'], [])
        return OdooModelWrapper(env['stock.production.lot'], [])

    @classmethod
    def _create_partners_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['res.partner'], [
            ('active', '=', True),
            ('is_blacklisted', '=', False)
        ])

    @classmethod
    def _create_product_templates_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 18:
            return OdooModelWrapper(env['product.template'],
                                    [('active', '=', True), ('type', '=', 'consu'), ('is_storable', '=', True)])
        if odoo_version >= 15:
            return OdooModelWrapper(env['product.template'], [('active', '=', True), ('detailed_type', '=', 'product')])
        return OdooModelWrapper(env['product.template'], [('active', '=', True), ('type', '=', 'product')])

    @classmethod
    def _create_products_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 18:
            return OdooModelWrapper(env['product.template'],
                                    [('active', '=', True), ('type', '=', 'consu'), ('is_storable', '=', True)])
        return OdooModelWrapper(env['product.product'], [])

    @classmethod
    def _create_stock_inventories_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 15:
            raise RuntimeError('Model \'stock.inventory\' does not exists in Odoo {}'.format(odoo_version))
        return OdooModelWrapper(env['stock.inventory'], [])

    @classmethod
    def _create_stock_inventory_lines_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 15:
            raise RuntimeError('Model \'stock.inventory.line\' does not exists in Odoo {}'.format(odoo_version))
        return OdooModelWrapper(env['stock.inventory.line'], [])

    @classmethod
    def _create_stock_move_lines_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['stock.move.line'], [])

    @classmethod
    def _create_stock_moves_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['stock.move'], [])

    @classmethod
    def _create_stock_pickings_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['stock.picking'], [])

    @classmethod
    def _create_stock_quants_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        return OdooModelWrapper(env['stock.quant'], [('location_id.active', '=', True), ('warehouse_id', '!=', False)])

    @classmethod
    def _create_warehouses_wrapper(cls, env, odoo_version: int) -> OdooModelWrapper:
        if odoo_version >= 16:
            return OdooModelWrapper(env['stock.warehouse'], [
                ('active', '=', True),
                ('company_id', '!=', False),
                ('company_id.active', '=', True)
            ])

        return OdooModelWrapper(env['stock.warehouse'], [
            ('active', '=', True),
            ('company_id', '!=', False)
        ])
