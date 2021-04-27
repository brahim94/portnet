# -*- coding: utf-8 -*-
import locale
from openerp import exceptions
from datetime import datetime, timedelta
import time
from openerp import netsvc
from openerp.tools.translate import _
from openerp import fields, models, api, tools, workflow
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )
from openerp.tools import float_compare, float_is_zero
from lxml import etree
from openerp.osv.orm import setup_modifiers
import re


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    #spec portnet
    loan=fields.Float(compute='get_loan',store=True)
    ded_pret_plaf=fields.Float(compute='get_loan',store=True,help="Total des intérêts cumulés")
    ded_pret_mensuel=fields.Float(compute='get_loan',store=True,help="Intérêts mensuel")
    ded_pret=fields.Float(compute='get_loan',store=True,help="Total des intérêts cumulés pour les logements sociaux")
    ##
    ##spec portnet
    @api.one
    @api.depends('employee_id','periode')
    def get_loan(self):
        self.loan=0
        somme_ded=0
        somme_ded_net=0
        array=[]
        valeur_mensuel = 0
        loan_ids=self.env['hr.loan.line'].search([['employee_id','=',self.employee_id.id]])
        for loan in loan_ids:
            #La condition sur le paiement à été enlever puisque la régle ded_pret utilise le cumul des prêts
            if loan.loan_id.payment_start_date<=loan.paid_period.date_start and loan.paid_period.date_start<=self.date_from:
                array.append(loan)
                #Valeur mensuel
                if loan.paid_period.id == self.periode.id:
                    valeur_mensuel = loan.loan_interest
        for a in array:
            for ar in a:
                if ar.loan_id.type_loan=='social':
                    somme_ded=somme_ded+ar.loan_interest
                else:
                    somme_ded_net=somme_ded_net+ar.loan_interest
        self.loan = valeur_mensuel
        self.ded_pret = somme_ded
        self.ded_pret_plaf = somme_ded_net
        self.ded_pret_mensuel = valeur_mensuel
        return array

    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        contract_ids=super(HrPayslip,self).get_contract(cr,uid,employee=employee,date_from=date_from,date_to=date_to)
        contract_obj = self.pool.get('hr.contract')
        contracts=[]
        for co in contract_ids:
            contract_id=contract_obj.browse(cr, uid, co, context=context)
            if contract_id.status=='valide':
                contracts.append(co)
        return contracts



    @api.multi
    def hr_verify_sheet(self):
        res = super(HrPayslip, self).hr_verify_sheet()
        ##spec portnet
        arr=self.get_loan()
        for ar in arr:
            for l in ar:
                l.paid=True
        ##
        events=self.env['hr.salary.rule'].search([['code','=',str(self.id)]])
        for evt in events:
            evt.unlink()
        #self.check_payroll()
        return res


    @api.multi
    def check_payroll(self):
        if self.employee_id:
            ##spec portnet
            hol=self.env['hr.holidays.status'].search([])
            holiday_type_name = 'Congés payés '+ str(self.periode.fiscalyear_id.name)
            holiday_status=self.env['hr.holidays.status'].search([('name','=',holiday_type_name),('year','=',self.periode.fiscalyear_id.name)])
            ##
            payrolls = self.search([['date_from','<=',self.date_from],['date_to','>=',self.date_from],'|',['date_from','<=',self.date_to],['date_to','>=',self.date_to],['employee_id','=',self.employee_id.id],['state','=','done' ]])
            if len(payrolls)>0:
                raise exceptions.Warning('Vous ne pouvez pas avoir deux bulletins validés pour un employé dans la même période!')
            else:
                ##spec
                if not holiday_status:
                    raise exceptions.Warning('''Le type de congé demandé n'existe pas: %s'''%holiday_type_name)
                else:
                    ##
                    xs=self.env['hr.holidays'].create({'holiday_type': 'employee','name':'Jours acquis du %s'%self.periode.name, 'number_of_days_temp': self.jours_acquis,'type':'add','periode':self.periode.id,'employee_id':self.employee_id.id,'state':'draft','holiday_status_id':holiday_status.id,'posted_date':self.date_to})
                    xs.write({'state':'validate'})
                    print xs

