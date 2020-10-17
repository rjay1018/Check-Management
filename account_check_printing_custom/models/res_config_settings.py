# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class ResConfigSettings(models.Model):
    _inherit = 'res.company'

    check_validity = fields.Integer(string='Number of months (check validity)',default=6)

   

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_validity = fields.Integer(related='company_id.check_validity')


