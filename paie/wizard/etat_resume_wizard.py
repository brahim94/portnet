# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp import exceptions
from datetime import datetime, timedelta
import time
from dateutil import relativedelta
from openerp import netsvc
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )
from openerp.tools import float_compare, float_is_zero
from lxml import etree
from openerp.osv.orm import setup_modifiers
import re


class HrEtatResumepWizard(models.TransientModel):
    _name = 'hr.etat.resume.wizard'

    start_date = fields.Date('Du', default=fields.Date.today,translate=True)
    end_date = fields.Date('Au', default=fields.Date.today,translate=True)
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
    def get_bulletin_ids(self, start_date, end_date):
        domain = [
            ('date_from', '<=', start_date),
            ('date_to', '>=', end_date),
            ('simulation','=',False)
            #('state','=','done')
            ]
        return self.env['hr.payslip'].search(domain)

    @api.multi
    def get_bulletin_done_ids(self):
        ids=self.get_bulletin_ids(self.start_date, self.end_date)
        list_ids = []
        i = 0
        while i <len(ids)/3.0:
            list_ids.append(ids[3*i:(i+1)*3])
            i += 1
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
    def get_effectifs(self):
        ids=self.get_bulletin_ids(self.start_date, self.end_date)
        nbr_h=0
        nbr_f=0
        for i in ids:
            if i.employee_id.gender=='male':
                nbr_h=nbr_h+1
            elif i.employee_id.gender=='female':
                nbr_f=nbr_f+1
        return {'nbr_h':nbr_h,'nbr_f':nbr_f}


    @api.multi
    # def get_sum(self):
    #     ids=self.get_bulletin_ids(self.start_date, self.end_date)
    #     total={'total':0.00,'cnssglobal':0.00,'totcnsssal':0.00,'totcnsspat':0.00,'cotallocation':0.00,'cotform':0.00,'partamo':0.00,'amopat':0.00,'totamo':0.00,'totcnss':0.00,'cotcnsspat':.00,'base':0.00,'anciennete':0.00,'representation':0.00,'transport':0.00,'panier':0.00,'totbrut':0.00,'cotcnss':0.00,'cotamo':0.00
    #             ,'fpro':0.00,'totcot':0.00,'ir':0.00,'arrprec':0.00,'arrencours':0.00,'nbrpersoch':0.00,'dedperso':0.00,
    #            'presence_jrs':0.00+26*len(ids),'brut_cnss':0.00,'cot_sal':0.00,'cot_pat':0.00,'net':0.00,'net_imp':0.00,'cout':0.00,'presence':0.00+191*len(ids),'conge_acquis':float(2*len(ids)),'hrs_trav':1.00+191*len(ids)}
    #     for i in ids:
    #         for rule in i.details_by_salary_rule_category:
    #
    #             if rule.code=='C1MaCotisationFamiliale':
    #                 total['cotallocation']=total['cotallocation']+rule.total
    #             if rule.code=='C1MaFormation':
    #                 total['cotform']=total['cotform']+rule.total
    #
    #             if rule.code=='C1MamoPatroParticip':
    #                 total['partamo']=total['partamo']+rule.total
    #             if rule.code=='C1MamoPat':
    #                 total['amopat']=total['amopat']+rule.total
    #
    #             if rule.code=='CNSS Ma':
    #                 total['cotcnsspat']=total['cotcnsspat']+rule.total
    #
    #             if rule.code==' BrutCNSSma ':
    #                 total['brut_cnss']=total['brut_cnss']+rule.total
    #             if rule.code=='CS':
    #                 total['cot_sal']=total['cot_sal']+rule.total
    #             if rule.code=='TCOMPMA':
    #                 total['cot_pat']=total['cot_pat']+rule.total
    #             if rule.code=='NET':
    #                 total['net']=total['net']+rule.total
    #             if rule.code=='C_IMP':
    #                 total['net_imp']=total['net_imp']+rule.total
    #             if rule.code=='TOTAL':
    #                 total['cout']=total['cout']+rule.total
    #             if rule.code=='BASE':
    #                 total['base']=total['base']+rule.total
    #             if rule.code=='ANCIENNETE':
    #                 total['anciennete']=total['anciennete']+rule.total
    #             if rule.code=='IndRep':
    #                 total['representation']=total['representation']+rule.total
    #             if rule.code=='IndemniteTransport':
    #                 total['transport']=total['transport']+rule.total
    #             if rule.code=='IndemnitePanier':
    #                 total['panier']=total['panier']+rule.total
    #             if rule.code=='BRUT':
    #                 total['totbrut']=total['totbrut']+rule.total
    #             if rule.code=='CNSS ma':
    #                 total['cotcnss']=total['cotcnss']+rule.total
    #             if rule.code=='C1ma':
    #                 total['cotamo']=total['cotamo']+rule.total
    #             if rule.code=='FPRO':
    #                 total['fpro']=total['fpro']+rule.total
    #             if rule.code=='SALC':
    #                 total['totcot']=total['totcot']+rule.total
    #
    #             if rule.code=='IRPP':
    #                 total['ir']=total['ir']+rule.total
    #             if rule.code=='arrondiEnCours':
    #                 total['arrencours']=total['arrencours']+rule.total
    #             if rule.code=='arrondiEnCours':
    #                 total['arrprec']=total['arrprec']+rule.total
    #             if rule.code=='NbrPerso':
    #                 total['nbrpersoch']=total['nbrpersoch']+rule.total
    #             if rule.code=='DEDPERSO':
    #                 total['dedperso']=total['dedperso']+rule.total
    #     total['totcnsspat']=total['cotcnsspat']+total['amopat']+total['cotform']+total['cotallocation']+total['partamo']
    #     total['totcnsssal']=total['cotcnss']+total['cotamo']
    #     total['totamo']=total['cotamo']+total['amopat']
    #     total['cnssglobal']=total['totcnsssal']+total['totcnsspat']
    #     total['totcnss']=total['cotcnss']+total['cotcnsspat']
    #     total['total']=total['fpro']+total['totcnsssal']
    #     total['totalglobal']=total['total']+total['totcnsspat']
    #     import locale
    #     for ll in total:
    #         total[ll]=locale.format("%.2f", total[ll], grouping=True)
    #     print total
    #     return total


    #portnet
    def get_sum(self):
        ids=self.get_bulletin_ids(self.start_date, self.end_date)
        total={'base_modep_pat':0.00,'totcaad':0.00,'totmodep':0.00,'totsaham':0.00,'totcnops':0.00,'base_caad':0.00,'caad_pat':0.00,'issaf_pat':0.00,'cnops_pat':0.00,'caad':0.00,'cnops':0.00,'modep':0.00,'modep_pat':0.00,'saham':0.00,'base_modep':0.00,'base_cnops':0.00,'base_rcar_rc':0.00,'base_rcar_rg':0.00,'rcar_rc':0.00,'part_pat_rcar_rc':0.00,'totrcar_rc':0.00,'total':0.00,'cnssglobal':0.00,'totcnsssal':0.00,'totcnsspat':0.00,'cotallocation':0.00,'cotform':0.00,'partamo':0.00,'amopat':0.00,'totamo':0.00,'totrcarrg':0.00,'rcar_rg_pat':.00,'base':0.00,'anciennete':0.00,'representation':0.00,'transport':0.00,'panier':0.00,'totbrut':0.00,'rcar_rg':0.00,'cotamo':0.00
                ,'fpro':0.00,'totcot':0.00,'ir':0.00,'arrprec':0.00,'arrencours':0.00,'nbrpersoch':0.00,'dedperso':0.00,
               'presence_jrs':0.00+26*len(ids),'cumul_BRUT':0.00,'cot_sal':0.00,'epargne_retraite':0.00,'cot_pat':0.00,'net':0.00,'net_imp':0.00,'cout':0.00,'presence':0.00+191*len(ids),'conge_acquis':float(2*len(ids)),'hrs_trav':1.00+191*len(ids)}
        for i in ids:
            for rule in i.details_by_salary_rule_category:

                if rule.code in ['epargne_retraite', 'epargne_retraite_v']:
                    total['epargne_retraite']=total['epargne_retraite']+rule.total
                if rule.code=='part_pat_caad':
                    total['caad_pat']=total['caad_pat']+rule.total
                if rule.code=='cnops_pat':
                    total['cnops_pat']=total['cnops_pat']+rule.total
                if rule.code=='part_pat_sm':
                    total['modep_pat']=total['modep_pat']+rule.total
                if rule.code=='part_pat_isaaf':
                    total['issaf_pat']=total['issaf_pat']+rule.total
                if rule.code=='part_sal_sc':
                    total['cnops']=total['cnops']+rule.total
                if rule.code=='caad':
                    total['caad']=total['caad']+rule.total
                if rule.code=='partsalsm':
                    total['modep']=total['modep']+rule.total
                if rule.code=='issaf':
                    total['saham']=total['saham']+rule.total
                if rule.code=='BRUT':
                    total['totbrut']=total['totbrut']+rule.total
                    if rule.total>9166.5:
                        total['base_modep']=total['base_modep']+9166.5
                    else:
                        total['base_modep']=total['base_modep']+rule.total
                    if rule.total>12083.25:
                        total['base_modep_pat']=total['base_modep_pat']+12083.25
                    else:
                        total['base_modep_pat']=total['base_modep_pat']+rule.total

                    if rule.total>16000:
                        total['base_cnops']=total['base_cnops']+16000
                    else:
                        total['base_cnops']=total['base_cnops']+rule.total
                    if rule.total>8333.75:
                        total['base_caad']=total['base_caad']+8333.75
                    else:
                        total['base_caad']=total['base_caad']+rule.total

                    if rule.total>16117:
                        total['base_rcar_rg']=total['base_rcar_rg']+16117
                        total['base_rcar_rc']=total['base_rcar_rc']+(rule.total-16117)

                    else:
                        total['base_rcar_rg']=total['base_rcar_rg']+rule.total

                if rule.code=='rcar_rc':
                    total['rcar_rc']=total['rcar_rc']+rule.total
                if rule.code=='part_pat_rcar_rc':
                    total['part_pat_rcar_rc']=total['part_pat_rcar_rc']+rule.total

                if rule.code=='C1MaCotisationFamiliale':
                    total['cotallocation']=total['cotallocation']+rule.total
                if rule.code=='C1MaFormation':
                    total['cotform']=total['cotform']+rule.total

                if rule.code=='C1MamoPatroParticip':
                    total['partamo']=total['partamo']+rule.total
                if rule.code=='C1MamoPat':
                    total['amopat']=total['amopat']+rule.total

                if rule.code=='rcar_rg_pat':
                    total['rcar_rg_pat']=total['rcar_rg_pat']+rule.total

                if rule.code==' BrutCNSSma ':
                    total['cumul_BRUT']=total['cumul_BRUT']+rule.total
                if rule.code=='CS':
                    total['cot_sal']=total['cot_sal']+rule.total
                if rule.code=='TCOMPMA':
                    total['cot_pat']=total['cot_pat']+rule.total
                if rule.code=='NET':
                    total['net']=total['net']+rule.total
                if rule.code=='C_IMP':
                    total['net_imp']=total['net_imp']+rule.total
                if rule.code=='TOTAL':
                    total['cout']=total['cout']+rule.total
                if rule.code=='BASE':
                    total['base']=total['base']+rule.total
                if rule.code=='ANCIENNETE':
                    total['anciennete']=total['anciennete']+rule.total
                if rule.code=='IndRep':
                    total['representation']=total['representation']+rule.total
                if rule.code=='IndemniteTransport':
                    total['transport']=total['transport']+rule.total
                if rule.code=='IndemnitePanier':
                    total['panier']=total['panier']+rule.total
                # if rule.code=='BRUT':
                #     total['totbrut']=total['totbrut']+rule.total
                if rule.code=='rcar_rg':
                    total['rcar_rg']=total['rcar_rg']+rule.total
                if rule.code=='C1ma':
                    total['cotamo']=total['cotamo']+rule.total
                if rule.code=='FPRO':
                    total['fpro']=total['fpro']+rule.total
                if rule.code=='SALC':
                    total['totcot']=total['totcot']+rule.total

                if rule.code=='IRPP':
                    total['ir']=total['ir']+rule.total
                if rule.code=='arrondiEnCours':
                    total['arrencours']=total['arrencours']+rule.total
                if rule.code=='arrondiEnCours':
                    total['arrprec']=total['arrprec']+rule.total
                if rule.code=='NbrPerso':
                    total['nbrpersoch']=total['nbrpersoch']+rule.total
                if rule.code=='DEDPERSO':
                    total['dedperso']=total['dedperso']+rule.total
        total['totcnsspat']=total['rcar_rg_pat']+total['amopat']+total['cotform']+total['cotallocation']+total['partamo']
        total['totcnsssal']=total['rcar_rg']+total['cotamo']
        total['totamo']=total['cotamo']+total['amopat']
        total['cnssglobal']=total['totcnsssal']+total['totcnsspat']
        total['totrcarrg']=total['rcar_rg']+total['rcar_rg_pat']
        total['totrcar_rc']=total['rcar_rc']+total['part_pat_rcar_rc']
        total['totcaad']=total['caad']+total['caad_pat']
        total['totmodep']=total['modep']+total['modep_pat']
        total['totcnops']=total['cnops']+total['cnops_pat']
        total['totsaham']=total['saham']+total['issaf_pat']

        total['total']=total['fpro']+total['totcnsssal']
        total['totalglobal']=total['total']+total['totcnsspat']
        import locale
        for ll in total:
            total[ll]=locale.format("%.2f", total[ll], grouping=True)
        return total


    @api.multi
    def get_line_ids(self):
        list=self.get_bulletin_done_ids()
        if list:
            return list[0][0].line_ids
        else:
            return False

    @api.multi
    def export_etat_resume(self):
        #ids = self.get_bulletin_done_ids()
        name = "Etat résumé des cotisations %s au %s "\
               % (self.start_date,
                  self.end_date)
        self.get_bulletin_done_ids()

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'paie.report_document_etat_resume',
            'datas': {
                'model': 'hr.etat.resume.wizard',
                #'ids': list_ids,
                },
            'name': name,
            }