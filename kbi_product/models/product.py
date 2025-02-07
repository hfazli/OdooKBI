from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection([
        ('consu', 'Goods'),
        ('service', 'WIP'),
        ('product', 'FG'),
    ], string='Product Type', default='consu')