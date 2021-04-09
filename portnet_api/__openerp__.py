# -*- coding: utf-8 -*-
{
    "name": "Service API PORTNET",
    "author": 'TECH-IT sarl',
    "description": """
        Service API PORTNET
----------------------------------------------------------
""",

    'website': 'https://www.tech-it.ma',
    "summary": """Service API PORTNET""",
    "version": "2.3",
    "support": "contact@tech-it.ma",
    "category": "Custom",
    "depends": ["base", "portnet_subscription", "portnet_invoicing", "sale", "account_voucher", "portnet_newtarification", "product"],
    "data": [
        "views/company_view.xml",
        "views/account_voucher_payment.xml",
        "views/product_view.xml",
    ],
    "installable": True,
    "application": False,
}
