# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    purchase_request_line_ids = fields.Many2many('purchase.request.line', 'rel_purchase_requisition_line', 'request_line_id', 'requisition_line_id',  string="Purchase Request Line")