# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import datetime
import os
from dateutil import parser
from dateutil.relativedelta import relativedelta

class contract_renewal_wizard(models.TransientModel):
    _name = 'contract.renewal.wizard'

    @api.multi
    def action_renewal(self):
        today = datetime.now().date()
        contracts = self.env['res.contract'].search([('id','in',self._context['active_ids'])])
        for ctr in contracts:
            #MAJ anticipated date
            months_in_advance = ctr.partner_id.categ_id.invoicing_advance_in_months
            if months_in_advance > 0:
                anticipated_invoice_date = parser.parse(ctr.next_invoice_date).date() - relativedelta(months=months_in_advance)
                if anticipated_invoice_date != ctr.anticipated_invoice_date:
                    ctr.anticipated_invoice_date = anticipated_invoice_date
            else:
                ctr.anticipated_invoice_date = ctr.next_invoice_date
            #MAJ anticipated date

            #Invoice creation + dates update
            ctr.write({'next_invoice_date':parser.parse(ctr.next_invoice_date) + relativedelta(months=ctr.periodicity_id.nb_months),
                     'anticipated_invoice_date':parser.parse(ctr.anticipated_invoice_date) + relativedelta(months=ctr.periodicity_id.nb_months)})
            ctr.action_create_invoice(str(today))
            #Invoice creation + dates update
        return True

contract_renewal_wizard()