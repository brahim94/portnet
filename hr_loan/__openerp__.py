# -*- coding: utf-8 -*-
{   'name': "l10n_ma_hr_loan",
    'version' : '1.1',
    'author' : 'Kazacube',
    'category' : 'Loan',
    'website': "http://www.kazacube.com",
    'version': '1.0',
    'description' : """

    """,
    'depends': ['base','paie'],

    # always loaded
    'data': [

        'security/hr_expense_expense_security.xml',
        'security/ir.model.access.csv',
        'hr_loan.xml',
	'hr_expense.xml',
	'hr_contract.xml',
    ],

    # only loaded in demonstration mode
    'demo': [
       # 'demo.xml',
    ],
}
