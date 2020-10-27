# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.exceptions import ValidationError


class AccountCheque(models.Model):
    _name = 'account.cheque'
    _description = 'Account Cheque Management'

    STATES = [('new', 'New'),
              ('under_collection', "Under Collection"),
              ('out_standing', "Out Standing"),
              ('in_bank', "In Bank"),
              ('in_drawable', "In Drawable"),
              ('return_acc', "Return To Account"),
              ('return_acv', "Return To Account"),
              ('done', 'Done')]

    name = fields.Char(string="Name", default=_("New"))
    date = fields.Date(string="Date", default=fields.Date.today)
    holder_id = fields.Many2one('res.partner', string="Holder")
    beneficiary_id = fields.Many2one('res.partner', string="Beneficiary")
    journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one('res.company', string="Company")
    cheque_line_ids = fields.One2many("account.cheque.line", "cheque_id", readonly=1)
    amount = fields.Float(string="Amount")
    bank_id = fields.Many2one('res.bank', string="Bank")
    currency_id = fields.Many2one('res.currency', string="Currency")
    memo = fields.Char(string="Communication")
    payment_id = fields.Many2one('account.payment', string="Payment")
    cheque_number = fields.Char("Cheque Number", readonly=1)
    cheque_type = fields.Selection([('inbound', 'Inbound'), ('outbound', "Outbound")], readonly=1)
    state = fields.Selection(STATES, default="new", readonly=1)
    return_reason = fields.Char(string="Return Reason", readonly=True)

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('account.cheque.seq')
        vals.update({
            'name': name,
            'cheque_line_ids': [(0, 0, {'note': "Cheque Created By [%s]" % self.env.user.name,
                                        'datetime': datetime.now(),
                                        'cheque_id': self.env.context.get('id')})]
        })
        return super(AccountCheque, self).create(vals)

    @api.multi
    def action_cheque_under_collection(self):
        for rec in self:
            under_collection_account_id = self.journal_id.under_collection_account_id
            partner_id = self.holder_id
            if not under_collection_account_id:
                raise ValidationError("Please check under collection account.")
            if not partner_id.property_account_receivable_id:
                raise ValidationError("Please check partner receivable account.")
            note = "STATE >> From New to Under Collection >> By User [%s]" % self.env.user.name
            move_id = self.payment_id.move_line_ids and self.payment_id.move_line_ids[0].move_id
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'under_collection'

    @api.multi
    def action_cheque_in_bank(self):
        for rec in self:
            rec.check_cheque_date(rec.date)
            under_collection_account_id = rec.journal_id.under_collection_account_id
            bank_account_id = rec.journal_id.default_debit_account_id
            note = "STATE >> From Under Collection To in Bank >> By User [%s]" % self.env.user.name
            partner_id = rec.holder_id
            move_vals = {
                'ref': rec.name,
                'journal_id': rec.journal_id.id,
                'date': datetime.now(),
                'line_ids': [
                    (0, 0, {
                        'account_id': bank_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': rec.amount,
                        'credit': 0.0}),
                    (0, 0, {
                        'account_id': under_collection_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': 0.0,
                        'credit': rec.amount})
                ]
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.sudo().post()
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'in_bank'

    @api.multi
    def action_cheque_customer_return(self):
        for rec in self:
            customer_return_account_id = rec.journal_id.customer_return_account_id
            bank_account_id = rec.journal_id.default_debit_account_id
            note = "STATE >> From In Bank To Return To Account >> By User [%s]" % self.env.user.name
            partner_id = rec.holder_id
            if not customer_return_account_id:
                raise ValidationError("Please check customer return account.")
            move_vals = {
                'ref': rec.name,
                'journal_id': rec.journal_id.id,
                'date': datetime.now(),
                'line_ids': [
                    (0, 0, {
                        'account_id': customer_return_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': rec.amount,
                        'credit': 0.0}),
                    (0, 0, {
                        'account_id': bank_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': 0.0,
                        'credit': rec.amount})
                ]
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.sudo().post()
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'return_acc'

    @api.multi
    def action_cheque_outstanding(self):
        for rec in self:
            outstanding_account_id = self.journal_id.outstanding_account_id
            partner_id = rec.holder_id
            if not outstanding_account_id:
                raise ValidationError("Please check Outstanding account.")
            if not partner_id.property_account_payable_id:
                raise ValidationError("Please check partner payable account.")
            note = "STATE >> From New to Outstanding >> By User [%s]" % self.env.user.name
            move_id = rec.payment_id.move_line_ids and rec.payment_id.move_line_ids[0].move_id
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'out_standing'

    @api.multi
    def action_cheque_in_drawable(self):
        for rec in self:
            rec.check_cheque_date(rec.date)
            outstanding_account_id = rec.journal_id.outstanding_account_id
            bank_account_id = rec.journal_id.default_credit_account_id
            note = "STATE >> From Out Standing To in Drawable >> By User [%s]" % rec.env.user.name
            partner_id = rec.holder_id
            move_vals = {
                'ref': rec.name,
                'journal_id': rec.journal_id.id,
                'date': datetime.now(),
                'line_ids': [
                    (0, 0, {
                        'account_id': outstanding_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': rec.amount,
                        'credit': 0.0}),
                    (0, 0, {
                        'account_id': bank_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': 0.0,
                        'credit': rec.amount})
                ]
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.sudo().post()
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'in_drawable'

    @api.multi
    def action_cheque_vendor_return(self):
        for rec in self:
            vendor_return_account_id = rec.journal_id.vendor_return_account_id
            bank_account_id = rec.journal_id.default_credit_account_id
            note = "STATE >> From In Bank To Return To Account >> By User [%s]" % self.env.user.name
            partner_id = rec.holder_id
            if not vendor_return_account_id:
                raise ValidationError("Please check vendor return account.")
            move_vals = {
                'ref': rec.name,
                'journal_id': rec.journal_id.id,
                'date': datetime.now(),
                'line_ids': [
                    (0, 0, {
                        'account_id': vendor_return_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': rec.amount,
                        'credit': 0.0}),
                    (0, 0, {
                        'account_id': bank_account_id.id,
                        'name': rec.name + '[' + note + ']',
                        'partner_id': partner_id.id,
                        'debit': 0.0,
                        'credit': rec.amount})
                ]
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.sudo().post()
            rec.create_cheque_line(rec, move_id, note)
            rec.state = 'return_acv'

    def create_cheque_line(self, cheque, move_id, note):
        line_values = {
            'cheque_id': cheque.id,
            'datetime': datetime.now(),
            'note': note,
            'move_id': move_id.id
        }
        line_id = self.env['account.cheque.line'].create(line_values)

    @api.multi
    def check_cheque_date(self, cheque_date):
        if cheque_date > str(datetime.now().date()):
            raise ValidationError(_("The check date has not yet come .! \n Check Date %s" % cheque_date))

    @api.multi
    def action_open_return_wizard(self):
        for rec in self:
            action = self.env.ref('account_cheque_management.return_cheque_wizard_action').read()[0]
            ctx = self.env.context.copy()
            ctx.update({
                'default_cheque_id': rec.id,
                'default_datetime': datetime.now()
            })
            action['context'] = ctx
            return action

    @api.multi
    def action_cheque_done(self):
        for rec in self:
            note = "Cheque Done by %s" % self.env.user.name
            line_values = {
                'cheque_id': self.id,
                'datetime': datetime.now(),
                'note': note,
            }
            self.env['account.cheque.line'].create(line_values)
            rec.state = 'done'


class AccountChequeLine(models.Model):
    _name = 'account.cheque.line'
    _description = 'Account Cheque Line'
    _order = 'datetime'

    move_id = fields.Many2one('account.move', string="Account Move")
    datetime = fields.Datetime(string="Date")
    cheque_id = fields.Many2one('account.cheque', string="Cheque")
    note = fields.Text(string="Note")
