from .documents_stock_picking_base import DocumentStockPickingImplBase
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class DocumentShipImpl(DocumentStockPickingImplBase):

    def get_stock_picking_filter(self, env: OdooEnvWrapper, document_type_name: str):
        return [('state', '=', 'assigned'),
                ('picking_type_id.sequence_code', '=', 'OUT')]
