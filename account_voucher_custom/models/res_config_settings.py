# -*- coding: utf-8 -*-
##############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    double_approval_amount = fields.Float(related='company_id.double_approval_amount',string='Double Approval Amount')

