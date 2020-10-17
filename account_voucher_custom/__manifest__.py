# -*- coding: utf-8 -*-
##############################################################################
#
#    NCTR, Nile Center for Technology Research
#    Copyright (C) 2011-2012 NCTR (<http://www.nctr.sd>).
#
##############################################################################

{
    "name": "Voucher Custom",
    "version": "Maknoun",
    "category": "Accounting & Finance",
    "description": """
Connecting Accounting Voucher with budget confirmations
=======================================================
each voucher line with analytic account must approved from managerial accounting department before
closing & creating journal entry for voucher.""",
    "author": "NCTR",
    "website": "http://www.nctr.sd",
    "depends": ["account_voucher"],
    "data": [
        "wizard/voucher_reject_reason_wizard.xml",
        "views/voucher_reject_reason_template.xml",
        "views/views.xml",
        "views/account_voucher_view.xml",
        "views/res_config_settings_views.xml",
        "security/ir.model.access.csv",
        "sequence/sequence.xml",
        ],
    "installable": True,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
