# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PurchaseLineWizard(models.TransientModel):
    _name = "purchase.request.line.wizard"
    _description = "Purchase Line Wizard"

    etat = fields.Selection([('qualifie', 'Qualifié'), ('Annulé', 'Annulé')], string="State", required=True)
    traitement = fields.Selection([('Appel d’offres', 'Appel d’offres'), ('Contrat / Convention', 'Contrat / Convention'), ('Consultation / BC', 'Consultation / BC'), ('Régie', 'Régie')], string="Mode de traitement")
    line_ids = fields.Many2many('purchase.request.line', 'rel_purchase_request', 'purchase_line_id', 'request_line_id', string="Purchase Request Line")
    besoin_type = fields.Selection([('Prévisionnel', 'Prévisionnel'),('Non planifié', 'Non planifié')], string="Type de besoin")
    programme_previsionnel = fields.Many2one("purchase.previsionnel", string="Programme prévisionnel")

    @api.model
    def default_get(self, fields):
        res = super(PurchaseLineWizard, self).default_get(fields)
        active_ids = self._context.get('active_ids', [])
        purchase_req_line = self.env['purchase.request.line'].search([('id', 'in', active_ids)])
        if any(purchase_req_line.filtered(lambda l: l.request_state != 'to_approve')):
            raise UserError(
                _("You can only process validated purchase request lines.")
            )
        res['line_ids'] =  purchase_req_line.ids if purchase_req_line else []
        return res

    def action_update_purchase_line(self):
        for record in self:
            for line in record.line_ids:
                line.write({
                    'etat': record.etat,
                    'traitement': record.traitement,
                    'besoin_type': record.besoin_type if record.besoin_type else False,
                    'programme_previsionnel': record.programme_previsionnel.id if record.besoin_type else False,
                    })
            for req in set(record.line_ids.mapped('request_id')):
                if not any(req.line_ids.filtered(lambda x: x.etat == False)):
                    req.state = 'approved'
                    req.qualifier_id = self.env.user.id
                elif len(req.line_ids.filtered(lambda x: x.etat == 'Annulé')) == len(req.line_ids):
                    req.line_ids.write({'cancelled': True})
                    req.state = 'cancelled'

    @api.onchange('besoin_type')
    def onchange_besoin_type(self):
        if self.besoin_type != 'Prévisionnel':
            self.programme_previsionnel = ''
