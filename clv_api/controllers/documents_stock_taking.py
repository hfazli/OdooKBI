import logging
from datetime import datetime
from typing import Union, Tuple, List, Any

from .common_utils import CommonUtils
from .model_converter import ModelConverter
from ..wrappers.clv_doc_line_wrapper import ClvDocLineWrapper
from ..wrappers.clv_doc_wrapper import ClvDocWrapper
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper

try:
    from ..custom.custom import after_get_document, after_get_document_descriptions
except ImportError:
    from ..custom.default import after_get_document, after_get_document_descriptions


class DocumentStockTakingImpl:
    """
    Implements the processing of stock taking documents.
    """
    _model_converter = ModelConverter()
    _cutils = CommonUtils()
    _logger = logging.getLogger(__name__)

    def get_descriptions(
            self,
            env: OdooEnvWrapper,
            document_type_name: str,
            offset: Union[int, None],
            limit: Union[int, None],
            request_count: Union[bool, None]):

        result = {}
        if request_count:
            result['totalCount'] = self._get_inv_adj_doc_descriptions_count(env)
            return result

        result['result'] =  after_get_document_descriptions(env, {}, self._generate_inv_adj_doc_descriptions(env))

        return result

    def get_document(
            self,
            env: OdooEnvWrapper,
            search_mode: str,
            search_code: str,
            document_type_name: str):

        stock_taking_id = CommonUtils.decode_stock_taking_id(search_code)
        warehouse_id = stock_taking_id

        found_warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True),
            ('id', '=', warehouse_id)
        ])

        if found_warehouses and len(found_warehouses) > 0:
            warehouse = found_warehouses[0]
            return self._generate_inv_adj_doc(warehouse, env)

        return None

    def set_document(self, env: OdooEnvWrapper, doc, device_info):
        if doc is None:
            raise RuntimeError('Document is null')

        doc_wrapper = ClvDocWrapper(doc)

        if doc_wrapper.created_on_device and not doc_wrapper.actual_lines:
            raise RuntimeError('Document is empty. You must complete it before submitting to Odoo')

        warehouse_id = doc_wrapper.warehouse_id
        if not warehouse_id:
            raise RuntimeError('Warehouse is not specified')

        warehouse_id = CommonUtils.convert_warehouse_id_from_clv_to_odoo(warehouse_id)
        found_warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True),
            ('id', '=', warehouse_id)
        ])
        if not found_warehouses or len(found_warehouses) == 0:
            raise RuntimeError('Unknown or inactive warehouse id')

        warehouse = found_warehouses[0]
        return self._set_inv_adj_doc(doc_wrapper, device_info, warehouse, env)

    def _get_inv_adj_doc_descriptions_count(self, env: OdooEnvWrapper) -> int:
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        # So, count of inventory adjustment documents is equal to warehouse count.
        return env['stock.warehouse'].searc_count([
            ('active', '=', True),
            ('company_id.active', '=', True)
        ])

    def _generate_inv_adj_doc_descriptions(self, env: OdooEnvWrapper):
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        descriptions = []

        warehouses = env['stock.warehouse'].search([
            ('active', '=', True),
            ('company_id.active', '=', True)
        ])

        for warehouse in warehouses:
            scan_locations = env.storage_locations_enabled \
                             and bool(warehouse.lot_stock_id.child_ids) \
                             and env.w15_settings.default_scan_locations

            modified_warehouse_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id)

            inv_adj_doc = {
                'id': CommonUtils.encode_stock_taking_id(warehouse.id),
                'name': 'Full inventory adjustment',
                'documentTypeName': 'StockTaking',
                'distributeByBarcode': True,
                'autoAppointed': False,
                'scanLocations': scan_locations,
                # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
                'warehouseExternalId': self._model_converter.clear_to_str(modified_warehouse_id),
                'warehouseId': self._model_converter.clear_to_str(modified_warehouse_id),
                'warehouseName': self._model_converter.clear_to_str(warehouse.name),
                'resultDocumentType': 'StockTaking',
                'sourceDocumentType': 'StockTaking'
            }
            descriptions.append(inv_adj_doc)

        return descriptions

    def _generate_inv_adj_doc(self, warehouse, env: OdooEnvWrapper):
        # Odoo does not have any specific document for stock taking process,
        # therefore we generate fake inventory adjustment document for each Odoo warehouse.
        scan_locations = env.storage_locations_enabled \
                         and bool(warehouse.lot_stock_id.child_ids) \
                         and env.w15_settings.default_scan_locations

        modified_warehouse_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id)

        doc = {
            'id': CommonUtils.encode_stock_taking_id(warehouse.id),
            'name': 'Full inventory adjustment',
            'documentTypeName': 'StockTaking',
            'distributeByBarcode': True,
            'autoAppointed': False,
            'scanLocations': scan_locations,
            # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
            'warehouseExternalId': self._model_converter.clear_to_str(modified_warehouse_id),
            'warehouseId': self._model_converter.clear_to_str(modified_warehouse_id),
            'warehouseName': self._model_converter.clear_to_str(warehouse.name),
            'resultDocumentType': 'StockTaking',
            'sourceDocumentType': 'StockTaking'
        }

        stock_quants = env['stock.quant'].search([
            ('warehouse_id', '=', warehouse.id),
            ('location_id.active', '=', True)
        ])

        expected_lines = []
        actual_lines = []

        for stock_quant in stock_quants:
            if stock_quant.quantity <= 0 and not stock_quant.inventory_quantity_set and stock_quant.inventory_quantity <= 0:
                continue

            expected_line = {
                'uid': self._model_converter.clear_to_str(stock_quant.id),
                'inventoryItemId': self._model_converter.clear_to_str(stock_quant.product_id.id),
                'expectedQuantity': self._model_converter.clear_to_str(stock_quant.quantity),
                'actualQuantity': self._model_converter.clear_to_str(stock_quant.inventory_quantity),
                'unitOfMeasureId': self._model_converter.clear_to_str(stock_quant.product_uom_id.id),
                'inventoryItemName': self._model_converter.clear_to_str(stock_quant.product_id.name),
                'inventoryItemBarcode': self._model_converter.clear_to_str(stock_quant.product_id.barcode),
                'unitOfMeasureName': self._model_converter.clear_to_str(stock_quant.product_uom_id.name),
                'registrationDate': str(),
                'documentId': self._model_converter.clear_to_str(doc['id']),
                'lastChangeDate': str(),
                'price': str(),
                'purchasePrice': str(),
                'sourceDocumentId': str(),
                'firstStorageId': self._model_converter.clear_to_str(stock_quant.location_id.id)
            }

            if stock_quant.tracking == 'serial':
                expected_line['serialNumber'] = self._model_converter.clear_to_str(stock_quant.lot_id.name)
            elif stock_quant.tracking == 'lot':
                expected_line['seriesId'] = self._model_converter.clear_to_str(stock_quant.lot_id.id)
                expected_line['seriesName'] = self._model_converter.clear_to_str(stock_quant.lot_id.name)

            expected_lines.append(expected_line)

        doc['expectedLines'] = expected_lines
        doc['actualLines'] = actual_lines

        return {'document': after_get_document(env, {}, doc)}

    def _set_inv_adj_doc(self, doc: ClvDocWrapper, device_info, warehouse, env: OdooEnvWrapper):

        auto_apply_inventory_adjustment = doc.auto_apply_inventory_adjustment
        rewrite_all_stock = doc.rewrite_all_stock
        rewrite_counted = doc.rewrite_counted

        modified_stock_ids = []
        if doc.actual_lines:
            expiration_dates_enabled = env.expiration_dates_tracking_enabled
            grouped_actual_lines = self._group_actual_lines(doc.actual_lines, expiration_dates_enabled)

            for group_key, actual_qty in grouped_actual_lines.items():

                location_id, product_id, uom_id, lot_name, expiration_date = group_key

                if location_id:
                    if env['stock.location'].search_count([('id', '=', location_id), ('warehouse_id', '=', warehouse.id)]) < 1:
                        raise RuntimeError('Document contains actual line with location of another warehouse')
                else:
                    location_id = warehouse.lot_stock_id.id

                domain_filter = [
                    ('product_id.id', '=', product_id),
                    ('product_uom_id.id', '=', uom_id),
                    ('location_id.id', '=', location_id),
                    ('warehouse_id.id', '=', warehouse.id),
                    ('company_id.id', '=', warehouse.company_id.id)
                ]

                if lot_name:
                    domain_filter.append(('lot_id.name', '=', lot_name))

                found_stock_quants = env['stock.quant'].search(domain_filter, limit=1)
                if found_stock_quants and len(found_stock_quants) > 0:
                    existing_stock_quant = found_stock_quants[0]

                    # In case 'RewriteAllStock' option is disabled and 'stock.quant' line was not modified and was not scanned then skip it
                    if not existing_stock_quant.inventory_quantity_set and not rewrite_all_stock and actual_qty == 0:
                        continue

                    inventory_qty = actual_qty
                    if not rewrite_counted:
                        inventory_qty = inventory_qty + existing_stock_quant.inventory_quantity

                    values = {
                        'inventory_quantity': inventory_qty,
                        'inventory_quantity_set': True,
                        'last_count_date': datetime.now()
                    }
                    existing_stock_quant.write(values)
                    if existing_stock_quant.id not in modified_stock_ids:
                        modified_stock_ids.append(existing_stock_quant.id)
                    continue

                new_stock_quant = {
                    'product_id': product_id,
                    'product_uom_id': uom_id,
                    'location_id': location_id,
                    'quantity': 0,
                    'inventory_quantity': actual_qty,
                    'inventory_quantity_set': True,
                    'last_count_date': datetime.now(),
                    'warehouse_id': warehouse.id,
                    'company_id': warehouse.company_id.id
                }

                if lot_name:
                    found_lots = env.lots.search([
                        ('product_id', '=', product_id),
                        ('name', '=', lot_name),
                        '|',
                        ('company_id', '=', warehouse.company_id.id),
                        ('company_id', '=', False)
                    ], limit=1)
                    if found_lots and len(found_lots) > 0:
                        existing_lot = found_lots[0]
                        new_stock_quant['lot_id'] = existing_lot.id
                    else:
                        new_lot = {
                            'product_id': product_id,
                            'name': lot_name,
                            'company_id': warehouse.company_id.id
                        }

                        # At the current moment, the use of expiration dates is not supported in the Warehouse 15.
                        # There is implementation only for one specific case - when we inventory new batches with an expiration date
                        if expiration_dates_enabled and expiration_date:
                            new_lot['expiration_date'] = expiration_date
                            new_lot['use_expiration_date'] = True

                        new_lot = env.lots.create(new_lot)
                        new_stock_quant['lot_id'] = new_lot.id

                new_stock_quant = env['stock.quant'].create(new_stock_quant)
                if new_stock_quant.id not in modified_stock_ids:
                    modified_stock_ids.append(new_stock_quant.id)

        if rewrite_all_stock:
            stock_quants = env['stock.quant'].search([
                ('id', 'not in', modified_stock_ids),
                ('location_id.active', '=', True),
                ('warehouse_id.id', '=', warehouse.id),
                ('company_id.id', '=', warehouse.company_id.id)
            ])

            for stock_quant in stock_quants:
                stock_quant.write({
                    'inventory_quantity': 0 if rewrite_counted else stock_quant.inventory_quantity,
                    'inventory_quantity_set': True,
                    'last_count_date': datetime.now()
                })

        if auto_apply_inventory_adjustment:
            for stock_quant_id in modified_stock_ids:
                stock_quant = env['stock.quant'].search([('id', '=', stock_quant_id)], limit=1)[0]
                stock_quant \
                    .with_context({f'inventory_name': self._generate_completed_inv_adj_doc_name(doc, device_info)}) \
                    .action_apply_inventory()

    # noinspection PyMethodMayBeStatic
    def _group_actual_lines(self, actual_lines: List[ClvDocLineWrapper], fill_expiration_dates: bool) -> dict[Tuple[int|None, int, int, str|None, datetime|bool], float]:
        result = {}

        if actual_lines:
            for actual_line in actual_lines:
                product_id = int(actual_line.inventory_item_id)
                uom_id = int(actual_line.unit_of_measure_id)

                location_id = None
                if actual_line.from_location_id:
                    location_id = int(actual_line.from_location_id)

                lot_name = None
                if actual_line.serial_number:
                    lot_name = actual_line.serial_number
                elif actual_line.series_name:
                    lot_name = actual_line.series_name

                expiration_date = fill_expiration_dates and actual_line.expiration_date

                group_key = (location_id, product_id, uom_id, lot_name, expiration_date)

                if group_key in result:
                    result[group_key] += actual_line.actual_quantity
                else:
                    result[group_key] = actual_line.actual_quantity

        return result

    # noinspection PyMethodMayBeStatic
    def _generate_completed_inv_adj_doc_name(self, doc: ClvDocWrapper, device_info) -> str:

        user_id = 'UNKNOWN_USER'
        device_id = 'UNKNOWN_DEVICE'

        if doc and doc.user_id:
            user_id = user_id.upper()
        elif device_info and device_info.get('userId'):
            user_id = str(device_info.get('userId')).upper()

        if doc and doc.device_id:
            device_id = doc.device_id.upper()
        elif device_info.get('deviceId'):
            device_id = str(device_info.get('deviceId')).upper()

        return f'Warehouse 15: Stock Taking by {user_id} with {device_id}'
