# -*- coding: utf-8 -*-
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )
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

class modep_report(models.TransientModel):
    _name = 'modep.report'

    fec_data= fields.Binary('LCR File', readonly=True)
    filename= fields.Char('Filename', size=256, readonly=True)


class cot_modep_report(models.Model):
    _name = 'cot.modep.report'

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
            #('state','=','done'),
            ('simulation','=',False)
            ]
        return self.env['hr.payslip'].search(domain)

    def get_form(self):
       return  {
           'LINE1' :
               [
                   {'annee':{'length':2,'type':'int'}},
                   {'mois':{'length':2,'type':'int'}},
                   {'modep':{'length':5,'type':'string'}},
                   {'matricule':{'length':6,'type':'int'}},
                   {'nax':{'length':6,'type':'string'}},
                   {'sbi':{'length':9,'type':'float'}},
                   {'sm_sal':{'length':9,'type':'float'}},
                   {'caad_sal':{'length':9,'type':'float'}},
                   {'issaf_sal':{'length':9,'type':'float'}},
                   {'sm_pat':{'length':9,'type':'float'}},
                   {'caad_pat':{'length':9,'type':'float'}},
                   {'issaf_pat':{'length':9,'type':'float'}},
                   {'nom':{'length':30,'type':'string'}},
                    ]
                    }

    def create_line(self, line, type_line):
        string_line=""
        for ele in self.get_form()[type_line]:
            if ele.values()[0].get('type')=='string':
                string_line += line.get(ele.keys()[0]).ljust(ele.values()[0].get('length'),' ')[0:ele.values()[0].get('length')]
            elif ele.values()[0].get('type')=='float':
                print line.get(ele.keys()[0])
                string_line += str(format(int(line.get(ele.keys()[0])*100), '0'+ str(ele.values()[0].get('length'))))[0:ele.values()[0].get('length')]
            else:
                string_line += str(format(line.get(ele.keys()[0]), '0'+ str(ele.values()[0].get('length'))))[0:ele.values()[0].get('length')]
        return string_line

    @api.multi
    def export_txt(self):
        bp_ids=self.get_bulletin_ids(self.periode.id)
        data = []
        cc = 1
        output = StringIO()
        for bp in bp_ids:
            periode=str.split(str(bp.periode.name),'/')
            mois=periode[0]
            annee=periode[1][2]+''+periode[1][3]
            sbi=0
            sm_sal=0
            caad_sal=0
            issaf_sal=0
            sm_pat=0
            caad_pat=0
            issaf_pat=0
            for rule in bp.details_by_salary_rule_category:
                if rule.code=='BRUT':
                    sbi=rule.total
                elif rule.code=='part_sal_sm':
                    sm_sal=rule.total
                elif rule.code=='caad':
                    caad_sal=rule.total
                elif rule.code=='issaf':
                    issaf_sal=rule.total
                elif rule.code=='part_pat_sm':
                    sm_pat=rule.total
                elif rule.code=='part_pat_caad':
                    caad_pat=rule.total
                elif rule.code=='part_pat_isaaf':
                    issaf_pat=rule.total
            line = {
                "annee":int(annee),
                "mois":int(mois),
                "modep":'modep',
                "matricule":int(bp.employee_id.matricule),
                "nax":'xxxxxx',
                "sbi":sbi,
                "sm_sal":sm_sal,
                "caad_sal":caad_sal,
                "issaf_sal":issaf_sal,
                "sm_pat":sm_pat,
                "caad_pat":caad_pat,
                "issaf_pat":issaf_pat,
                "nom":bp.employee_id.name,
            }
            data.append(self.create_line(line,'LINE1'))
            output.write("%s\n" %(self.create_line(line,'LINE1')))

        vals={'fec_data': base64.encodestring(output.getvalue()),'filename': 'modep.txt'}
        wizard_id = self.pool.get('modep.report').create(self._cr, self._uid, vals, context=self._context)
        return {
            'name':_("Rapport txt test"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'modep.report',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': '[]',
            }