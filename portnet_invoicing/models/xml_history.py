# -*- encoding: utf-8 -*-
from openerp import models, fields,  api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
import time
class xml_history(models.Model):
    _name = 'xml.history'

    _order ="date desc"

    date=fields.Datetime(string="Date dépot facture")
    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Facture")
    invoice_number = fields.Char(string="Numéro de facture")
    invoice_state = fields.Char(string="Statut de la facture")
    customer_code = fields.Char(string="Code client")
    customer_name = fields.Char(string="Nom client")
    note = fields.Char(string="Note")
    filename = fields.Char(string="Nom du fichier")
    messageref = fields.Char(string="Code message facture")
    transaction_id = fields.Char(string="Paiement/Id.Trans")
    acc_date = fields.Char(string="Date accusée de réception")
    last_payment_load_date = fields.Char(string="Derniére date d'intégration paiement")
    first_payment_load_date = fields.Char(string="Premiére date d'intégration paiement")
    type = fields.Selection([('invoice_deposit','Depôt facture'),('inv_integration_ok',"Intégration facture OK"),('inv_integration_nok',"Intégration facture NOK"),('payment_integration_ok',"Intégration paiement OK"),('payment_integration_nok',"Intégration paiement NOK")],string="Type")


xml_history()