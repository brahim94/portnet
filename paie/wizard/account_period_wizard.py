# -*- encoding: utf-8 -*-
from datetime import datetime
from openerp import fields, models, api


class account_period_wizard(models.Model):
    _name = "account.period.wizard"

    def get_default_period(self):
        today = datetime.today().date()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        periods = self.env['account.period'].search([['name','=',period]])
        return periods or False
    periode = fields.Many2one('account.period','Période',default=get_default_period )
    state_paie = fields.Boolean(related='periode.state_paie',string='Période fermée',store=True)

    @api.multi
    def ouvrir(self):
        self.state_paie=False
        return {'ir.actions.act_window_close'}

    @api.multi
    def fermer(self):
        self.state_paie=True
        return {'ir.actions.act_window_close'}

