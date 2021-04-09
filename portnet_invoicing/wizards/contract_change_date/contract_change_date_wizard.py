# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os
from dateutil import parser
from dateutil.relativedelta import relativedelta

class contract_change_date_wizard(models.TransientModel):
    _name = 'contract.change.date.wizard'

    @api.multi
    def action_change(self):
        contracts = self.env['res.contract'].search([('id','in',self._context['active_ids'])])
        for ctr in contracts:
            if ctr.next_invoice_date >= '2016-05-01' and ctr.next_invoice_date <= '2016-06-30':
                print ctr.id
                ctr.next_invoice_date = parser.parse(ctr.next_invoice_date) + relativedelta(months=ctr.periodicity_id.nb_months)
        return True

contract_change_date_wizard()