# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import os

class move_treasury_update_wizard(models.TransientModel):
    _name = 'move.treasury.update.wizard'

    @api.multi
    def action_update(self):
        moves = self.env['account.move'].browse(self._context['active_ids'])
        for move in moves:
            move.action_update_maturity_dates()
        return True

move_treasury_update_wizard()