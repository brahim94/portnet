# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os

class operation_invoice_validation_wizard(models.TransientModel):
    _name = 'operation.invoice.validation.wizard'

    @api.multi
    def action_validate(self):
        invoices = self.env['account.invoice'].search([('id','in',self._context['active_ids']),('op_id','!=',False),('state','=','draft')])
        for inv in invoices:
            inv.validate_operation_invoice()

operation_invoice_validation_wizard()