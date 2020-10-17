# -*- coding: utf-8 -*-
   

from odoo import models, fields, api, _
from odoo.addons.account_check_printing_custom.models import amount_to_text_ar
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime





class AccountRegisterPaymentsCustom(models.TransientModel):
    _inherit = "account.register.payments"

    
    check_number = fields.Integer(string="Check Number", readonly=False, copy=False, default=0,
        help="Number of the check corresponding to this payment. If your pre-printed check are not already numbered, "
             "you can manage the numbering in the journal configuration page.")
    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the paymen_t values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        return super(AccountRegisterPaymentsCustom, self)._prepare_payment_vals()
        amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'check_number':self.check_number,
        }
  

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.one
    @api.depends('outbound_payment_method_ids')
    def _compute_transfer_payment_method_selected(self):
        self.transfer_payment_method_selected = any(
            pm.code == 'transfer' for pm in self.outbound_payment_method_ids)

    check_dimension = fields.Many2one(
        'account.check.dimension', 'Check dimension')
    transfer_sequence_id = fields.Many2one(
        'ir.sequence', 'Transfer Sequence', copy=False, help="Transfer numbering sequence.")
    transfer_payment_method_selected = fields.Boolean(compute='_compute_transfer_payment_method_selected',
                                                      help="Technical feature used to know whether transfer was enabled as payment method.")


class CheckLog(models.Model):
    """
    This class for storing some data for each printed check as a 
    summary log display check info and it's state.
    """
    _name = 'check.log'
    _description = 'Check Log'

    # TODO
    signed = fields.Boolean(String='Signed')
    name = fields.Many2one(
        'account.payment', String='Payment Amount', ondelete='cascade')
    # TODO
    reason = fields.Selection([('void', 'Void'), ('loss', 'Loss'), (
        'cancelation', 'Cancelation'), ('unk', 'Unknown')], String="Reason")
    check_no = fields.Char('Check Number', size=128)
    journal_id = fields.Many2one(
        'account.journal', String='Bank', readonly=True)
    date_due = fields.Date(related='name.payment_date',
                           String='Due Date', store=True)
    partner_id = fields.Many2one(
        related='name.partner_id', String='Beneficiary', store=True, readonly=True)
    amount = fields.Monetary(
        related='name.amount',string="Amount", store=True, readonly=True)
    
    currency_id = fields.Many2one('res.currency',
        related='name.currency_id',string="Currency", store=True, readonly=True)
    
    company_id = fields.Many2one(
        related='name.company_id', String='Company', store=True, readonly=True)
    status = fields.Selection([('active', 'Active'), ('canceled',
                                                      'Canceled'), ('deleted', 'Deleted')], String="Check Status")
    release_at = fields.Char('Release At', size=54, Translate=True)
    description = fields.Char('Description', size=128, Translate=True)

    @api.multi
    @api.constrains('journal_id', 'check_no')
    def _check_no(self):
        """
        Constrain method to prohibit system from duplicating check no for the same 
        bank account / journal.

        @return: Boolean True or False
        """
        for log in self:
            checks = self.search([('journal_id', '=', log.journal_id.id),
                                  ('check_no', '=', log.check_no), ('status', '!=', 'deleted')])
            if len(checks) > 1:
                raise ValidationError(
                    _('This check no.(%s) is already exist!') % log.check_no)

    @api.model
    def notify_user(self, *args, **kwargs):
        if self.env.user.company_id.check_validity:
            validity_months = -1 * self.env.user.company_id.check_validity

            past_start = datetime.today() + relativedelta(months=validity_months)
            past_end = past_start + relativedelta(days=7)

            past_start = str(past_start.date())
            past_end = str(past_end.date())

            recs = self.search([('status', '=', 'active'), ('date_due',
                                                            '<=', past_end), ('date_due', '>=', past_start), ])

            IrModelData = self.env['ir.model.data']
            channel_check_log = IrModelData.xmlid_to_object(
                'account_check_printing_custom.channel_check_log')
            template_check_log = IrModelData.xmlid_to_object(
                'account_check_printing_custom.email_template_data_check_validity')
            if template_check_log:
                for rec in recs:
                    MailTemplate = self.env['mail.template']
                    body_html = MailTemplate.render_template(
                        template_check_log.body_html, 'check.log', rec.id)
                    subject = MailTemplate.render_template(
                        template_check_log.subject, 'check.log', rec.id)

                    channel_check_log.message_post(
                        body=body_html, subject=subject,
                        subtype='mail.mt_comment')

        return True


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    transfer_number = fields.Integer(
        string="Transfer Number", readonly=True, copy=False)
    release_at = fields.Char('Release At', size=54, Translate=True)
    description = fields.Char('Description', size=128, Translate=True)
    check_number = fields.Integer(string="Check Number", readonly=True, copy=False,
        help="Number of the check corresponding to this payment. If your pre-printed check are not already numbered, "
             "you can manage the numbering in the journal configuration page.")

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id and self.journal_id.check_dimension:
            self.release_at = self.journal_id.check_dimension.release_at_text
            self.description = self.journal_id.check_dimension.description_text
        return super(AccountPayment, self)._onchange_journal()

    @api.onchange('amount')
    def _onchange_amount(self):
        context = self._context or {}
        if hasattr(super(AccountPayment, self), '_onchange_amount'):
            super(AccountPayment, self)._onchange_amount()
        if context.get('lang') == 'ar_SY':
            units_name = self.currency_id.currency_unit_label
            cents_name = self.currency_id.currency_subunit_label
            self.check_amount_in_words = amount_to_text_ar.amount_to_text(
                self.amount, 'ar', units_name, cents_name)

    @api.one
    def create_check_log(self, new_check_no, release_at):
        """ Create a check.log """
        context = self._context or {}
        cr = self._cr or False
        uid = self._uid or False
        ids = self._ids or []
        self.env['check.log'].create({
            'name': self.id,
            'status': 'active',
            'check_no': new_check_no,
            'journal_id': self.journal_id.id,
            'release_at': release_at,
            'description': self.description,
        })

    @api.multi
    def do_print_checks(self):
        if self.journal_id.check_dimension.id != False:
            res = {
                'payment_date': self.payment_date,
                'partner_name': self.partner_id.name,
                'check_amount_in_words': self.check_amount_in_words,
                'amount_money': self.amount,
                'release_at_name': self._context.get('release_at', False) or self.release_at,
                'description_name': self.description,
                'beneficiary': self.journal_id.check_dimension.beneficiary,
                'font_size': self.journal_id.check_dimension.font_size,
                'date': self.journal_id.check_dimension.date,
                'amount': self.journal_id.check_dimension.amount,
                'number': self.journal_id.check_dimension.number,
                'release_at': self.journal_id.check_dimension.release_at,
                'description': self.journal_id.check_dimension.description,
            }
            datas = {
                'ids': self._ids,
                'model': 'account.payment',
                'form': res,
            }
            self.write({'release_at': res['release_at_name']})
            dic = self.env.ref(
                'account_check_printing_custom.print_check_qweb_report').report_action(self, data=datas)
            return dic
        else:
            raise UserError(
                _("Please add check dimensions to the selected journal in order to print a check."))

    @api.multi
    def print_checks(self):
        """ 
        Inherit to call wiz.print.check
        """
        self = self.filtered(lambda r: r.payment_method_id.code ==
                             'check_printing' and r.state != 'reconciled')
        if len(self) == 0:
            raise UserError(_("Payments to print as a checks must have 'Check' selected as payment method and "
                              "not have already been reconciled"))
        if any(payment.journal_id != self[0].journal_id for payment in self):
            raise UserError(
                _("In order to print multiple checks at once, they must belong to the same bank journal."))
        if not self[0].journal_id.check_manual_sequencing:
            is_printed = False
            if self.check_number != 0:
                is_printed = True
            last_printed_check = self.search([
                ('journal_id', '=', self[0].journal_id.id),
                ('check_number', '!=', 0)], order="check_number desc", limit=1)
            next_check_number = last_printed_check and last_printed_check.check_number
            if not is_printed:
                next_check_number = last_printed_check and last_printed_check.check_number + 1 or 1
            return {
                'name': _('Print Check Report'),
                'type': 'ir.actions.act_window',
                'res_model': 'wiz.print.check',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': self.ids,
                    'default_next_check_number': next_check_number,
                    'default_preprinted': is_printed,
                }
            }
        else:
            return self.do_print_checks()

    @api.multi
    def print_transfer_report(self):
        datas = {}
        [data] = self.read()
        data['payment_ids'] = self.ids
        datas = {
            'ids': self._ids,
            'model': 'account.payment',
            'form': data
        }
        last_printed_transfer = self.search([
            ('journal_id', '=', self[0].journal_id.id),
            ('transfer_number', '!=', 0),
            ('payment_method_code', '=', 'transfer')], order="transfer_number desc", limit=1)
        next_transfer_number = last_printed_transfer and last_printed_transfer.transfer_number + 1 or 1
        self.write({'state': 'sent', 'transfer_number': next_transfer_number})
        return self.env.ref('account_check_printing_custom.bank_transfer_report_action').report_action(self, data=datas)

    def splite_amount_total(self, amount):
        """
        This method split the amount number into tow parts, before decimal point and after
        @return: list of string with tow parts
        """
        split_num = str(amount).split('.')
        return split_num


class account_check_dimension(models.Model):

    _name = 'account.check.dimension'

    name = fields.Char('Name', size=54, required=True, Translate=True)
    font_size = fields.Integer(
        'Font Size', size=54, required=True, Translate=True)
    date = fields.Char('Date', size=54, required=True, Translate=True)
    beneficiary = fields.Char('Beneficiary', size=54,
                              required=True, Translate=True)
    amount = fields.Char('Written Amount', size=54,
                         required=True, Translate=True)
    number = fields.Char('Amount', size=54, required=True, Translate=True)
    release_at = fields.Char('Release At', default="0,0",size=54,
                             required=False, Translate=True)
    description = fields.Char('Description', size=128,
                              required=True, Translate=True)
    release_at_text = fields.Char('Release At', size=54, Translate=True)
    description_text = fields.Char('Description', size=128, Translate=True)
    active = fields.Boolean(
        default=True, help="Set active to false to hide the check dimension without removing it.")
    preview = fields.Html('Report Preview', sanitize=False, strip_style=False, readonly=1)
    # we add this field to ovecome onchange problem with readonly fields(preview)
    html_text = fields.Text()

    @api.model
    def create(self, vals):
        if 'html_text' in vals:
            vals['preview'] = vals['html_text']
        res = super(account_check_dimension, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'html_text' in vals:
            vals['preview'] = vals['html_text']
        res = super(account_check_dimension, self).write(vals)
        return res

    def check_dimension_values(self, value):
        # if value is empty or value not x,y then default value 20,20 else x and y
        if value == False or len(value.split(',', 1)) != 2:
            return ['20','20']
        else:
            # if value is 'x,y' then splited_value is ['x','y']
            splited_value = value.split(',', 1)
            return splited_value

    @api.onchange('font_size', 'date', 'beneficiary', 'amount', 'number', 'release_at', 'description')
    def print_preview(self):
        dimension_values = {'date': str(self.date),
                            'beneficiary': str(self.beneficiary),
                            'amount': str(self.amount),
                            'number': str(self.number),
                            'release_at': str(self.release_at),
                            'description': str(self.description)}

        # using mapping to split string values from (x,y) form to ['x','y'] form to use x and y more easy
        splited_dimension_values = dict(map(lambda key_val: (
            key_val[0], self.check_dimension_values(key_val[1])), dimension_values.items()))
        font_size = self.font_size or 0

        html = """
                <body>
                    <html>

                        <center>
                            <h2>
                                عرض نموذج الشيك
                            </h2>
                        </center>
                        <br/>
                        <br/>
                        <hr/>
                        <svg dir="ltr"  height="1000" width="1000" style="font-size: %spx;">
                            <text x="%s" y="%s">
                                       المستفيد
                            </text>
                            <text x="%s" y="%s">
                                      المبلغ المكتوب
                            </text>
                            <text x="%s" y="%s">
                                       الوصف
                            </text>
                            <text x="%s" y="%s">
                                        الملبغ
                            </text>
                            <text x="%s" y="%s">
                                        التاريخ
                            </text>
                            <!--text x="%s" y="%s">
                                        حرر في
                            </text-->
                        </svg>

                    </html>
                </body>
                """ % (str(font_size),
              splited_dimension_values['beneficiary'][0],
              splited_dimension_values['beneficiary'][1],
              splited_dimension_values['amount'][0],
              splited_dimension_values['amount'][1],
              splited_dimension_values['description'][0],
              splited_dimension_values['description'][1],
              splited_dimension_values['number'][0],
              splited_dimension_values['number'][1],
              splited_dimension_values['date'][0],
              splited_dimension_values['date'][1],
              splited_dimension_values['release_at'][0],
              splited_dimension_values['release_at'][1])
        #uncomment the following lines if you want to show real report ^_^
        #datas=  {'ids': (9,), 'model': 'account.payment', 'form': {'partner_name': 'مدثر أحمد عمر', 'release_at': '840,840', 'date': '801,800', 'release_at_name': '1', 'description': '850,850', 'payment_date': '2018-11-27', 'font_size': 14, 'description_name': False, 'beneficiary': '810,810', 'number': '830,830', 'amount': '820,820', 'amount_money': 1000000.0, 'check_amount_in_words': 'Three Hundred And Thirty-Three Riyal'}}
        #html =  self.env.ref('account_check_printing_custom.print_check_qweb_report').render_qweb_html(self, data=datas,)[0]
        self.preview = html
        self.html_text = html
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
