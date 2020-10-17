# -*- coding: utf-8 -*
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import time
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime


class account_register_paymentsCustom(models.TransientModel):
    _inherit = 'account.register.payments'

    note=fields.Char('Deposit Bank') 
    check_number_custom= fields.Char('Check Number')
    postponement_date= fields.Date('Date of postponement', required=False ,states={'done':[('readonly',True)]}, copy=False)
    postponement=fields.Boolean(string="postponement")
    date_now = fields.Date(string='Data now ', default=datetime.today() ,invisible=True)
    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        ''' 
        amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication, # DO NOT FORWARD PORT TO V12 OR ABOVE
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'check_number_custom':self.check_number_custom,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'postponement_date':self.postponement_date,
            'postponement':self.postponement,
            'date_now':self.date_now,
            'note':self.note,
         }
 



class account_payments(models.Model):
    _inherit = 'account.payment'
    
    # sales_man_id = fields.Many2one('hr.employee', string="Sales Man")
    payment_checked = fields.Boolean(string="Payment Checked", readonly=True, help="Field is defines is this payment calculated for the sales man or not")
    check_number_custom= fields.Char('Check Number' ,copy=False)
    postponement=fields.Boolean(string="postponement")
    note=fields.Char('Deposit Bank')
    postponement_date= fields.Date('Date of postponement', required=False ,states={'done':[('readonly',True)]}, copy=False)
    date_now = fields.Date(string='Data now ', default=datetime.today() ,invisible=True)

# class AccountRegisterPaymentsCustom_Inh(models.TransientModel):
#     _inherit = "account.register.payments"

#     check_number_custom= fields.Char('Check Number')

    



