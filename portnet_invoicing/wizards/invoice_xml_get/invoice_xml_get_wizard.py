# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os

class invoice_xml_get_wizard(models.TransientModel):
    _name = 'invoice.xml.get.wizard'

    def _default_nb_invoices(self):
        if 'active_ids' in self._context:
            return len(self._context.get('active_ids'))
        else:
            return 0

    nb_invoices = fields.Integer(string="Nombre de factures à traiter", required=False, default=_default_nb_invoices)
    # création facture manuelle ==> création xml manuel action_get
    @api.multi
    def action_get(self):
        invoices = self.env['account.invoice'].search([('id','in',self._context['active_ids'])])
        for inv in invoices:
            if inv.state in ['open','paid','cancel']:
                action = {'open':9,'paid':2 ,'cancel':3}
                inv._gen_xml_file(action[inv.state])
            else:
                raise exceptions.ValidationError("La facture doît être ouverte, payée ou annulée")
        return True

invoice_xml_get_wizard()