# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    default_code = fields.Char(
        'Part Number', compute='_compute_default_code',
        inverse='_set_default_code', store=True)

    type = fields.Selection(
        string="Product Type",
        help="FG (Finished Goods) adalah barang jadi.\n"
             "WIP (Work in Progress) adalah barang dalam proses.\n"
             "PKG adalah paket gabungan produk.",
        selection=[
            ('consu', "FG"),      # Mengubah "Goods" menjadi "FG"
            ('service', "WIP"),    # Mengubah "Service" menjadi "WIP"
            ('combo', "PKG"),      # Mengubah "Combo" menjadi "PKG"
        ],
        required=True,
        default='consu',
    )

    @api.depends('product_variant_ids.default_code')
    def _compute_default_code(self):
        self._compute_template_field_from_variant_field('default_code')

    def _set_default_code(self):
        self._set_product_variant_field('default_code')

    @api.depends('product_variant_ids.type')
    def _compute_type(self):
        self._compute_template_field_from_variant_field('type')
    
    def _set_type(self):
        self._set_product_variant_field('type')