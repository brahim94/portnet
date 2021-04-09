# -*- coding: utf-8 -*-

{
    'name': 'PORTNET SUBSCRIPTION',
    'version': '1.0',
    'author': 'GTD AFRICA',
    'summary': 'SUBSCRIPTION PORTNET',
    'description': """ Ce module permet la gestion du souscription des clients dans la plateforme PORTNET """,
    'website': '',
    'depends': ['base','account','portnet_invoicing','sale'],
    'category': 'Autre',
    'demo': [],
    'data': [
        'views/partner_view.xml',
        'views/setting_gu_view.xml',
        'cron/crons.xml',
    ],
    'application':True,
    'installable':True,
}
