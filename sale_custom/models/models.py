# -*- coding: utf-8 -*-

import time
import math
from odoo import fields, models, api, exceptions, _
import re
from odoo.exceptions import ValidationError, AccessError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import base64
from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from num2words import num2words
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class sale_order_custom(models.Model):
	"""docstring for sale_order_custom"""
	_inherit="sale.order"
	_order = " id desc"


	 

 

	state = fields.Selection(selection_add=[('confirm_stock', 'Confirm Stock')])
 
 


	

 


	@api.multi
	def _action_confirm(self):
		super(sale_order_custom, self)._action_confirm()
		for order in self:
			order.order_line._action_launch_procurement_rule()

	# connfirm sale order immediate 
	@api.multi
	def action_confirm_custom(self):
		imediate_obj=self.env['stock.immediate.transfer']
		res=super(sale_order_custom,self).action_confirm()
		for order in self:

			warehouse=order.warehouse_id
			if warehouse :
 
				for picking in self.picking_ids:
					picking.button_validate()
					#picking.action_assign()
					imediate_rec=imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
					imediate_rec.process()
			self.write({'state':'confirm_stock'})
			self._cr.commit()
			
			
		return res



	def action_cancel(self):
		invoices = self.mapped('invoice_ids').filtered(
			lambda x: x.state  in ['draft'])
		if  invoices:
			invoices.action_invoice_cancel()
		return super(sale_order_custom, self).action_cancel()


	
