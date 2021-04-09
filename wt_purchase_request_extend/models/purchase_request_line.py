# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_STATES = [
    ("draft", "Draft"),
    ("to_be_approve", "Approve"),
    ("to_approve", "Validated"),
    ("approved", "Qualified"),
    ("done", "Closed"),
    ("rejected", "Refusé"),
    ("cancelled", "Annulé")
]


class PurchaseRequestLinet(models.Model):
    _inherit = 'purchase.request.line'

    etat = fields.Selection([('qualifie', 'Qualifié'), ('Annulé', 'Annulé'), ('Affecté', 'Affecté')], string="State", readonly=True)
    is_achat = fields.Boolean(string="Achat Regie souhaite?")
    traitement = fields.Selection([('Appel d’offres', 'Appel d’offres'), ('Contrat / Convention', 'Contrat / Convention'), ('Consultation / BC', 'Consultation / BC'), ('Régie', 'Régie')], string="Mode de traitement")
    prod_categ_id = fields.Many2one('product.category', string="Family")
    prod_child_categ_id = fields.Many2one('product.category', string="Sub Family")
    prod_demand_qty = fields.Float(string="Quantity requested", default=1.00)
    filename = fields.Char(string="Filename")
    attachment_id = fields.Binary(type="binary", string="Attachement")
    financement_type = fields.Selection([('CHB', 'CHB'),('Sur Budget', 'Sur Budget')], related='request_id.financement_type', string="Type de Financement")   
    besoin_type = fields.Selection([('Prévisionnel', 'Prévisionnel'),('Non planifié', 'Non planifié')], string="Type de besoin")
    programme_previsionnel = fields.Many2one("purchase.previsionnel", string="Programme prévisionnel")
    request_state = fields.Selection(
        string="Request state",
        related="request_id.state",
        selection=_STATES,
        store=True,
    )


    @api.onchange('prod_demand_qty')
    def onchange_prod_demand_qty(self):
        self.product_qty = self.prod_demand_qty

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.product_qty > self.prod_demand_qty:
            raise UserError(
                _("You cannot enter  Quantité accordée more than  Quantité demandée.")
            )

    @api.onchange('besoin_type')
    def onchange_besoin_type(self):
        if self.besoin_type != 'Prévisionnel':
            self.programme_previsionnel = ''
