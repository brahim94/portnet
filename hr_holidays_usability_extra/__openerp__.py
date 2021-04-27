# -*- coding: utf-8 -*-
{
    'name': "hr_holidays_usability_extra",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_holidays_usability'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_holidays.xml',
        'views/hr_holidays_status.xml',
        'templates.xml',
        'cron/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
