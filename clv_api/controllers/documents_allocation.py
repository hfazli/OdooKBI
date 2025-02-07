from .documents_stock_picking_base import DocumentStockPickingImplBase
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class DocumentAllocationImpl(DocumentStockPickingImplBase):
    """
    Overrides to process Allocation documents
    """

    def get_stock_picking_filter(self, env: OdooEnvWrapper, document_type_name: str):
        domain = [('state', '=', 'assigned')]
        if env.odoo_version >= 18:
            domain.extend([('picking_type_id.sequence_code', '=', 'STOR')])
        else:
            domain.extend([('picking_type_id.sequence_code', '=', 'INT')])
        # filter only input source locations
        domain.extend([('location_id.name', '=', 'Input')])

        return domain
