# -*- coding: utf-8 -*-
from odoo import http

# class AccountCustom(http.Controller):
#     @http.route('/account_custom/account_custom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_custom/account_custom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_custom.listing', {
#             'root': '/account_custom/account_custom',
#             'objects': http.request.env['account_custom.account_custom'].search([]),
#         })

#     @http.route('/account_custom/account_custom/objects/<model("account_custom.account_custom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_custom.object', {
#             'object': obj
#         })