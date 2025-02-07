# -*- coding: utf-8 -*-
# from odoo import http


# class KbiProduct(http.Controller):
#     @http.route('/kbi_product/kbi_product', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kbi_product/kbi_product/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('kbi_product.listing', {
#             'root': '/kbi_product/kbi_product',
#             'objects': http.request.env['kbi_product.kbi_product'].search([]),
#         })

#     @http.route('/kbi_product/kbi_product/objects/<model("kbi_product.kbi_product"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kbi_product.object', {
#             'object': obj
#         })

