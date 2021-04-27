# -*- coding: utf-8 -*-
from openerp import fields, models, api
from datetime import datetime
import time

class hr_expense_expense(models.Model):
    _inherit = 'hr.expense.expense'

    def get_default_period(self):
        today = datetime.today().date()
        period = today.strftime("%m") + '/' + today.strftime("%Y")
        periods = self.env['account.period'].search([['name', '=', period]])
        if not periods.state_paie:
            return periods
        else:
            return False

    def expense_accept(self):
        return self.sudo().write({'state': 'confirm1', 'date_valid': time.strftime('%Y-%m-%d'), 'user_valid': self._uid})

    def expense_accept1(self):
        return self.write({'state': 'confirm2', 'date_valid': time.strftime('%Y-%m-%d'), 'user_drh': self._uid})

    def expense_accept2(self):
        return self.write({'state': 'accepted', 'date_valid': time.strftime('%Y-%m-%d'), 'user_dg': self._uid})

    @api.one
    def refuse1(self):
        return self.write({'state': 'cancelled', 'date_valid': False, 'user_drh': False,'note':"refusé par le DRH"})

    @api.one
    def refuse2(self):
        return self.write({'state': 'cancelled', 'date_valid': False, 'user_dg': False,'note':"refusé par le DG"})

    mission=fields.Text('Mission')
    periode = fields.Many2one('account.period','Période',default=get_default_period )
    type = fields.Selection([('maroc', "Au maroc"),('etranger', "A l'étranger"),], default='maroc')
    state = fields.Selection([
            ('draft', 'New'),
            ('cancelled', 'Refused'),
            ('confirm', 'En attente d\'approbation du responsable'),
            ('confirm1', 'En attente d\'approbation du DRH'),
            ('confirm2', 'En attente d\'approbation du DG'),
            ('accepted', 'Approved'),
            ('done', 'Waiting Payment'),
            ('paid', 'Paid'),
            ],
            'Status', readonly=True, track_visibility='onchange', copy=False,
            help='When the expense request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to admin, the status is \'Waiting Confirmation\'.\
            \nIf the admin accepts it, the status is \'Accepted\'.\n If the accounting entries are made for the expense request, the status is \'Waiting Payment\'.')
    user_drh = fields.Many2one('res.users', 'Utilisateur DRH', readonly=True, copy=False,
                                      states={'draft':[('readonly',False)], 'confirm1':[('readonly',False)]})
    user_dg = fields.Many2one('res.users', 'Utilisateur DG', readonly=True, copy=False,
                               states={'draft': [('readonly', False)], 'confirm2': [('readonly', False)]})
    date_debut_mission = fields.Date('Date début de mission')
    date_fin_mission = fields.Date('Date fin de mission')


