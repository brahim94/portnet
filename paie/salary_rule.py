# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp import exceptions


class SalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _inherit = ['hr.salary.rule', 'mail.thread']

    rule_id = fields.Many2one('hr.contract.type','Rubriques')


    @api.onchange('child_ids')
    def _default_name(self):
        if self.parent_rule_id and isinstance(self.id, models.NewId):
            self.name=self.parent_rule_id.name
            self.category_id = self.parent_rule_id.category_id
            self.code = self.parent_rule_id.code
            self.sequence =  self.parent_rule_id.sequence
            self.condition_select = self.parent_rule_id.condition_select

    condition_python = fields.Text(track_visibility='onchange')
    active = fields.Boolean(track_visibility='onchange')
    appears_on_payslip = fields.Boolean(track_visibility='onchange')
    sequence = fields.Integer(track_visibility='onchange')
    name = fields.Char(track_visibility='onchange')
    category_id = fields.Many2one(track_visibility='onchange')
    code = fields.Char(track_visibility='onchange')
    date_debut = fields.Date('Date début',default='2000-01-01',translate=True)
    date_fin = fields.Date('Date fin',default='2099-01-01',translate=True)
    negociable = fields.Boolean('Négociable', track_visibility='onchange')
    amount_select = fields.Selection([('percentage', 'Pourcentage %'), ('fix', 'Montant fix'), ('code', 'Code python')], track_visibility='onchange')
    amount_python_compute = fields.Text(track_visibility='onchange')
    niveau = fields.Selection([('1','Pays'),('2','')],default='2')
    code_rub=fields.Integer('Code rubrique', track_visibility='onchange')
    taux_rapport = fields.Float('Taux pour rapport', help='''Ce champs est utilisé uniquement pour l'impression des 
    rapports de bulletin de paie l'administrateur des règles de paie doit s'assurer que ce taux est en cohérence avec
     la méthode de calcule de la règle. Par exemple son code python''', track_visibility='onchange')



    @api.one
    @api.constrains('date_debut','date_fin')
    def _check_dates(self):
        if self.parent_rule_id:
            rules = self.search([('parent_rule_id','=',self.parent_rule_id.id)])
            rules=rules | self.parent_rule_id
            rules=rules - self
            po=[]
            for p in rules:
                if p.date_debut<=self.date_debut<=p.date_fin or p.date_debut<=self.date_fin<=p.date_fin:
                    po.append(p)
            if len(po)>0:
                raise exceptions.ValidationError('Vous ne pouvez pas créer des règles salariales pour des périodes qui se chevauchent!')
            if self.date_fin< self.date_debut:
                raise exceptions.ValidationError('La date début doit être inférieure à date fin !')




