# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os
from amount_to_text_kzc import amount_to_text_fr

class invoice_update_wizard(models.TransientModel):
    _name = 'invoice.update.wizard'

    all_invoices = fields.Boolean(string="Toutes les factures")

    @api.multi
    def action_update(self):
        if self.all_invoices:
            invoices  = self.pool.get('account.invoice').search_read(self._cr, 1, [('state', '!=', 'draft')], ['id'])
        else:
            invoices  = self.pool.get('account.invoice').search_read(self._cr, 1, [('state', '!=', 'draft'),('id','in',self._context['active_ids'])], ['id'])
        for inv in invoices:
            invoice = self.env['account.invoice'].browse(inv['id'])
            invoice.amount_letter = amount_to_text_fr(invoice.amount_total,invoice.currency_id.report_currency)
        return True

invoice_update_wizard()