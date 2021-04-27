# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )
from datetime import datetime

class HrLoan(models.Model):
    _name = 'hr.loan'

    name = fields.Char('Référence')
    employee_id = fields.Many2one('hr.employee','Employé',required=True)
    total_loan = fields.Float('Montant')
    rate = fields.Float('Taux')
    payment_start_date = fields.Date(string='''Date d'effet''', required=True, default=fields.Date.today())
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line")
    type_loan=fields.Selection([('social', 'Logement social'),('autres', 'Autres'),], 'Type de logement', select=True)

    @api.multi
    def check_date(self):
        now=datetime.now().year
        if now<datetime.strptime(self.payment_start_date, DEFAULT_SERVER_DATE_FORMAT).year:
            return False
        else:
            return True

    _constraints = [
        (check_date, '''Date d'effet ne doit pas dépasser l'année en cours ''',['payment_start_date']),
    ]


class HrLoanLine(models.Model):
    _name="hr.loan.line"

    paid_period = fields.Many2one('account.period','Période',required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    paid_amount= fields.Float(string="Mensualité", required=True)
    paid = fields.Boolean(string="Prélevé")
    loan_id =fields.Many2one('hr.loan', string="Loan Ref.", ondelete='cascade')
    payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    loan_interest = fields.Float('Intérêt')

    @api.model
    def create(self, vals):
        emp= self.env['hr.loan'].browse(vals['loan_id']).employee_id
        vals.update({'employee_id':emp.id})
        res=super(HrLoanLine,self).create(vals)
        return res