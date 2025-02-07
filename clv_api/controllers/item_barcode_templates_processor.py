from .common_utils import CommonUtils
from .model_converter import ModelConverter
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class ItemBarcodeTemplatesProcessor:
    """
    The Item Barcode Template is a concept from the Cleverence Platform.
    This template defines a rule (typically using regular expressions)
    for parsing specific field values from a scanned barcode.

    When searching for items by barcode,
    both the original scanned barcode and the parsed values (extracted using the templates)
    are passed along Odoo module from the Cleverence app.
    This enables searching for data in Odoo by custom barcodes,
    whose format is defined in the Cleverence app.

    Let's consider a simple example.
    Suppose we have a barcode '2101234567890'.
    And a barcode template: 210{InventoryItemId:3}{SeriesName:6}{CheckSum:1}
    According to this template, the Cleverence app will parse the barcode and pass data in the following format:
    'templates': [
        {
            'InventoryItemId': '123',
            'SeriesName': '456789'
        }
    ]
    """
    _model_converter = ModelConverter()

    @classmethod
    def _search_item_by_id_and_lot(cls, env: OdooEnvWrapper, template):
        """
        Returns inventory item with specified lot by values from barcode template.
        """
        inventory_item_id = template.get('inventoryItemId'.lower(), False)
        if not inventory_item_id or not inventory_item_id.isdigit():
            return []

        series_name = template.get('seriesName'.lower(), False)

        found_item = env['product.product'].search([
            ('active', '=', True),
            ('product_tmpl_id.tracking', '=', 'lot'),
            ('id', '=', inventory_item_id)
        ], limit=1)

        found_lot = env.lots.search([
            ('name', '=', series_name)
        ], limit=1)

        if not found_item or not found_lot:
            return []

        inventory_item = cls._model_converter.product_to_inventory_item(env, found_item)
        related_data = cls._model_converter.product_to_related_data(env, found_item)

        related_data['unitOfMeasure'][0]['seriesId'] = cls._model_converter.clear_to_str(found_lot.id)
        related_data['unitOfMeasure'][0]['seriesName'] = cls._model_converter.clear_to_str(found_lot.name)

        return [{'inventoryItem': inventory_item, 'relatedData': related_data}]

    @classmethod
    def _search_item_by_id(cls, env: OdooEnvWrapper, template):
        """
        Returns inventory item by id from parsed barcode template.
        """
        inventory_item_id = template.get('inventoryItemId'.lower(), False)
        if not inventory_item_id or not inventory_item_id.isdigit():
            return []

        inventory_item_id = int(inventory_item_id)

        found_item = env['product.product'].search([
            ('active', '=', True),
            ('id', '=', inventory_item_id)
        ], limit=1)

        if not found_item:
            return []

        inventory_item = cls._model_converter.product_to_inventory_item(env, found_item)
        related_data = cls._model_converter.product_to_related_data(env, found_item)

        return [{'inventoryItem': inventory_item, 'relatedData': related_data}]

    @classmethod
    def search_by_templates(cls, env: OdooEnvWrapper, barcode_templates):
        """
        Returns inventory items, according to information from barcode templates.
        """
        if not barcode_templates:
            return []

        result = []
        for template in barcode_templates:
            items = cls._search_by_template(env, template)
            result.extend(items)

        return result

    @classmethod
    def _search_by_template(cls, env: OdooEnvWrapper, barcode_template):
        if not barcode_template:
            return []

        normalized_template = {key.lower(): value for key, value in barcode_template.items()}

        if 'inventoryItemId'.lower() in normalized_template and 'seriesName'.lower() in normalized_template:
            return cls._search_item_by_id_and_lot(env, normalized_template)
        elif 'inventoryItemId'.lower() in normalized_template:
            return cls._search_item_by_id(env, normalized_template)

        return []
