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
    'name': 'PORTNET REPORTS',
    'version': '1.1',
    'author': 'KAZACUBE',
    'summary': 'RAPPORTS PORTNET',
    'description': """
        Ce module permet de rajouter rapports spécifiques à PORTNET""",

    'website': 'https://www.kazacube.com',

    'depends': ['base','account','portnet_invoicing','kzc_tools','pentaho_reports','account_cutoff_prepaid','portnet_treasury','account_financial_report_webkit_xls'],

    'category': 'Reporting',
    'demo': [],
    'data': [
             "security/ir.model.access.csv",
             "root_menu.xml",
             # "balance_aged/account_move_line_view.xml",
             "balance_aged/wizard/aged_partner_balance_wizard.xml",
             "facture/layouts.xml",
             "facture/invoice_portnet.xml",
             "details_facture/invoice_details.xml",
             "facturation_encaissement/payment_invoice.xml",
             "facturation_encaissement/wizard/fact_encaiss_wizard_view.xml",
             "etat_pca/account_cutoff.xml",
             "indicateurs_financier/financial_indicator.xml",
             "indicateurs_performance_financier/financial_performance_indicator.xml",
             "situation_mentuelle_tresorerie/monthly_monitoring_treasury.xml",
             "situation_mentuelle_tresorerie/wizard/monthly_treasury_wizard_view.xml",
             "indicateurs_tri_suivi_budget/quarterly_indicators_monitoring_budget.xml",
             "indicateurs_tri_suivi_budget/wizard/budget_tri_suivi_wizard_view.xml",
             "situation_tresorerie/treasury_situation.xml",
             "situation_budget/budget_situation.xml",
             "etat_synthese_facturation/billing_synthesis_state.xml",
             "bon_commande_achat/purchaseorder_portnet.xml",
             "bon_commande_achat/purchasequotation_portnet.xml",
             "configure_table_xls/config_table_xls.xml",
             "indicateur_activite_commerciale/indicateur_activite_commerciale.xml",
             "trial_balance/trial_balance.xml",
             "partners_balance/partners_balance_wizard_view.xml"
             ],

    'application':True,
    'installable':True,
}
