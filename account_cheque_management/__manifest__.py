# -*- coding: utf-8 -*-

{
    'name': 'Account Check Management',
    'version': '1.0',
    'summary': """Account Check Management.""",
    'description': """
    Account Cheque Management.
""",

    'author': 'Abdalrhman Ibrahim',
    'support': 'abdalrhmanibrahim55@gmail.com',
    'images': ['static/description/cheque-icon-5.png'],
    'category': 'Warehouse',
    'depends': ['account'],
    'data': [
                'security/ir.model.access.csv',
                'data/account_cheque_sequence.xml',
                'data/account_journal_data.xml',
                'wizard/return_cheque_wizard.xml',
                'views/account_cheque_view.xml',
                'views/account_payment_view.xml',
                'views/account_journal_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
