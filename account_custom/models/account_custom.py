# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang
from odoo import api , fields,exceptions, tools, models,_
from odoo.exceptions import ValidationError

class AccountAccountType(models.Model):
	_inherit = "account.account.type"

	active = fields.Boolean(default=True, help="Set active to false to hide the Account Type without removing it.")
 
class AccountAccountInherit(models.Model):
	_inherit="account.account"



	
class account_journal_dashboard_custom(models.Model):
	_inherit = "account.journal"

	@api.multi
	def get_line_graph_datas(self):
		data = []
		today = datetime.today()
		last_month = today + timedelta(days=-30)
		bank_stmt = []
		# Query to optimize loading of data for bank statement graphs
		# Return a list containing the latest bank statement balance per day for the
		# last 30 days for current journal
		query = """SELECT a.date, a.balance_end
						FROM account_bank_statement AS a,
							(SELECT c.date, max(c.id) AS stmt_id
								FROM account_bank_statement AS c
								WHERE c.journal_id = %s
									AND c.date > %s
									AND c.date <= %s
									GROUP BY date) AS b
						WHERE a.id = b.stmt_id
						ORDER BY date;"""

		self.env.cr.execute(query, (self.id, last_month, today))
		bank_stmt = self.env.cr.dictfetchall()

		last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids),('date', '<=', last_month.strftime(DF))], order="date desc, id desc", limit=1)
		start_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0

		locale = self._context.get('lang') or 'en_US'
		if locale == "ar_SY":
		
			locale = "ar"

		show_date = last_month
		#get date in locale format
		name = format_date(show_date, 'd LLLL Y', locale=locale)
		short_name = format_date(show_date, 'd MMM', locale=locale)
		data.append({'x':short_name,'y':start_balance, 'name':name})

		for stmt in bank_stmt:
			#fill the gap between last data and the new one
			number_day_to_add = (datetime.strptime(stmt.get('date'), DF) - show_date).days
			last_balance = data[len(data) - 1]['y']
			for day in range(0,number_day_to_add + 1):
				show_date = show_date + timedelta(days=1)
				#get date in locale format
				name = format_date(show_date, 'd LLLL Y', locale=locale)
				short_name = format_date(show_date, 'd MMM', locale=locale)
				data.append({'x': short_name, 'y':last_balance, 'name': name})
			#add new stmt value
			data[len(data) - 1]['y'] = stmt.get('balance_end')

		#continue the graph if the last statement isn't today
		if show_date != today:
			number_day_to_add = (today - show_date).days
			last_balance = data[len(data) - 1]['y']
			for day in range(0,number_day_to_add):
				show_date = show_date + timedelta(days=1)
				#get date in locale format
				name = format_date(show_date, 'd LLLL Y', locale=locale)
				short_name = format_date(show_date, 'd MMM', locale=locale)
				data.append({'x': short_name, 'y':last_balance, 'name': name})

		[graph_title, graph_key] = self._graph_title_and_key()
		color = '#3c33ff' if '+e' in version else '#3c33ff'
		return [{'values': data, 'title': graph_title, 'key': graph_key, 'area': True, 'color': color}]
 


	
class account_payment(models.Model):
	_inherit = "account.payment"

	check_status=fields.Boolean(default=False, help="Set True when check was paid ")


class account_account_custom(models.Model):
	_inherit = "account.account"
	_order = 'code'
