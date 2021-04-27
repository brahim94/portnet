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
class EtatIR(models.TransientModel):
    _name = 'etat.ir.wizard'

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

    def get_totbrutImpo(self):
        bps=self.get_bulletin_done_ids()
        tot_cimp=0
        for bp in bps:
            for rule in bp.details_by_salary_rule_category:
                if rule.code=='BRUT':
                    tot_cimp=tot_cimp+rule.total
        return tot_cimp

    def get_totir(self):
        bps=self.get_bulletin_done_ids()
        tot_ir=0
        for bp in bps:
            for rule in bp.details_by_salary_rule_category:
                if rule.code=='IRPP':
                    tot_ir=tot_ir+rule.total
        return tot_ir

    def get_totnetImpo(self):
        bps=self.get_bulletin_done_ids()
        tot_netImpo=0
        for bp in bps:
            for rule in bp.details_by_salary_rule_category:
                if rule.code=='C_IMPR':
                    tot_netImpo=tot_netImpo+rule.total
        return tot_netImpo



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
        name = "Etat IR du %s au %s "\
               % (self.start_date,
                  self.end_date)
        #self.get_bulletin_done_ids()

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'paie.report_etat_ir',
            'datas': {
                'model': 'etat.ir.wizard',
                #'ids': list_ids,
                },
            'name': name,
            }

    def get_brutImpo(self,payslip):
        brut=0
        payslip_id=self.env['hr.payslip'].browse(payslip)
        for rule in payslip_id.details_by_salary_rule_category:
            if rule.code=='BRUT':
                brut=rule.total
        return brut

    def get_netImpo(self,payslip):
        netimpo=0
        payslip_id=self.env['hr.payslip'].browse(payslip)
        for rule in payslip_id.details_by_salary_rule_category:
            if rule.code=='C_IMPR':
                netimpo=rule.total
        return netimpo

    def get_ir(self,payslip):
        ir=0
        payslip_id=self.env['hr.payslip'].browse(payslip)
        for rule in payslip_id.details_by_salary_rule_category:
            if rule.code=='IRPP':
                ir=rule.total
        return ir
