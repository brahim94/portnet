# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'PORTNET PAYMENT',
    'version': '1.1',
    'author': 'KAZACUBE',
    'summary': 'PAYMENT PORTNET',
    'description': """
        Ce module permet d'ajouter de champs dans le paiement à PORTNET""",

    'website': 'https://www.kazacube.com',

    'depends': ['base','account','portnet_invoicing','positional_file','bank_reconcile'],

    'category': 'accounting',
    'demo': [],
    'data': [
             "security/ir.model.access.csv",
             "views/account_voucher_view.xml",
             "views/account_move_line_view.xml",
             "views/account_journal_view.xml",
             "views/settings_view.xml",
             "views/unprocessed_jplus2_view.xml",
             "views/bank_view.xml",
             "cron/crons.xml",
             "sequence/xml_payment_message_seq.xml",
             "reports/reports.xml",

            ],

    'application':True,
    'installable':True,
 }
