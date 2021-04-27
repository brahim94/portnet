# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp import exceptions


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def test(self):
        vals={}
        payslips = self.browse(self._context['active_ids'])
        for e in payslips:
            print e.employee_id.email
        raise exceptions.Warning('mail')

    @api.multi
    def send(self):
        payslips = self.browse(self._context['active_ids'])
        for e in payslips:
            print e.employee_id.email


class Mail(models.Model):
    _inherit ='mail.mail'


    @api.model
    def test(self):
        payslips = self.env['hr.payslip'].browse(self._context['active_ids'])
        for e in payslips:
            print e.employee_id.email
        raise exceptions.Warning('mail')







