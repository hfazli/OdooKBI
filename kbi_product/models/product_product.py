# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    default_code = fields.Char('Part Number', index=True)

    type = fields.Selection(
    string="Product Type",
    help="FG (Finished Goods) are tangible materials and merchandise you provide.\n"
         "WIP (Work in Progress) represents items still in production process.\n"
         "PKG (Package) represents combination of multiple items.",
    selection=[
        ('consu', "FG"),
        ('service', "WIP"),
        ('combo', "Combo"),
    ],
    required=True,
    default='consu',
)