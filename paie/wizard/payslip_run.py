# -*- coding: utf-8 -*-
import locale
from openerp import models, fields, api
from openerp import exceptions
from datetime import datetime, timedelta
import time
from dateutil import relativedelta
from openerp import netsvc
from openerp.tools import ( DEFAULT_SERVER_DATE_FORMAT,)
from openerp.tools import float_compare, float_is_zero
from lxml import etree
from openerp.osv.orm import setup_modifiers
import re


class PayslipRunInterWizard(models.TransientModel):
    _name='payslip.run.inter'

    payslip_id=fields.Many2one('hr.payslip','Name')
    #employee_id=fields.related('payslip.id.employee_id','Employé')
    select_payslip=fields.Boolean(default=True)
    wizard_id = fields.Many2one('payslip.run')


class PayslipRunWizard(models.TransientModel):
    _name = 'payslip.run'

    periode = fields.Many2one('account.period','Période' )
    payslip_ids=fields.One2many('payslip.run.inter','wizard_id')


    def onchange_period(self,cr,uid,ids,periode,context=None):
        value={}
        if periode:
            bp_ids=self.pool.get('hr.payslip').search(cr,uid,[('periode','=',periode),('simulation','=',False),('state','=','draft')])
            liste=[]
            for bp in bp_ids:
                val={
                    'select_payslip':True,
                    'payslip_id':bp,
                }
                liste.append((0,0,val))
            value.update(payslip_ids=liste)
            return {'value':value}
        else:
            raise exceptions.Warning('veuillez choisir une période valide')

    @api.multi
    def valider(self):
        for bp in self.payslip_ids:
            if bp.select_payslip:
                #bp_id=self.pool.get('hr.payslip').browse(cr,uid,bp.payslip_id)
                bp.payslip_id.hr_verify_sheet()
                bp.payslip_id.process_sheet()

        return {'warning':{'title':'Validation','message':'Les bulletins seléctionnés ont été validés'}}
