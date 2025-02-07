from typing import List

from ..controllers.common_utils import CommonUtils
from ..wrappers.clv_doc_line_wrapper import ClvDocLineWrapper
from ..wrappers.clv_doc_wrapper import ClvDocWrapper
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class StockPickingByActualDocFactory:

    @classmethod
    def create(cls, env: OdooEnvWrapper, clv_doc: ClvDocWrapper) -> object:
        """
        Creates a new 'stock.picking' in Odoo based on Cleverence document created on the mobile device.
        """

        warehouse_id = clv_doc.warehouse_id
        if not warehouse_id:
            raise RuntimeError('Warehouse is not specified')

        partner_id = int(clv_doc.customer_vendor_id)
        if not partner_id:
            raise RuntimeError('Partner is not specified')

        warehouse_id = CommonUtils.convert_warehouse_id_from_clv_to_odoo(warehouse_id)
        warehouse = env.warehouses.search([('id', '=', warehouse_id)], limit=1)

        if not warehouse:
            raise RuntimeError("Warehouse with id='{}' does not exist or is archived".format(warehouse_id))

        partner = env.partners.search([('id', '=', partner_id)], limit=1)
        if not partner:
            raise RuntimeError("Partner with id='{}' does not exist, is archived or is blacklisted".format(partner_id))

        operation_code = False
        doc_type_name = clv_doc.document_type_name.lower()
        if doc_type_name == 'receiving':
            if warehouse.reception_steps != 'one_step':
                raise RuntimeError('Creating documents on the mobile device is supported only for one-step receiving process')
            operation_code = 'incoming'
        elif doc_type_name == 'ship':
            if warehouse.delivery_steps != 'ship_only':
                raise RuntimeError('Creating documents on the mobile device is supported only for one-step shipping process')
            operation_code = 'outgoing'
        else:
            raise RuntimeError(
                f'Creating documents on the mobile device is not supported for \'{doc_type_name}\' document type')

        picking_types = env['stock.picking.type'].search([
            ('active', '=', True),
            ('warehouse_id', '=', warehouse_id),
            ('code', '=', operation_code)])

        if not picking_types:
            raise RuntimeError('Operation type for this document not found')

        # Temporally we select the first one,
        # but actually we need to select between several picking types.
        picking_type = picking_types[0]

        stock_picking = env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': partner.id,
            'origin': cls._generate_origin_for_stock_picking(clv_doc),
            'company_id': warehouse.company_id.id
        })

        grouped_actual_quantities = cls._group_actual_quantities(clv_doc.actual_lines)

        for group_key, quantity in grouped_actual_quantities.items():
            new_stock_move = {
                'picking_id': stock_picking.id,
                'product_id': group_key[0],
                'product_uom': group_key[1],
                cls._get_planned_qty_name(env): quantity,
                'location_id': stock_picking.location_id.id,
                'location_dest_id': stock_picking.location_dest_id.id,
                'name': cls._generate_stock_move_name(clv_doc),
                'company_id': stock_picking.company_id.id
            }

            if env.odoo_version >= 17:
                new_stock_move['picked'] = False

            stock_picking.move_ids_without_package.create(new_stock_move)

        stock_picking.action_assign()

        return stock_picking

    @classmethod
    def _group_actual_quantities(cls, actual_lines: List[ClvDocLineWrapper]) -> dict:
        result = {}
        for actual_line in actual_lines:
            product_id = int(actual_line.inventory_item_id)
            uom_id = int(actual_line.unit_of_measure_id)
            actual_qty = actual_line.actual_quantity

            key = (product_id, uom_id)
            if key in result:
                result[key] += actual_qty
            else:
                result[key] = actual_qty

        return result

    @classmethod
    def _generate_origin_for_stock_picking(cls, clv_doc: ClvDocWrapper) -> str:
        doc_name = (clv_doc.name or 'UNKNOWN_DOC').upper()
        user_id = (clv_doc.user_id or 'UNKNOWN_USER').upper()
        device_id = (clv_doc.device_id or 'UNKNOWN_DEVICE').upper()

        return f'{doc_name} by {user_id} with {device_id}'

    @classmethod
    def _generate_stock_move_name(cls, clv_doc: ClvDocWrapper) -> str:
        user_id = (clv_doc.user_id or 'UNKNOWN_USER').upper()
        device_id = (clv_doc.device_id or 'UNKNOWN_DEVICE').upper()

        return f'Stock move by {user_id} with {device_id}'

    @classmethod
    def _get_planned_qty_name(cls, env: OdooEnvWrapper):
        if env.odoo_version >= 17:
            return 'product_uom_qty'

        return 'product_uom_qty'
