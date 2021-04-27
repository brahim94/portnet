# -*- coding: utf-8 -*-
from datetime import datetime
from openerp import fields, models, api
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )
from hr_payslip import HrPayslip
from openerp import exceptions


class Structure(models.Model):
    _inherit = 'hr.payroll.structure'

    date_debut_structure = fields.Date('Date début',translate=True)
    date_fin_structure = fields.Date('Date fin',translate=True)

    @api.one
    def copy(self,default=None):
        rule_ids=self.rule_ids.copy()
        #self.create({'name': 'name___', 'code': 'code__','rule_ids': [(6, False, rule_ids.ids)] })
        #rule_ids=self.rule_ids.copy()
        #default.update({'rule_ids':self.rule_ids.copy()})
        return super(Structure, self).copy({'name': 'name___', 'code': 'code__','rule_ids': [(6, False, rule_ids.ids)] })





