# -*- coding: utf-8 -*-
from openerp import fields, models,api
from openerp import exceptions
from datetime import datetime
from dateutil.relativedelta import relativedelta

class primes(models.Model):
    _name = 'hr.primes'

    def get_periods(self):
        today = datetime.today().date()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        period_id = self.env['account.period'].search([['name','=',period]])
        periods = self.env['account.period'].search([['date_start','>=',period_id.date_start]])
        print periods
        period_ids=[]
        for p in periods:
            period_ids.append(p.id)

        return [('id','in',period_ids)]

    employee_id=fields.Many2one('hr.employee','employé')
    matricule=fields.Char(string='Matricule')
    periode = fields.Many2one('account.period','Période')#,domain=get_periods )
    montant = fields.Float('Montant')
    rubrique_id=fields.Many2one('hr.salary.rule','Prime/Indémnité',domain=[('negociable','=',True)])

    @api.model
    def create(self, vals):
        emp=False
        if vals.get('matricule'):
            emp=self.onchange_matricule(vals.get('matricule'))
            vals.update({'employee_id':emp.id})
        new_record = super(primes, self).create(vals)

        return new_record


    def onchange_matricule(self,matricule):
        emp=self.env['hr.employee'].search([('matricule','=',matricule)])
        if emp:
            return emp
        else:
            raise exceptions.ValidationError('''Ce matricule n'est pas valide''')

    @api.constrains('rubrique_id')
    def indomain(self):
        for prime in self:
            rub=self.env['hr.salary.rule'].browse([prime.rubrique_id.id])
            if not rub.negociable:
                raise exceptions.ValidationError('Vous ne pouvez pas utiliser la rubrique %s'%rub.name)
        for pr in self:
            prime_ids=self.search([['periode','=',pr.periode.id]])
            for pri in prime_ids:
                if pri.rubrique_id==pr.rubrique_id and pri.employee_id==pr.employee_id and pri!=pr:
                    raise exceptions.ValidationError('''Vous ne pouvez pas affecter une prime deux fois à l'employé %s durant la même période'''%pr.employee_id.name)




