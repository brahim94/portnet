from openerp import models, fields, api, _, exceptionsi

class account_invoice_ext(models.Model):
    _inherit = 'account.invoice'

    transport_order = fields.Char('Ordre de transport')

    # def print_portnet_ext(self):
    #     return self.env.ref('portnet_report_extend.report_invoice_porntet_extend').report_action(self)
