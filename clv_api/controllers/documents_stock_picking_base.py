import logging
import threading
from abc import abstractmethod
from typing import Optional

from .common_utils import CommonUtils
from .document_type_info import BusinessLocationType, DocumentTypeInfo
from .model_converter import ModelConverter
from ..utils.stock_picking_by_actual_doc_factory import StockPickingByActualDocFactory
from ..wrappers.clv_doc_line_wrapper import ClvDocLineWrapper
from ..wrappers.clv_doc_wrapper import ClvDocWrapper
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper

try:
    from ..custom.custom import after_get_document, after_get_document_descriptions
except ImportError:
    from ..custom.default import after_get_document, after_get_document_descriptions


class DocumentStockPickingImplBase:
    """
    Base class to handle stock.picking odoo documents in Inventory API processes
    """
    _model_converter = ModelConverter()
    _logger = logging.getLogger(__name__)
    _cutils = CommonUtils()

    @abstractmethod
    def get_stock_picking_filter(self, env: OdooEnvWrapper, document_type_name: str):
        """
        Returns search filter list
        @param env: Environment
        @param document_type_name: document type name
        """
        pass

    def get_descriptions(self, env: OdooEnvWrapper, document_type_name: str, offset, limit, request_count: bool):
        """
        Returns list of the document's headers
        @param env: Environment
        @param document_type_name: document's type name
        @param offset: offset in selected documents page
        @param limit: the maximum number of records in the result
        @param request_count: if need to return the total number of records in query
        @return:
        """
        filter_list = self.get_stock_picking_filter(env, document_type_name)
        documents = env['stock.picking'].search(filter_list, limit=limit, offset=offset, order='id DESC')
        result = {}
        if request_count:
            result['totalCount'] = len(env['stock.picking'].search(filter_list))
        docs = [self._model_converter.stock_picking_to_doc_description(env, doc, document_type_name) for doc in documents]
        result = {'result': after_get_document_descriptions(env, {}, docs) }
        return result

    def get_document(self, env: OdooEnvWrapper, search_mode: str, search_code: str, document_type_name: str):
        """
        Returns particular document with expected and actual lines
        @param env: Environment
        @param search_mode: how to search document
        @param search_code: the data to search document
        @param document_type_name: expected document's type name
        @return:
        """
        doc_result_container = {'document': None}
        if not search_code:
            return doc_result_container

        # Ignore document type name for now - not essential for odoo
        if search_mode.lower() == 'byCode'.lower():
            stock_picking_id = CommonUtils.decode_stock_picking_id(search_code)
            pick_docs = env['stock.picking'].search([('id', '=', stock_picking_id)])
        else:
            search_domain = self.get_stock_picking_filter(env, document_type_name)
            search_domain.append(('name', 'ilike', search_code))
            pick_docs = env['stock.picking'].search(search_domain)
        if not pick_docs or len(pick_docs) != 1:
            return doc_result_container

        pick_doc = pick_docs[0]
        doc_type = self._cutils.get_document_type_info_by_document(pick_doc)
        doc = self._model_converter.stock_picking_to_doc_description(env, pick_doc, document_type_name)
        doc['expectedLines'] = self._model_converter.stock_picking_to_expected_lines(env, pick_doc)
        ignore_zero_qty_done_actuals = doc_type.actual_lines_ignores_zero_qty_done
        if doc_type.clv_api_name == "Ship":
            ignore_zero_qty_done_actuals = not env.w15_settings.ship_expected_actual_lines
        actual_lines = self._model_converter.stock_picking_to_actual_lines(env, pick_doc, ignore_zero_qty_done_actuals)
        if actual_lines and len(actual_lines) > 0:
            doc['actualLines'] = actual_lines
        doc_result_container['document'] = after_get_document(env, {}, doc)
        return doc_result_container

    def set_document(self, env: OdooEnvWrapper, doc, device_info):
        """
        Processes finished document in odoo (validates it after modifications on the mobile device and executes validate)
        @param env:
        @param doc:
        @return:
        """
        if doc is None:
            return 200

        odoo_doc = None
        doc_wrapper = ClvDocWrapper(doc)

        if not doc_wrapper.actual_lines:
            raise RuntimeError('Document is empty. You must complete it before submitting to Odoo')

        if not doc_wrapper.created_on_device:
            stock_picking_id = CommonUtils.decode_stock_picking_id(doc_wrapper.id)
            odoo_doc = env['stock.picking'].search([('id', '=', stock_picking_id)])
            if not odoo_doc:
                raise RuntimeError('Odoo document not found')
        else:
            odoo_doc = StockPickingByActualDocFactory.create(env, doc_wrapper)

        doc_type = self._cutils.get_document_type_info_by_document(odoo_doc)

        with_locations = doc_wrapper.scan_locations

        self._logger.debug('Processing document %s, id = %s', odoo_doc.name, str(odoo_doc.id))

        not_processed = {}
        self._logger.debug('Stage 1 (edit existing lines)')
        for line in doc_wrapper.actual_lines:
            if not self._process_set_document_line(env, doc_type, odoo_doc, line,
                                                   add_to_any_line=False,
                                                   add_new_line_if_not_declared=False,
                                                   assign_new_barcodes=True,
                                                   with_locations=with_locations):
                not_processed[line.uid] = line
        self._logger.debug('Stage 1 done')

        self._logger.debug('Stage 2 (less lines need to be added)')
        for (line_uid, line) in not_processed.items():
            self._process_set_document_line(env, doc_type, odoo_doc, line,
                                            add_to_any_line=True,
                                            add_new_line_if_not_declared=True,
                                            assign_new_barcodes=False,
                                            with_locations=with_locations)
        self._logger.debug('Stage 2 done')

        need_backorder = self._get_auto_create_backorder_setting(env)
        new_ctx = odoo_doc \
            .with_context(cancel_backorder=not need_backorder) \
            .with_context(skip_backorder=True) \
            .with_context(skip_sms=True) \
            .with_context(skip_overprocessed_check=True)

        if not need_backorder:
            new_ctx = new_ctx.with_context(
                picking_ids_not_to_backorder=self._create_not_picking_backorder_lines(odoo_doc))

        if env.odoo_version <= 13:
            setattr(threading.currentThread(), 'testing', True)
        new_ctx.button_validate()
        return 200

    def _create_not_picking_backorder_lines(self, odoo_doc):
        """
        All lines not need to be back ordered
        """
        result = []
        for pick_line in odoo_doc:
            result.append(pick_line.id)
        return result

    def _log_processing_line(self, line):

        inventory_item_id_str = self._model_converter.clear_to_str(line.get('inventoryItemId'))
        if inventory_item_id_str:
            inventory_item_id_str = ' inventory item id = ' + inventory_item_id_str

        inventory_item_name_str = self._model_converter.clear_to_str(line.get('inventoryItemName'))
        if inventory_item_name_str:
            inventory_item_name_str = ' inventory item name = ' + inventory_item_name_str

        serial_number_str = self._model_converter.clear_to_str(line.get('serialNumber'))
        if serial_number_str:
            serial_number_str = ' serial = ' + serial_number_str

        series_name_str = self._model_converter.clear_to_str(line.get('seriesName'))
        if series_name_str:
            series_name_str = ' series = ' + series_name_str

        qty_str = self._model_converter.clear_to_str(line.get('actualQuantity'))
        if qty_str:
            qty_str = 'qty = ' + qty_str

        self._logger.debug('Processing line:%s',
                           inventory_item_id_str, inventory_item_name_str,
                           serial_number_str,
                           series_name_str,
                           qty_str)

    def _process_set_document_line(self,
                                   env: OdooEnvWrapper,
                                   doc_type: DocumentTypeInfo,
                                   odoo_doc,
                                   line : ClvDocLineWrapper,
                                   add_to_any_line: bool,
                                   add_new_line_if_not_declared: bool,
                                   assign_new_barcodes: bool,
                                   with_locations: bool) -> bool:
        """
        The core of the processing document line. It either modifies an existing odoo's line or
        creates new one.
        @param env: Environment
        @param doc_type: documentTypeInfo object which describes odoo doc
        @param odoo_doc: the odoo's document stock.picking object
        @param line: Inventory API line dictionary object
        @param add_to_any_line: Can we apply modifications to any found line?
        @param add_new_line_if_not_declared: Can we add new line if there is no appropriate line to modify
        @param assign_new_barcodes: Assign barcode to the odoo product if it filled in line and absent in odoo?
        @param with_locations: Apply location's filter to find appropriate odoo's document line?
        @return:
        """

        self._log_processing_line(line)

        if line.actual_quantity == 0:
            return False

        odoo_product = env['product.product'].search([('id', '=', int(line.inventory_item_id))])
        if not odoo_product:
            raise RuntimeError("Product with id='{}' not found".format(line.inventory_item_id))

        self._logger.debug('Processing product:%s', odoo_product.name)

        if assign_new_barcodes:
            self._assign_line_barcode_to_odoo_product(odoo_product, line)

        with_serial = odoo_product.product_tmpl_id.tracking == 'serial'
        if with_serial and not line.serial_number:
            if doc_type.generate_fake_serial_if_empty and env.w15_settings.scan_serials_on_allocation:
                line.serial_number = CommonUtils.create_random_fake_serial_number()
            else:
                raise RuntimeError('No serial number specified to serial tracking odoo product.')

        with_series = odoo_product.product_tmpl_id.tracking == 'lot'
        if with_series and not line.series_name:
            raise RuntimeError('No series specified to the line with series tracking')

        # Trying to find an exactly matching line

        exactly_matching_line_filter = [
            ('picking_id', '=', odoo_doc.id),
            ('product_id', '=', odoo_product.id),
            ('picked', '=', False)
        ]

        if with_serial:
            sn = line.serial_number
            exactly_matching_line_filter.append('|')
            exactly_matching_line_filter.append(('lot_name', '=', sn))
            exactly_matching_line_filter.append(('lot_id.name', '=', sn))
        elif with_series:
            lot = line.series_name
            exactly_matching_line_filter.append('|')
            exactly_matching_line_filter.append(('lot_name', '=', lot))
            exactly_matching_line_filter.append(('lot_id.name', '=', lot))

        if with_locations:
            if doc_type.main_location_type == BusinessLocationType.DEST and line.to_location_id:
                exactly_matching_line_filter.append(('location_dest_id', '=', line.to_location_id))
            elif doc_type.main_location_type == BusinessLocationType.SRC and line.from_location_id:
                exactly_matching_line_filter.append(('location_id', '=', line.from_location_id))

        found_lines = env['stock.move.line'].search(exactly_matching_line_filter)
        if found_lines and len(found_lines) == 1:
            exact_line = found_lines[0]
            if self._get_quantity_done(env, exact_line) >= self._get_product_uom_qty(env, exact_line):
                return True

        if not found_lines and (with_serial or with_series):
            # Trying to find lines with lot not specified
            lot_not_specified_line_filter = [
                ('picking_id', '=', odoo_doc.id),
                ('product_id', '=', odoo_product.id),
                ('lot_id', '=', False),
                '|',
                ('lot_name', '=', False),
                ('lot_name', '=', ''),
                ('picked', '=', False)
            ]
            found_lines = env['stock.move.line'].search(lot_not_specified_line_filter)

            # Trying to fine lines with any lot and with zero qty done to replace lot
            if not found_lines and add_to_any_line:
                any_zero_qty_line_filter = [
                    ('picking_id', '=', odoo_doc.id),
                    ('product_id', '=', odoo_product.id),
                    '|',
                    (self._get_quantity_done_name(env), '=', 0),
                    ('picked', '=', False)
                ]
                found_lines = env['stock.move.line'].search(any_zero_qty_line_filter)
        elif not found_lines:
            if self._has_valid_bound_move_line(line):
                found_lines = env['stock.move.line'].search([
                    ('picking_id', '=', odoo_doc.id),
                    ('product_id', '=', odoo_product.id),
                    ('move_id', '=', int(line.bound_document_line_uid))
                ])

            # Trying to find any containing product line
            if not found_lines and add_to_any_line:
                found_lines = env['stock.move.line'].search([
                    ('picking_id', '=', odoo_doc.id),
                    ('product_id', '=', odoo_product.id)
                ])

        self._logger.debug('Found %d possible existing lines to update', len(found_lines))

        # distribute quantity per lines
        while line.actual_quantity > 0:
            if found_lines:
                found_lines = found_lines.filtered(
                    lambda odoo_line: self._get_product_uom_qty(env, odoo_line) > self._get_quantity_done(env, odoo_line)
                )

            if found_lines and with_locations:
                location_id = False
                if doc_type.main_location_type == BusinessLocationType.DEST and line.to_location_id:
                    location_id = line.to_location_id
                elif doc_type.main_location_type == BusinessLocationType.SRC and line.from_location_id:
                    location_id = line.from_location_id

                found_lines = found_lines.filtered(
                    lambda odoo_line: self._get_odoo_line_location_id(odoo_doc, odoo_line) == location_id
                )

            if not found_lines:
                self._logger.debug('No line find to update')
                if not add_new_line_if_not_declared:
                    return False
                self._logger.debug('Adding new line to the document')
                self._add_new_move_line(env, odoo_doc, odoo_product, line)
                break

            found_line = found_lines[0]
            self._logger.debug('Updating odoo line %d', found_line.id)
            less_qty = self._get_product_uom_qty(env, found_line) - self._get_quantity_done(env, found_line)
            add_qty = min(less_qty, line.actual_quantity)
            self._logger.debug('Found exact line to update id = %d, serial = %s', found_line.id, found_line.lot_name)
            self._logger.debug('Adding quantity=%f, serial=%s, location_id=%s, location_dest_id=%s',
                               add_qty,
                               line.serial_number,
                               line.from_location_id,
                               line.to_location_id)

            updating_dict = {
                self._get_quantity_done_name(env): self._get_quantity_done(env, found_line) + add_qty,
                'picked': True,
                'company_id': odoo_doc.company_id.id
            }

            if with_serial and \
                    found_line.lot_name != line.serial_number and \
                    found_line.lot_id.name != line.serial_number:
                self._process_fake_serial_number_in_lot_storage(env, odoo_doc, found_line, line)
                self._set_lot_id_or_name_to_update_dict(updating_dict, env, line.serial_number, odoo_product.id)
            elif with_series and \
                    found_line.lot_name != line.series_name and \
                    found_line.lot_id.name != line.series_name:
                self._set_lot_id_or_name_to_update_dict(updating_dict, env, line.series_name, odoo_product.id)
            else:
                self._logger.debug('pass through odoo line lot_id = %s, lot_name = %s',
                                   self._model_converter.clear_to_str(found_line.lot_id),
                                   self._model_converter.clear_to_str(found_line.lot_name))

            if with_locations:
                self._add_line_location_to_line_update_dict(env, odoo_doc, line, updating_dict)

            found_line.write(updating_dict)
            line.actual_quantity = line.actual_quantity - add_qty

            if line.actual_quantity > 0:
                self._logger.debug('We have to add %f more quantity by this line', line.actual_quantity)

            if with_serial \
                    and line.actual_quantity > 0 \
                    and CommonUtils.is_fake_serial_number(line.serial_number):
                line.serial_number = CommonUtils.create_random_fake_serial_number()

        return True

    def _set_lot_id_or_name_to_update_dict(self, update_dict, env: OdooEnvWrapper, new_lot: str, product_id: Optional[int] = None):
        """
        Sets either existing lot_id or new new_lot name to update dict
        @param update_dict: update dictionary or the odoo line
        @param env: Environment
        @param new_lot: new lot name (series or serial number)
        @return:
        """
        domain_filter = [('name', '=', new_lot)]
        if product_id:
            domain_filter.append(('product_id', '=', product_id))
        if update_dict.get('company_id'):
            domain_filter.extend(['|', ('company_id', '=', update_dict.get('company_id')), ('company_id', '=', False)])
        found_lot = env.lots.search(domain_filter)
        if found_lot:
            update_dict['lot_id'] = found_lot[0].id
            update_dict['lot_name'] = None
            self._logger.debug('line setted existing lot = %s with id = %s', new_lot, str(found_lot[0].id))
        else:
            lot = env.lots.create({
                'product_id': product_id,
                'name': new_lot,
                'company_id': update_dict.get('company_id') or False
            })
            update_dict['lot_id'] = lot.id
            update_dict['lot_name'] = None
            self._logger.debug('line creating new lot = %s', new_lot)

    def _process_fake_serial_number_in_lot_storage(self, env: OdooEnvWrapper, odoo_doc, odoo_line, line: ClvDocLineWrapper):
        """
        Processes case when current odoo_line contains fake serial number.
        It replaces lots and serial table storage.
        Returns True if proceeded
        @param env: Environment
        @param odoo_doc: odoo document
        @param odoo_line: odoo line
        @param line: Inventory API line (dictionary)
        @return:
        """

        doc_type = self._cutils.get_document_type_info_by_document(odoo_doc)
        if not doc_type.can_overwrite_fake_serial_numbers:
            return

        new_serial = line.serial_number
        if not new_serial or not odoo_line.lot_id or not CommonUtils.is_fake_serial_number(odoo_line.lot_id.name):
            return

        self._logger.debug('fake serial number ' + str(odoo_line.lot_id.name) + ' updating to ' + new_serial)
        odoo_line.lot_id.update({'name': new_serial})

    def _get_auto_create_backorder_setting(self, env: OdooEnvWrapper) -> bool:
        """
        True if need create backorder setting
        @param env: Environment
        @return:
        """
        return not env.w15_settings.auto_create_backorders

    def _add_line_location_to_line_update_dict(self, env: OdooEnvWrapper, odoo_doc, line: ClvDocLineWrapper, update_dict):
        """
        Adds location id to update dictionary
        @param env: Environment
        @param odoo_doc: odoo document
        @param line: Inventory API line
        @param update_dict: odoo's line update dictionary
        @return:
        """
        doc_type = self._cutils.get_document_type_info_by_document(odoo_doc)
        line_storage_id = False
        if doc_type.main_location_type == BusinessLocationType.DEST and line.to_location_id:
            line_storage_id = line.to_location_id
        elif doc_type.main_location_type == BusinessLocationType.SRC and line.from_location_id:
            line_storage_id = line.from_location_id

        if not line_storage_id:
            return

        line_location = env['stock.location'].search([('id', '=', int(line_storage_id))])
        if not line_location:
            return
        line_location = line_location[0]

        doc_location = self._cutils.get_doc_main_location(odoo_doc)

        # Verify if line's first storage id corresponds to the document location

        if not line_location.parent_path.startswith(doc_location.parent_path):
            raise RuntimeError('Document location=%s does not contain line location=%s',
                               doc_location.parent_path, line_location.parent_path)

        if doc_type.main_location_type == BusinessLocationType.DEST:
            update_dict['location_dest_id'] = line_location.id
        else:
            update_dict['location_id'] = line_location.id

    def _get_odoo_line_location_id(self, odoo_doc, odoo_line):
        """
        Returns expected ood's line location id (depends on the document type).
        @param odoo_doc: odoo document
        @param odoo_line: odoo's line
        @return:
        """
        doc_type = self._cutils.get_document_type_info_by_document(odoo_doc)
        if doc_type.main_location_type == BusinessLocationType.DEST:
            return odoo_line.location_dest_id.id
        else:
            return odoo_line.location_id.id

    def _assign_line_barcode_to_odoo_product(self, odoo_product, line: ClvDocLineWrapper):
        """
        Assignes barcode to the odoo's product if it is not assigned yet.
        @param odoo_product: odoo product object
        @param line: Inventory API line
        @return:
        """
        barcode = line.barcode
        if not barcode:
            return
        if odoo_product.barcode:
            if odoo_product.barcode != barcode:
                raise RuntimeError('Can not assign new barcode value to the product.')
            return
        odoo_product.write({'barcode': barcode})

    def _add_new_move_line(self, env: OdooEnvWrapper, odoo_doc, odoo_product, line: ClvDocLineWrapper):
        """
        Creates and ads new stock.move.line to the odoo stock.picking document
        @param env: Environment
        @param odoo_doc: odoo document
        @param odoo_product: odoo product corresponds to adding line
        @param line: Inventory API line object
        @return:
        """
        new_item = {
            'picking_id': odoo_doc.id,
            'product_id': odoo_product.id,
            'product_uom_id': odoo_product.uom_id.id,
            'location_id': odoo_doc.location_id.id,
            'location_dest_id': odoo_doc.location_dest_id.id,
            'picked': True,
            self._get_quantity_done_name(env): line.actual_quantity,
            'company_id': odoo_doc.company_id.id
        }
        if self._has_valid_bound_move_line(line):
            new_item['move_id'] = int(line.bound_document_line_uid)
        if odoo_product.product_tmpl_id.tracking == 'serial' and line.serial_number:
            self._set_lot_id_or_name_to_update_dict(new_item, env, line.serial_number, odoo_product.id)
        elif odoo_product.product_tmpl_id.tracking == 'lot' and line.series_name:
            self._set_lot_id_or_name_to_update_dict(new_item, env, line.series_name, odoo_product.id)
        self._add_line_location_to_line_update_dict(env, odoo_doc, line, new_item)
        odoo_doc.move_line_ids_without_package.create(new_item)

    def _has_valid_bound_move_line(self, line: ClvDocLineWrapper) -> bool:
        """
        Does line contains valid bound line uid value
        @param line: Inventory API line
        @return:
        """
        return line.bound_document_line_uid.isdigit()

    def _trunc_list_length(self, list, length: int):
        """
        Local routing to truncate list
        @param list:
        @param length:
        @return:
        """
        while len(list) > length:
            list.pop()

    def _get_quantity_done(self, env: OdooEnvWrapper, odoo_line):
        if env.odoo_version >= 17:
            if odoo_line.picked:
                return odoo_line.quantity
            return 0
        return odoo_line.qty_done

    def _get_quantity_done_name(self, env: OdooEnvWrapper):
        if env.odoo_version >= 17:
            return 'quantity'
        return 'qty_done'

    def _get_product_uom_qty(self, env: OdooEnvWrapper, odoo_line):
        """
        Returns valid reserved (expected) odoo line quantity
        @param odoo_line: odoo document line stock.move.line
        @return:
        """
        if env.odoo_version >= 17:
            return odoo_line.quantity_product_uom
        if env.odoo_version >= 16:
            return odoo_line.reserved_uom_qty
        else:
            return odoo_line.product_uom_qty

    def _get_product_uom_qty_name(self, env: OdooEnvWrapper):
        """
        Returns the name of the odoo document line reserved (expected) field
        @return:
        """
        if env.odoo_version >= 17:
            return 'quantity_product_uom'
        if env.odoo_version >= 16:
            return 'reserved_uom_qty'
        else:
            return 'product_uom_qty'
