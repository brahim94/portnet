# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from cStringIO import StringIO
import base64
import xlwt
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Style
from openpyxl.drawing.image import Image
class OrdreVirementizard(models.TransientModel):
    _name = 'ordre.virement.wizard'

    start_date = fields.Date('Du')
    end_date = fields.Date('Au')

    def get_default_period(self):
        today = datetime.today().date()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        periods = self.env['account.period'].search([['name','=',period]])

        return periods or False
    periode = fields.Many2one('account.period','Période',default=get_default_period )

    @api.multi
    @api.onchange('periode')
    def onchange_period(self):
        if self.periode:
            self.start_date=self.periode.date_start
            self.end_date=self.periode.date_stop
        else:
            raise exceptions.Warning('veuillez choisir une période valide')

    @api.model
    def get_bulletin_ids(self, periode):
        domain = [
            ('periode', '=', periode),
            ('simulation','=',False)
            #('state','=','done')
            ]
        return self.env['hr.payslip'].search(domain)

    @api.multi
    def get_bulletin_done_ids(self):
        ids=self.get_bulletin_ids(self.periode.id)
        list_ids = ids

        if list_ids:
            return list_ids
        else:
            raise exceptions.Warning('Il n y a aucun bulletin de paie durant cette période')

    @api.multi
    def get_date_now(self):
        now = datetime.now()
        return now.strftime("%d/%m/%Y")

    @api.multi
    def get_time_now(self):
        now = datetime.now()
        return now.strftime("%H:%M")
    @api.multi
    def button_report_pdf(self):
        #ids=self.get_bulletin_ids(self.periode.id)
        #ids = self.get_bulletin_done_ids()
        name = "Ordre de virement du %s au %s "\
               % (self.start_date,
                  self.end_date)
        #self.get_bulletin_done_ids()

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'paie.report_ordre_virement',
            'datas': {
                'model': 'ordre.virement.wizard',
                #'ids': list_ids,
                },
            'name': name,
            }

    def get_rib(self,employee):
        rib=''
        employee_id=self.env['hr.employee'].browse(employee)
        if employee_id.status=="valide":
            if(employee_id.rib_code_ville==False and employee_id.rib_code_banque==False) and employee_id.rib_code_guichet==False and employee_id.rib_numero_de_banque==False and employee_id.cle_rib==False:
                rib=' '
            else:
                rib=str(employee_id.rib_code_ville)+''+str(employee_id.rib_code_banque)+''+str(employee_id.rib_code_guichet)+''+str(employee_id.rib_numero_de_banque)+''+str(employee_id.cle_rib)
        return rib

    def get_net(self,payslip):
        net=0
        payslip_id=self.env['hr.payslip'].browse(payslip)
        for rule in payslip_id.details_by_salary_rule_category:
            if rule.code=='NET':
                net=rule.total
        return net


