# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime

class contract_validation_wizard(models.TransientModel):
    _name = 'contract.validation.wizard'

    contract_id = fields.Many2one(comodel_name="res.contract", string="Demande de création client", required=False)
    choice = fields.Selection(string="Facturation", selection=[('create', 'Créer une facture'), ('no_create', 'Ne pas créer de facture'), ], required=False, default='no_create')
    date = fields.Date(string="Date", required=False, default=fields.Date().today())
    next_seq = fields.Boolean(string="Incrémenter la séquence")

    @api.multi
    def action_confirm(self):
        if self.next_seq:
            self.contract_id.name = self.env['ir.sequence'].get('res.contract.seq')
        if self.choice == 'create':
            self.contract_id.action_create_invoice(self.date)
        self.contract_id.state = 'pending'



contract_validation_wizard()