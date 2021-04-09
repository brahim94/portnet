# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_invoice_extend(models.Model):

    _inherit = 'account.invoice'

    def print_portnet_extend(self):
        return self.env.ref('portnet_report_extend.report_invoice_porntet_extend').report_action(self)
