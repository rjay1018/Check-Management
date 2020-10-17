# -*- coding: utf-8 -*-


{
    'name' : 'Check Printing Custom',
    'version' : 'Maknoun',
    'author' : 'NCTR',
    'website': 'http://www.nctr.sd',
    'description' : """account check printing custom""",
    'depends' : ['account_check_printing'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'wizard/account_check_print_wizard_view.xml',
        'views/account_check_printing_report.xml',
        'views/print_check_view.xml',
        'views/bank_transfer_report.xml',
        'views/res_config_settings_views.xml',
        'data/notify_users_scheduler.xml',
        #'report/check_log_report.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
