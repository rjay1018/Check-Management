# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cheque_no = fields.Char("Cheque Number")
    bank_id = fields.Many2one("res.bank", "Bank")
    cheque_date = fields.Date("Cheque Date")
    account_no = fields.Char("Account Number")

    def _get_liquidity_move_line_vals(self, amount):
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)
        if self.payment_type == 'inbound' and self.payment_method_code == 'cheque':
            # compute debit account
            res['account_id'] = self.journal_id.under_collection_account_id.id
        if self.payment_type == 'outbound' and self.payment_method_code == 'cheque':
            res['account_id'] = self.journal_id.outstanding_account_id.id
        return res

    @api.onchange('partner_id', 'payment_method_code', 'bank_id')
    def onchange_partner(self):
        if self.payment_method_code == 'cheque':
            if self.partner_id:
                partner_bank_id = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
                if partner_bank_id:
                    self.bank_id = partner_bank_id.bank_id
                    self.account_no = partner_bank_id.acc_number
            self.cheque_no = self.get_cheque_number()
        else:
            self.bank_id = False
            self.account_no = False

    def get_cheque_number(self):
        cheque_no = self.journal_id.cheque_number + 1
        return cheque_no

    def check_cheque_number(self, cheque_number):
        cheque_id = self.env['account.cheque'].search([('cheque_number', '=', cheque_number)])
        if cheque_id:
            raise ValidationError("You can not duplicated Cheque Number [%s]" % cheque_id.cheque_number)
        else:
            pass

    @api.multi
    def post(self):
        for rec in self:
            res = super(AccountPayment, self).post()
            if rec.payment_method_code == 'cheque':
                rec.check_cheque_number(rec.cheque_no)
                cheque_id = rec.create_payment_cheque()
                if self.payment_type == 'inbound':
                    cheque_id.action_cheque_under_collection()
                if self.payment_type == 'outbound':
                    cheque_id.action_cheque_outstanding()
                self.journal_id.cheque_number = self.cheque_no
            return res

    def create_payment_cheque(self):
        cheque_obj = self.env['account.cheque']
        cheque_values = self._prepare_cheque_values()
        cheque_id = cheque_obj.create(cheque_values)
        return cheque_id

    @api.model
    def _prepare_cheque_values(self):
        holder_id, beneficiary_id = self.get_beneficiary_and_holder()
        cheque_values = {
            'date': self.cheque_date,
            'holder_id': holder_id and holder_id.id or False,
            'beneficiary_id': beneficiary_id and beneficiary_id.id or False,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'amount': self.amount,
            'bank_id': self.bank_id.id,
            'currency_id': self.currency_id.id,
            'memo': self.communication,
            'payment_id': self.id,
            'cheque_number': self.cheque_no,
            'cheque_type': self.payment_type,
        }
        return cheque_values

    def get_beneficiary_and_holder(self):
        holder_id = False
        beneficiary_id = False
        if self.payment_type == 'outbound':
            holder_id = self.company_id.partner_id
            beneficiary_id = self.partner_id
        if self.payment_type == 'inbound':
            beneficiary_id = self.company_id.partner_id
            holder_id = self.partner_id
        return holder_id, beneficiary_id
