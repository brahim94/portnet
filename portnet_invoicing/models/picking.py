# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    project_break_ids = fields.One2many(comodel_name="project.break", inverse_name="picking_id", string="Arrêt-Service", required=False, )
    requisition_id=fields.Many2one('purchase.requisition',string='Demande d\'achat')

stock_picking()



