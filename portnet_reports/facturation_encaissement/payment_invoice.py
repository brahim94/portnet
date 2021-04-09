# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################


from openerp import models, fields, api, _, exceptions,tools



class payment_invoice_reporting(models.Model):
    _name = "payment.invoice.reporting"

    code_partner = fields.Char(string='Code Client')
    code_pres = fields.Char(string='Code Préstation')
    design_pres = fields.Char(string='Designation Préstation')
    num_invoice = fields.Char(string='Numéro Facture')
    amount_untaxed = fields.Float(string='Montant HT')
    amount_total = fields.Float(string='Montant TTC')
    amount_tax = fields.Float(string='Montant TVA')
    quantity = fields.Float(string='Quantité')
    price_unit = fields.Float(string='Tarif')
    partner_name = fields.Char(string='Nom Client')
    date_invoice = fields.Date(string='Date Emission')
    ref_reglement = fields.Char(string='Référence réglement')
    name_reglement = fields.Char(string='Nom réglement')
    debit = fields.Float(string='Débit')
    credit = fields.Float(string='Encaissé TTC')
    balance = fields.Float(string='Solde TTC')
    date_payment = fields.Date(string='Date Paiement')
    period_id = fields.Many2one(comodel_name="account.period", string="Période")
    method_id = fields.Many2one(comodel_name="account.invoice.tva.reglement", string="Méthode de paiement")
    reconcile_type = fields.Selection(string="Type Encaiss", selection=[('none', 'Aucun'), ('partial', 'Partiel'),('total','Total') ], required=False, )

    @api.one
    def unlink(self):
        raise exceptions.ValidationError(_('Suppression non autorisée !'))



payment_invoice_reporting()

