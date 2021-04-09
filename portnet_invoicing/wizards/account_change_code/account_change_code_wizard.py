# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os

class account_change_code_wizard(models.TransientModel):
    _name = 'account.change.code.wizard'

    @api.multi
    def action_change(self):
        accounts = self.env['account.account'].search([('id','in',self._context['active_ids'])])
        for acc in accounts:
            acc.code = acc.code+'00'
        return True

account_change_code_wizard()