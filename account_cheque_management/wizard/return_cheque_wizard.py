# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import AccessError, UserError, ValidationError


class ReturnChequeWizard(models.TransientModel):
    _name = 'return.cheque.wizard'
    _description = 'Return Cheque Wizard'

    cheque_id = fields.Many2one('account.cheque', string="Cheque")
    datetime = fields.Datetime(string="Datetime")
    reason = fields.Text(string="Return Reason")

    @api.multi
    def action_cheque_return(self):
        self.check_cheque_date(self.cheque_id.date)
        if self.cheque_id.cheque_type == 'inbound':
            self.cheque_id.action_cheque_customer_return()
        if self.cheque_id.cheque_type == 'outbound':
            self.cheque_id.action_cheque_vendor_return()
        self.cheque_id.sudo().write({'return_reason': self.reason})

    @api.multi
    def check_cheque_date(self, cheque_date):
        if self.datetime < cheque_date or self.datetime > str(datetime.now()):
            raise ValidationError(_("The return date can not be less than cheque date and grater than today.!"
                                    " \n Check Date %s" % cheque_date))
