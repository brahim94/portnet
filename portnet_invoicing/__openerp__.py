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
    'name': 'PORTNET INVOICING',
    'version': '1.0',
    'author': 'KAZACUBE',
    'summary': 'Facturation PORTNET',
    'description': """
        Ce module permet de rajouter des fonctionnalités spécifiques au processus de facturation PORTNET
----------------------------------------------------------
""",

    'website': 'https://www.kazacube.com',
    'depends': ['base_setup','account','account_cutoff_prepaid','stock','tva_ma','portnet_move_store','mail'],
    'category': 'Autre',
    'demo': [],
    'data': [
             "security/groups.xml",
             "security/ir.model.access.csv",
             "views/customer_request_view.xml",
             "views/contract_view.xml",
             "views/partner_view.xml",
             "views/periodicity_view.xml",
             "views/invoice_view.xml",
             "views/partner_group_view.xml",
             "views/operation_type_view.xml",
             "views/exception_view.xml",
             "views/xml_history_view.xml",
             "views/settings_view.xml",
             "views/product_view.xml",
             "views/picking_view.xml",
             "views/account_view.xml",
             "views/sale_view.xml",
             "views/subscription_reason_view.xml",
             "views/invoicing_operation_view.xml",
             "wizards/customer_request/customer_request_wizard_view.xml",
             "wizards/customer_subscription/customer_subscription_wizard_view.xml",
             "wizards/customer_invoicing/customer_invoicing_wizard_view.xml",
	         "wizards/customer_refund/account_invoice_refund_view.xml",
             "wizards/invoice_xml_get/invoice_xml_get_wizard_view.xml",
             "wizards/supplier_penalty_fees/supplier_penalty_fees_wizard_view.xml",
             "wizards/customer_penalty_fees/customer_penalty_fees_wizard_view.xml",
             "wizards/contract_validation/contract_validation_wizard_view.xml",
             "wizards/customer_requests_purge/customer_requests_purge_wizard_view.xml",
             #'wizards/account_change_code/account_change_code_wizard_view.xml',
             #'wizards/contract_change_date/contract_change_date_wizard_view.xml',
             'wizards/contract_renewal/contract_renewal_wizard_view.xml',
             "wizards/move_treasury_update/move_treasury_update_wizard_view.xml",
             "wizards/invoice_update/invoice_update_wizard_view.xml",
             "wizards/partner_update/partner_update_wizard_view.xml",
             "wizards/customer_requests_removal/customer_requests_removal_wizard_view.xml",
             "wizards/auto_reconciliation/auto_reconciliation_wizard_view.xml",
             "wizards/invoices_in_folder/invoice_in_folder_wizard_view.xml",
             "wizards/operation_invoice_validation/operation_invoice_validation_wizard_view.xml",
             "wizards/manual_contract_invoice/manual_contract_invoice_wizard_view.xml",
             "sequence/contract_seq.xml",
             "sequence/xml_invoice_message_seq.xml",
             "sequence/xml_exchange_seq.xml",
             "templates/mail_notif_templates.xml",
             "cron/crons.xml",
             ],


    'application':True,
    'installable':True,
}
