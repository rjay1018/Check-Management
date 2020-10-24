# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"

    cheque_number = fields.Integer(string="Cheque Number")
    under_collection_account_id = fields.Many2one('account.account', string="Under Collection Account")
    outstanding_account_id = fields.Many2one('account.account', string="Outstanding Account")
    customer_return_account_id = fields.Many2one('account.account', string="Customer Return Account")
    vendor_return_account_id = fields.Many2one('account.account', string="Vendor Return Account")
    is_customer_cheque = fields.Boolean(string="Is Customer Cheque", compute="compute_payment_method_type")
    is_vendor_cheque = fields.Boolean(string="Is Vendor Cheque", compute="compute_payment_method_type")

    @api.depends('inbound_payment_method_ids', 'outbound_payment_method_ids')
    def compute_payment_method_type(self):
        for rec in self:
            cheque_in_payment_method_id = self.env.ref('account_cheque_management.account_payment_method_cheque_in')
            cheque_out_payment_method_id = self.env.ref('account_cheque_management.account_payment_method_cheque_out')
            for method in rec.inbound_payment_method_ids:
                if method.id == cheque_in_payment_method_id.id:
                    rec.is_customer_cheque = True
            for method in rec.outbound_payment_method_ids:
                if method.id == cheque_out_payment_method_id.id:
                    rec.is_vendor_cheque = True
