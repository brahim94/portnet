# -*- coding: utf-8 -*-
from openerp import fields, models, api,workflow
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )

class date_event(models.Model):
    _name='hr.date.event'

    date_limite = fields.Selection([(num, str(num)) for num in range(1,30)], 'Date limite')

class HrEvent(models.Model):
    _name = 'hr.event'

    def get_default_period(self):
        today = datetime.today()
        period =today.strftime("%m")+'/'+today.strftime("%Y")

        date_limite_ids=self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite=date_limite_ids[0]
            date_limite=str(datetime.today().year)+'-'+str(datetime.today().month)+'-'+str(date_limite.date_limite).zfill(2)

        next_period=str(today.month+1).zfill(2)+'/'+today.strftime("%Y")
        if date_limite and today<= datetime.strptime(date_limite, DEFAULT_SERVER_DATE_FORMAT) :
            periods = self.env['account.period'].search([['name','=',period]])
        else:
            periods=periods = self.env['account.period'].search([['name','=',next_period]])
        return periods or False

    @api.model
    def get_payslip_run_ids(self):
        payslip_run = []
        run_ids = self.env['hr.payslip.run'].search([])
        for r in run_ids:
            if r.date_start == self.date_from and r.state == 'draft':
                payslip_run.append(r.id)
        return [('id', 'in', payslip_run)]

    def get_periods(self):
        today = datetime.today()
        period =today.strftime("%m")+'/'+today.strftime("%Y")

        date_limite_ids=self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite=date_limite_ids[0]
            date_limite=str(datetime.today().year)+'-'+str(datetime.today().month)+'-'+str(date_limite.date_limite).zfill(2)
        year=today.year
        month=today.month
        if today.month+1>12:
            month=0
            year=year+1
        next_period=str(month+1).zfill(2)+'/'+str(year)
	if date_limite and today<= datetime.strptime(date_limite, DEFAULT_SERVER_DATE_FORMAT) :
            periods = self.env['account.period'].search([['name','=',period]])
        else:
            periods=periods = self.env['account.period'].search([['name','=',next_period]])
        periods = self.env['account.period'].search([['date_start','>=',periods[0].date_start]])
        period_ids=[]
        for p in periods:
            period_ids.append(p.id)
        return [('id','in',period_ids)]

    contract_id = fields.Many2one('hr.contract','Contrat')


    periode = fields.Many2one('account.period','Période',default=get_default_period,domain=get_periods )
    categorie_type_event = fields.Char('catégorie event')
    date = fields.Date('Date')
    date_debut= fields.Date('Date debut',translate=True)
    date_fin= fields.Date('Date fin',translate=True)
    deduire_jr_autorise=fields.Boolean('Déduire jours autorisés')
    duree = fields.Float('Duree',compute='compute_duration', store=True)
    duree_jr_leg = fields.Float('Durée',compute='get_duree',store=True)
    employee_id=fields.Many2one('hr.employee','employé')
    event_id=fields.Many2one('hr.payslip')
    event_type=fields.Many2one('hr.event.type','''Type d'événement''')
    heures_supp = fields.Float('''Nombre d'heure''')
    impact_conge = fields.Boolean('Impact congé')
    impact_salaire = fields.Boolean('Impact salaire')
    rupture_contrat = fields.Boolean('Rupture du contrat')
    justif = fields.Binary('Justificatif')
    notes= fields.Text('Notes')
    date_validation=fields.Date('Date Validation')
    status = fields.Selection([
        ('brouillon', "Brouillon"),
        ('valide', "Validé"),
        ], default='brouillon')

    @api.onchange('event_type')
    def onchange_type_event(self):
        self.impact_salaire=self.event_type.impact_salaire
        self.impact_conge=self.event_type.impact_conge
        self.categorie_type_event=self.event_type.category

    @api.depends('event_type')
    def get_duree(self):
            if self.event_type.salary_rule and self.event_type.salary_rule.category_id.code=='EVT':
                self.duree_jr_leg=self.event_type.salary_rule.amount_fix
            else:
                self.duree_jr_leg=0

    @api.depends('date_debut','date_fin')
    def compute_duration(self):
        hhpo = self.env['hr.holidays.public']
        days = 0.0
        if self.date_debut and self.date_fin:
            date_dt = start_date_dt = fields.Date.from_string(
            self.date_debut)
            end_date_dt = fields.Date.from_string(
            self.date_fin)
            while True:
                if not date_dt.weekday()==6:
                    days += 1.0
                if date_dt == end_date_dt:
                    break
                date_dt += relativedelta(days=1)
        self.duree= days
        return days

    @api.multi
    def action_valider(self):
        if self.categorie_type_event=='jrslegaux':
            xs=self.env['hr.holidays'].create({'holiday_type': 'employee','name':self.event_type.name, 'number_of_days_temp': self.duree_jr_leg,'type':'add','employee_id':self.employee_id.id,'state':'cancel','holiday_status_id':self.event_type.holiday.id})
            workflow.trg_validate(self._uid, 'hr.holidays', xs.id, 'validate', self._cr)
        #return self.write({'status': 'valide'})
        self.status="valide"
        if self.rupture_contrat:
            contrat_id=self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)])
            self.contract_id=contrat_id
            contrat_id.date_end=self.date
        payslips=self.event_id
        # if payslips:
        #     for p in payslips:
        #         p.calculer_nbr_jr_acquis()
        self.date_validation=datetime.now()
        return self.status


class ResCompany(models.Model):
    _inherit = 'res.company'

    mode_de_gestion = fields.Selection([('1', 'Annuel'),('2', 'Par événement')])
    type_id=fields.Many2one('hr.contract.type','type_contrat')
    @api.multi
    def valider_mode_getsion(self):
        return self.mode_de_gestion


class type_event(models.Model):
    _name='hr.event.type'

    name = fields.Char('''Type d'événement''')
    impact_salaire = fields.Boolean('Impact salaire')
    impact_conge = fields.Boolean('Impact congé')
    salary_rule = fields.Many2one('hr.salary.rule','''Règle salariale associée''',domain=[('category_id.code','in',['AEVT','EVT','HS','AbsMaladie'])])
    holiday = fields.Many2one('hr.holidays.status','Type de congé associé')
    category=fields.Selection([('absMaladie','Absence/Maladie'),('jrslegaux','Jours légaux'),('HS','Heures supplémentaires'),('autres','Autres')],'''Catégorie d'événement''')
    code=fields.Char('Code')


