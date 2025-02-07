from .documents_stock_picking_base import DocumentStockPickingImplBase
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class DocumentPickAndShipImpl(DocumentStockPickingImplBase):
    """
    @deprecated Overrides to process PickAndShip documents
    """

    def get_stock_picking_filter(self, env: OdooEnvWrapper, document_type_name: str):
        return [('picking_type_id.code', '=', 'outgoing'), ('state', '=', 'assigned')]
