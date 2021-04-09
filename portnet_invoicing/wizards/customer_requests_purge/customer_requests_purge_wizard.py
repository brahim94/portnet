# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os
import parser

class customer_requests_purge_wizard(models.TransientModel):
    _name = 'customer.requests.purge.wizard'

    date_start = fields.Datetime(string="Du")
    date_stop = fields.Datetime(string="Au")

    @api.multi
    def action_validate(self):
        c_reqs = self.env['customer.request'].search([('state','=','confirmed'),('create_date','>=',self.date_start),('create_date','<=',self.date_stop)])
        if c_reqs:
            c_reqs.unlink()
        return True

customer_requests_purge_wizard()