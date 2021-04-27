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
from datetime import datetime
from dateutil.relativedelta import relativedelta


class one2many_mod2(fields.One2many):

    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        if context is None:
            context = {}
        if not values:
            values = {}
        res = {}
        for id in ids:
            res[id] = []
        ids2 = obj.pool[self._obj].search(cr, user, [(self._fields_id,'in',ids), ('appears_on_payslip', '=', True),('total','!=',0)], limit=self._limit)
        for r in obj.pool[self._obj].read(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
            key = r[self._fields_id]
            if isinstance(key, tuple):
                key = key[0]
            res[key].append(r['id'])
        return res


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    line_ids= one2many_mod2('hr.payslip.line', 'slip_id', 'Payslip Lines', readonly=True,domain=[('total','!=',0),('appears_on_payslip', '=', True)], states={'draft':[('readonly',False)]})


    #payslipid = fields.Many2one('simulateur','payslips')
    simulation=fields.Boolean('Simulation',default=False)
    totalExpense = fields.Float(compute='get_total_expense')
    totalCotRetraite=fields.Float(compute='get_total_retraite')
    totalHS125=fields.Float(compute='get_total_hs125')
    totalHS150=fields.Float(compute='get_total_hs150')
    totalHS200=fields.Float(compute='get_total_hs200')
    regul_mt_ir = fields.Float('Regul montant IR')

    @api.one
    @api.depends('periode','employee_id')
    def get_total_hs125(self):
        for rub in self.rubriques_ids:
            if rub.name.code=='BASE':
                sal_base=rub.montant
                break
        total=0
        event_hs_ids=self.env['hr.event'].search([('status','=','valide'),('employee_id','=',self.employee_id.id),('periode','=',self.periode.id)])
        for eve in event_hs_ids:
            if eve.event_type.code=='HS125':
                total=total+eve.heures_supp
        self.totalHS125=total*125/float(100)*sal_base/191
        return self.totalHS125
    @api.one
    @api.depends('periode','employee_id')
    def get_total_hs150(self):
        for rub in self.rubriques_ids:
            if rub.name.code=='BASE':
                sal_base=rub.montant
                break
        total=0
        event_hs_ids=self.env['hr.event'].search([('status','=','valide'),('employee_id','=',self.employee_id.id),('periode','=',self.periode.id)])
        for eve in event_hs_ids:
            if eve.event_type.code=='HS150':
                total=total+eve.heures_supp
        self.totalHS150=total*150/float(100)*sal_base/191
        return self.totalHS150

    @api.one
    @api.depends('periode','employee_id')
    def get_total_hs200(self):
        for rub in self.rubriques_ids:
            if rub.name.code=='BASE':
                sal_base=rub.montant
                break
        total=0
        event_hs_ids=self.env['hr.event'].search([('status','=','valide'),('employee_id','=',self.employee_id.id),('periode','=',self.periode.id)])
        for eve in event_hs_ids:
            if eve.event_type.code=='HS200':
                total=total+eve.heures_supp
        self.totalHS200=total*150/float(100)*sal_base/191
        return self.totalHS200

    @api.one
    @api.depends('periode','employee_id')
    def get_total_retraite(self):
        total=0
        contrat_comp_ids=self.env['hr.contrat.complementaire'].search([('employee_id','=',self.employee_id.id)])
        for con in contrat_comp_ids:
            if con.cotisation_fixe and datetime.strptime(con.date_effet, DEFAULT_SERVER_DATE_FORMAT)<=datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT):
                print 'a'
                total=total+con.montant_retraite
        self.totalCotRetraite=total
        return self.totalCotRetraite

    @api.one
    @api.depends('periode', 'employee_id')
    def get_total_expense(self):
        total=0
        expense_ids=self.env['hr.expense.expense'].search([('employee_id','=',self.employee_id.id),('periode','=',self.periode.id),('state','=','accepted'),('type','=','maroc')])
        for exp in expense_ids:
            total=total+exp.amount
        self.totalExpense=total
        return self.totalExpense

    def nbr_jr_trav(self):
        nbr=0
        for l in self.worked_days_line_ids:
            nbr=nbr+l.number_of_days
        return locale.format("%.2f", nbr, grouping=True)

    regul_jr_ir=fields.Float('Régul Jour IR',help="""En cas de reprise, saisir le nombre de jours d’absence du mois impactant l’IR.
                                                    En cas de rappel, saisir le nombre de jours de présence supplémentaire en négatif""")
    mois_en_cours = fields.Char(compute='get_mois_en_cours',store=True)
    nbr_jours_travail = fields.Float(compute='get_nbr_jr_trav')
    nbr_jours = fields.Float(compute='get_nbr_jr_conges_payes')
    nbr_jr_conges_payes=fields.Float(compute='nbr_jr_conges_payes')
    sal_journalier = fields.Float(compute='get_salaire_journalier')
    nbr_jours_absence = fields.Float(compute='add_event_in_rules')
    matricule = fields.Char(related='employee_id.matricule', string='Matricule', store=True)
    regul_pret = fields.Boolean(string='Mois de régularisation de prêt', help="Ce champ permet de dire si ce mois contient une régularisation de prêt immobilier ou non. Si oui, il faut cocher ce champ")

    def _get_default_journal(self):
        journal=self.env['account.journal'].search([['code','=','JPaie']])
        return journal or False

    def get_default_period(self):
        today = datetime.today().date()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        periods = self.env['account.period'].search([['name','=',period]])
        return periods or False

    # TODO: utiliser un dictionnaire qui contiendra tous les cumuls
    payslip_used_for_cumuls = fields.Many2one('hr.payslip', "Bulletin utilisé", help = 'Bulletin qui a servi pour remonter les cumuls', readonly = True)
    brutCNSSma = fields.Float('Cumul Brut Imposable')
    cumul_Net_imposable = fields.Float('Cumul Net Imposable régularisé')
    cumul_Net_imposable_nr = fields.Float('Cumul Net Imposable')
    cumul_IRPP = fields.Float('Cumul IR')
    cumulregularise = fields.Float('Cumul imposable régularisé')
    ded_cachrges_famil = fields.Float('Cumul Déd.Charges Familiales')
    cumul_FPRO = fields.Float('Cumul Frais Professionnels')
    cumul_deductions_log = fields.Float('Cumul déductions logement')
    cumul_interet = fields.Float('Cumul Intérêt Habitat')
    cumul_jours = fields.Float('Cumul Jours Travaillés')
    cumul_regul_jr_ir = fields.Float('Cumul régul jour IR')
    cumul_epargne = fields.Float('Cumul épargne retraite')
    cumul_CAAD = fields.Float('Cumul CAAD')
    cumul_MODEP = fields.Float('Cumul MODEP')
    cumul_assurance = fields.Float('Cumul Assurance')
    cumul_Charges_salariales = fields.Float('Cumul Charges Salariales')
    cumul_imposable = fields.Float(compute='somme_cumul_imposable',store=True)
    cumul_recore_sal = fields.Float('Cumul RECORE')
    cumul_cnops = fields.Float('Cumul CNOPS')
    cumul_rcar_rc = fields.Float('Cumul RCAR RC')
    cumul_rcar_rg = fields.Float('Cumul RCAR RG')
    cumul_tcompma = fields.Float('Cumul Cotisations Patronales')
    brutnimposable = fields.Float('Cumul Brut N Imposable')

    # jours congés acquis / pris / ...
    reliquat = fields.Float('Reliquat N-1',compute='sum_jrs_acquis',store=True) #LE RELIQUAT EST LA SOMME DES ATTRIBUTIONS  DE CONGÉ VALIDÉES SUR N-1 ET N-2
    jours_acquis = fields.Float('Jours acquis',compute='calculer_nbr_jr_acquis',store=True)
    solde_acquis = fields.Float('Acquis/Annee',compute='sum_jrs_acquis',store=True)
    solde_pris = fields.Float('Pris/Année',compute='sum_jrs_acquis',store=True) # lE SOLDE PRIS EST LA SOMME DES CONGÉS PRIS DEPUIS LE DÉBUT DE L'ANNÉE JUSQU'A LE MOIS EN COURS INCLUS (EN PRENANT EN COMPTE LA DATE LIMITE).
    solde_conge = fields.Float('Solde congés',compute='sum_jrs_acquis',store=True)

    arrprec = fields.Float('Arrondi du mois précédent')
    arr_prec = fields.Float(compute='get_arrondi_prec',store=True)
    regul = fields.Boolean('Appliquer régularisations',default=True)
    nbr_mois = fields.Integer('Nombre de mois')
    nbr_payslip = fields.Float(compute='somme_cumul_imposable',store=True)
    nbr_bp = fields.Float(compute='somme_cumul_imposable',store=True)

    somme_impot = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_brut = fields.Float(compute='somme_cumul_imposable',store=True) # la somme trimestrielle du brut sans le mois en cours
    somme_rcar_rc = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_rcar_rg = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_rcar_rc_annuel = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_rcar_rg_annuel = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_brut_annuel = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_rg_fpro = fields.Float(compute='somme_cumul_imposable',store=True)
    somme_fpro = fields.Float(compute='somme_cumul_imposable',store=True)
    fpro_reste = fields.Float(compute='get_fpro_reste',store=True)

    etat_du_lot = fields.Boolean('Etat du lot',compute='get_state')
    comptabilise = fields.Boolean('Comptabilsé', default=False)
    periode = fields.Many2one('account.period','Période',default=get_default_period )
    journal_id= fields.Many2one('account.journal', 'Salary Journal',states={'draft': [('readonly', False)]}, readonly=True, required=True, default=_get_default_journal)

    duree_anciennete = fields.Float('Durée',compute='get_duree',store=True)
    events = fields.One2many('hr.event','event_id')
    rubriques_ids = fields.One2many('hr.payslip.primes','payslip_id')
    readonly = fields.Boolean('Mode lecture seule',compute='get_readonly')

    state = fields.Selection([
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('done', 'Validé'),
            ('cancel', 'Rejected'),], 'Status', select=True, readonly=True, copy=False,)

    @api.model
    def create(self, vals):

        context=self.env.context
        if 'simulation' not in vals or 'simulation' in vals and not vals['simulation']:
            payslip = self.search([('employee_id','=',vals['employee_id']),('periode','=',vals['periode']),('simulation','=',False)])
            if len(payslip)!=0:
                raise exceptions.ValidationError('Vous avez déjà un bulletin de paie de cet employé pour cette période')

        new_record = super(HrPayslip, self).create(vals)
        return new_record






    @api.one
    @api.depends('periode','employee_id','contract_id')
    def get_fpro_reste(self):
        fpro_reste=0
        payslip=self.search([['employee_id','=',self.employee_id.id],['simulation','=',False],['date_from','=',datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)-relativedelta(months=1)]])
        if payslip:
            for rule in payslip[0].details_by_salary_rule_category:
                if rule.code=='fpro_reste':
                    fpro_reste=rule.total
        self.fpro_reste=fpro_reste

    @api.model
    def get_payslip_run_ids(self):
        payslip_run = []
        run_ids = self.env['hr.payslip.run'].search([])
        for r in run_ids:
            if r.date_start == self.date_from and r.state == 'draft' and r.simulation==False:
                payslip_run.append(r.id)
        return [('id', 'in', payslip_run)]

    payslip_run_id = fields.Many2one('hr.payslip.run', 'Payslip Batches', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    #, domain=get_payslip_run_ids)

    @api.multi
    def get_name_of_report(self):
        name= self.employee_id.matricule+'_'+self.employee_id.nom+'_'+self.employee_id.prenom+'_'+self.periode.name
        if self.state=='draft' and self.simulation==False:
            name=name+''+'_Brouillon'
        elif self.simulation:
            name=name+''+'Simulation'
        return name

    def onchange_contract_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        contract_obj = self.pool.get('hr.contract')
        #res = super(HrPayslip, self).onchange_contract_id(cr, uid, ids, date_from=date_from, date_to=date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        return True

    @api.one
    def get_state(self):
        self.ensure_one()
        payslip_state=self.state
        value=True
        batch_state=self.payslip_run_id and self.payslip_run_id.state or False
        if batch_state :
            if batch_state=='close':
                if payslip_state=='done' :
                    value=False
                else :
                    value=True
        self.etat_du_lot=value

    @api.one
    def get_readonly(self):
        self.ensure_one()
        payslip_state=self.state
        value=False
        if payslip_state=='done' :
            value=True
        else :
            value=False
        self.readonly=value

    def draft_payslip(self, cr, uid, ids,*args):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'hr.payslip', p_id, cr)
            wf_service.trg_create(uid, 'hr.payslip', p_id, cr)
        return True

    @api.v7
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(HrPayslip, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for field in res['fields']:
                if field in ('contract_id') :
                    continue
                nodes = doc.xpath("//field[@name='%s']"%field)
                for node in nodes:
                    if not node.get('attrs') :
                        attrs="{ 'readonly':[('readonly','=',True)] }"
                        node.set('attrs',attrs )
                    else :
                        attrs=node.get('attrs')
                        if attrs.find('readonly')==-1:
                            sc=re.sub('[{}]','',attrs)
                            attrs="{"+sc+",'readonly':[ ('readonly','=',True) ] } "
                            node.set('attrs',attrs)
                        else:
                            attrs=attrs.replace('[',"[ '|',").replace("]",",('readonly','=',True)]")
                            node.set('attrs',attrs)
                    setup_modifiers(node, res['fields'][field])
        res['arch'] = etree.tostring(doc)
        return res

    duration=fields.Integer('Jr trav',compute='computeduration',store=True)
    @api.depends('contract_id','periode')
    def computeduration(self):

        self.ensure_one()
        days = 0.0
        if self.contract_id.date_start> self.date_from:
            date_dt = start_date_dt = fields.Date.from_string(self.date_from)
            end_date_dt = fields.Date.from_string(
            self.contract_id.date_start)
            while True:
                if not date_dt.weekday() == 6:
                    days += 1.0
                if date_dt == end_date_dt:
                    break
                date_dt += relativedelta(days=1)
        if days>1:
            self.duration= days-1
        else:
            self.duration=days
        return self.duration

    @api.one
    @api.depends('contract_id','periode')
    def get_nbr_jr_conges_payes(self):
        nbr=0
        emp_holidays = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('periode','=',self.periode.id),('type','=','remove'), ('state','=','validate')])
        for ho in emp_holidays:
            nbr = nbr + ho.number_of_days_temp
        self.nbr_jours = nbr

    api.one
    @api.depends('periode')
    def get_mois_en_cours(self):
        if self.periode:
            mois=datetime.strptime(self.periode.date_start, DEFAULT_SERVER_DATE_FORMAT).month
            self.mois_en_cours=mois
        return True


    # @api.one
    # @api.depends('periode','contract_id')
    # def get_nbr_jr_trav(self):
    #     nbr=0
    #     for l in self.worked_days_line_ids:
    #         nbr=nbr+l.number_of_days
    #     self.nbr_jours_travail=26
    #     return self.nbr_jours_travail
    @api.one
    @api.depends('periode','contract_id')
    def get_nbr_jr_trav(self):
        #Override pour ne pas mettre les jours legaux mais les jours IGR (IR:regul_jr_ir)
        nbr=0
        rule = self.details_by_salary_rule_category.search([('slip_id','=',self.id),('code','=','regul_jr_ir')], limit=1)
        if rule:
            nbr=rule.total
            self.nbr_jours_travail = nbr
        else:
            self.nbr_jours_travail=26
        return self.nbr_jours_travail

    def nbr_jr_conge_pay(self):
        nbr=0
        emp_holidays = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('vacation_date_from','>',self.date_from),('vacation_date_to','<',self.date_to)])
        for ho in emp_holidays:
            nbr=+ho.number_of_days_temp
        return locale.format("%.2f", nbr, grouping=True)

    def get_nbr_jr_rappel_salaire(self):
        nbr = 0
        if self.rubriques_ids:
            for rubrique in self.rubriques_ids:
                if rubrique.name.code == 'rappel_salaire_jrs':
                    nbr = rubrique.montant
        return locale.format("%.2f", nbr, grouping=True)

    @api.one
    @api.depends('periode','employee_id','contract_id')
    def get_fpro_reste(self):
        fpro_reste=0
        payslip=self.search([('employee_id','=',self.employee_id.id),('simulation','=',False),('date_from','=',datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)-relativedelta(months=1))])
        if payslip:
            for rule in payslip[0].details_by_salary_rule_category:
                if rule.code=='fpro_reste':
                    fpro_reste=rule.total
        self.fpro_reste=fpro_reste

    @api.one
    @api.depends('periode', 'employee_id')
    def somme_cumul_imposable(self):
        payslips = self.search([('employee_id', '=', self.employee_id.id), ('simulation', '=', False)])
        pay_year = []
        for p in payslips:
            if datetime.strptime(p.date_from, DEFAULT_SERVER_DATE_FORMAT).year == datetime.strptime(self.date_from,
                                                                                                    DEFAULT_SERVER_DATE_FORMAT).year:
                pay_year.append(p)
        somme_cumul_imposable = 0
        somme_brut = 0
        nbr_bp = 0
        somme_brut_annuel = 0
        somme_rcar_rg_annuel = 0
        somme_rcar_rc_annuel = 0

        somme_ir_payes = 0
        somme_impot = 0
        somme_fpro = 0
        somme_rcar_rc = 0
        somme_rcar_rg = 0
        somme_rg_fpro = 0
        n = 0
        for i in pay_year:
            n += 1
            for k in i.details_by_salary_rule_category:
                if k.code == 'C_IMPR':
                    somme_cumul_imposable += k.total
                elif k.code == 'IRPP':
                    somme_ir_payes += k.total
                elif k.code in ['T1', 'T2', 'T3', 'T4', 'T5']:
                    somme_impot += k.total
                elif k.code == 'FPRO':
                    somme_fpro += k.total
                elif k.code == 'RG_FPRO':
                    somme_rg_fpro += k.total
                elif k.code == 'rcar_rc':
                    somme_rcar_rc_annuel += k.total
                elif k.code == 'rcar_rg':
                    somme_rcar_rg_annuel += k.total
                elif k.code == 'BRUT':
                    somme_brut_annuel += k.total
        month_act = datetime.strptime(self.periode.date_start, DEFAULT_SERVER_DATE_FORMAT).month
        flag = False
        flag2 = False
        if month_act in [3, 6, 9, 12]:
            for i in pay_year:
                mois = datetime.strptime(i.periode.date_start, DEFAULT_SERVER_DATE_FORMAT).month
                if mois == month_act - 2:
                    flag2 = True
                    flag = True
                    nbr_bp = 3
                    for k in i.details_by_salary_rule_category:
                        if k.code == 'rcar_rc':
                            somme_rcar_rc += k.total
                        if k.code == 'rcar_rg':
                            somme_rcar_rg += k.total
                        if k.code == 'BRUT':
                            somme_brut += k.total
                if mois == month_act - 1:
                    flag2 = True
                    for k in i.details_by_salary_rule_category:
                        if k.code == 'rcar_rc':
                            somme_rcar_rc += k.total
                        if k.code == 'rcar_rg':
                            somme_rcar_rg += k.total
                        if k.code == 'BRUT':
                            somme_brut += k.total
                    if not flag:
                        nbr_bp = 2
                if mois == month_act:
                    for k in i.details_by_salary_rule_category:
                        if k.code == 'rcar_rc':
                            somme_rcar_rc += k.total
                        if k.code == 'rcar_rg':
                            somme_rcar_rg += k.total
                        if k.code == 'BRUT':
                            somme_brut += k.total
                    if not flag2:
                        nbr_bp = 1


        elif month_act in [2, 5, 8, 11]:
            for i in pay_year:
                mois = datetime.strptime(i.periode.date_start, DEFAULT_SERVER_DATE_FORMAT).month
                if mois in [month_act - 1]:
                    flag = True
                    nbr_bp = 2
                    for k in i.details_by_salary_rule_category:
                        if k.code == 'rcar_rc':
                            somme_rcar_rc += k.total
                        if k.code == 'rcar_rg':
                            somme_rcar_rg += k.total
                        if k.code == 'BRUT':
                            somme_brut += k.total
                if not flag:
                    nbr_bp = 1

        else:
            for i in pay_year:
                mois = datetime.strptime(i.periode.date_start, DEFAULT_SERVER_DATE_FORMAT).month
                if mois in [month_act]:
                    nbr_bp = 1
                    for k in i.details_by_salary_rule_category:
                        if k.code == 'rcar_rc':
                            somme_rcar_rc += k.total
                        if k.code == 'rcar_rg':
                            somme_rcar_rg += k.total
                        if k.code == 'BRUT':
                            somme_brut += k.total

        self.nbr_bp = nbr_bp
        self.somme_brut = somme_brut
        self.somme_rcar_rc = somme_rcar_rc
        self.somme_rcar_rg = somme_rcar_rg
        self.cumul_imposable = somme_cumul_imposable
        self.nbr_payslip = n
        self.somme_impot = somme_ir_payes
        self.somme_fpro = somme_fpro
        self.somme_rg_fpro = somme_rg_fpro
        self.somme_brut_annuel = somme_brut_annuel
        self.somme_rcar_rc_annuel = somme_rcar_rc_annuel
        self.somme_rcar_rg_annuel = somme_rcar_rg_annuel

    def process_sheet(self):
        return self.write({'paid': True, 'state': 'done'})

    def _get_date_limit(self,payslip_month,payslip_year):
        # Recuperation de la date limite
        date_limite = False
        date_limite_ids = self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite = date_limite_ids[0]
            # Condition pour ajouter le 0 pour les mois 1---9
            if len(str(payslip_month)) == 1:
                date_limite = str(payslip_year) + '-0' + str(payslip_month) + '-' + str(
                    date_limite.date_limite).zfill(2)
            else:
                date_limite = str(payslip_year) + '-' + str(payslip_month) + '-' + str(
                    date_limite.date_limite).zfill(2)
                ##Fin issue
        return date_limite


    @api.one
    @api.depends('worked_days_line_ids','jours_acquis')
    def sum_jrs_acquis(self):
        self.reliquat = reliquat = 0
        self.solde_pris = 0
        self.solde_acquis = 0
        holidays_pool = self.env['hr.holidays']

        if not self.employee_id:
            self.solde_conge = 0
            self.reliquat = 0
        else:
            holidays = holidays_pool.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])
            if holidays:
                periode_payslip = self.env['account.period'].search([('date_start', '=', self.date_from),('special', '=', False)])
                if periode_payslip:
                    periode = periode_payslip[0]
                for hol in holidays:
                    payslip_year = str((datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).year))
                    payslip_month = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).month
                    holiday_name = (hol.holiday_status_id.name).encode('utf-8', 'ignore')
                    date_limit = self._get_date_limit(payslip_month, payslip_year)
                    # Récupération de la date de comptabilisation (si aucune date n'est saisi, Le système prend la date d'ajourd'hui
                    posted_date = hol.posted_date or datetime.now().strftime('%Y-%m-%d')
                    if holiday_name != 'Congés payés ' + str(
                            (datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).year)):
                        reliquat = hol.number_of_days + reliquat
                self.reliquat = reliquat

                # self.solde_conge=holidays[0].current_remaining_leaves
                for holiday in holidays:
                    payslip_year = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).year
                    payslip_month = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).month

                    holiday_year = datetime.strptime(posted_date, DEFAULT_SERVER_DATE_FORMAT).year
                    posted_date = holiday.posted_date or datetime.now().strftime('%Y-%m-%d')
                    date_limit = self._get_date_limit(payslip_month, payslip_year)

                    if holiday.number_of_days < 0:
                        # ICI, ON PARLE DE DEMANDE ET NON PAS D'ATTRIBUTIN

                        if holiday.holiday_status_id.name.encode('utf8') == 'Congés payés ' + str(
                                datetime.strptime(self.date_from,
                                                  DEFAULT_SERVER_DATE_FORMAT).year) and holiday.periode.date_start <= periode.date_start:
                            self.solde_pris = self.solde_pris + holiday.number_of_days_temp
                    else:
                        # fix me PRENDRE EN CONSIDÉRATION LE MOIS DU BULLETIN
                        if holiday.holiday_status_id.name.encode('utf8') == 'Congés payés ' + str(
                                datetime.strptime(self.date_from,
                                                  DEFAULT_SERVER_DATE_FORMAT).year) and holiday.periode.date_start < periode.date_start:
                            self.solde_acquis = self.solde_acquis + holiday.number_of_days
            else:
                self.solde_conge = 0
        # Ajout du nbr de jours ICCP
        payslip_primes = self.rubriques_ids
        nbr_jour_iccp = 0
        for prime in payslip_primes:
            if prime.name.code == 'iccp':
                nbr_jour_iccp = prime.montant

        self.solde_pris += nbr_jour_iccp
        # FIn ajout ICCP

        # Ajout du nbr de jours NJR
        nbr_jour_njr = 0
        for prime in payslip_primes:
            if prime.name.code == 'NJR':
                nbr_jour_njr = prime.montant

        self.solde_pris += nbr_jour_njr
        # FIn ajout NJR

        self.solde_acquis = self.solde_acquis + self.jours_acquis
        self.solde_conge = self.reliquat + self.solde_acquis - self.solde_pris
        return self.solde_conge, self.reliquat

    @api.one
    @api.depends('worked_days_line_ids','periode')
    def sum_jrs_pris(self):
        holidays_pool=self.env['hr.holidays']
        if not self.employee_id:
            self.solde_conge=0
        else:
            holidays=self.env['hr.holidays'].search([['employee_id','=',self.employee_id.id]])
            if holidays:
                self.solde_conge=holidays[0].current_remaining_leaves
            else:
                self.solde_conge=0
        self.solde_conge+=self.jours_acquis
        return self.solde_conge

    @api.one
    @api.depends('worked_days_line_ids','events')
    def calculer_nbr_jr_acquis(self):
        if not self.employee_id:
            self.jours_acquis=0
        else:
            if self.contract_id:
                if not self.contract_id.avenant_ids:
                    self.jours_acquis=self.contract_id.nbr_jr_conge
                else:
                    for a in self.contract_id.avenant_ids:
                        for b in self.contract_id.avenant_ids:
                            print('in eveeeeeeeeeeeeeeeeent')
                            if a.date_end > b.date_end:
                                self.jours_acquis = a.nbr_jr_conge
                            else:
                                self.jours_acquis = b.nbr_jr_conge
                dt=0
                events=self.get_events_impact_conge()
                if events:
                    for e in events:
                        if e.categorie_type_event=='absMaladie' and e.status=='valide' and e.periode.id == self.periode.id:
                            dt+=e.compute_duration()
                    self.jours_acquis-=dt/26
            else:
                self.jours_acquis=0
        return self.jours_acquis

    @api.multi
    @api.onchange('periode')
    def onchange_period(self):
        if self.periode:
            self.date_from=self.periode.date_start
            self.date_to=self.periode.date_stop
            self.primes_variables()


    @api.one
    @api.depends('date_from')
    def get_duree(self):
        #self.ensure_one()
        if self.date_from and self.date_to:
            contrat = self.env['hr.contract'].search([['employee_id', '=', self.employee_id.id], ['date_start', '<=', self.date_from], ['date_end', '>=', self.date_from]])
            if len(contrat) == 1:
                self.contract_id = contrat
                if contrat.date_end < self.date_to:
                    self.date_to = contrat.date_end
                    exceptions.ValidationError('la date fin choisi')

                a= (datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime( self.contract_id.date_anciennetee, DEFAULT_SERVER_DATE_FORMAT)).days/float(366)
                self.duree_anciennete=a
                return self.duree_anciennete
            elif len(contrat) == 0:
                contrat = self.env['hr.contract'].search([['employee_id', '=', self.employee_id.id], ['date_start', '<=',self.date_to], ['date_end', '>=', self.date_from]])
                if len(contrat) == 1:
                    self.contract_id = contrat
                    if contrat.date_start > self.date_from:
                        self.date_from = contrat.date_start
                        exceptions.ValidationError('la date debut choisi')
                else:
                    self.contract_id = self.env['hr.contract']
            else:
                raise exceptions.Warning('err')

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        empolyee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        worked_days_obj = self.pool.get('hr.payslip.worked_days')
        primes_obj=self.pool.get('hr.payslip.primes')
        input_obj = self.pool.get('hr.payslip.input')
        if context is None:
            context = {}
        #delete old worked days lines
        worked_days_ids_to_remove = []
        old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_worked_days_ids:
            #worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)
            worked_days_ids_to_remove = map(lambda x: (2, x,), old_worked_days_ids)
        #delete old input lines
        input_line_ids_to_remove = []
        old_input_ids = ids and input_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_input_ids:
            #input_obj.unlnink(cr, uid, old_input_ids, context=context)
            input_line_ids_to_remove = map(lambda x: (2, x,), old_input_ids)

        #delete old input lines
        primes = ids and primes_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_input_ids:
            primes_obj.unlnink(cr, uid, primes, context=context)
        #defaults
        res = {'value':{
                      'line_ids':[],
                      'input_line_ids': input_line_ids_to_remove,
                      'worked_days_line_ids': worked_days_ids_to_remove,
                      'rubriques_ids':[],
                      'events':[],
                      #'details_by_salary_head':[], TODO put me back
                      'name':'',
                      'contract_id': False,
                      'struct_id': False,
                      }
            }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)
        res['value'].update({
                    'name': _('Bulletin %s %s') % (employee_id.name, tools.ustr(ttyme.strftime('%m/%Y'))),
                    'company_id': employee_id.company_id.id
        })

        if not context.get('contract', False):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
                contract=self.pool.get('hr.contract').browse(cr, uid, contract_ids[0], context=context)

            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)

        if not contract_ids:
            return res
        contract_record = contract_obj.browse(cr, uid, contract_ids[0], context=context)
        res['value'].update({
                    'contract_id': contract_record and contract_record.id or False
        })
        struct_record = contract_record and contract_record.struct_id or False
        if not struct_record:
            return res
        res['value'].update({
                    'struct_id': struct_record.id,
        })
        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
        input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        res['value'].update({
                    'worked_days_line_ids': worked_days_line_ids,
                    'input_line_ids': input_line_ids,
        })

        events=[]
        record=employee_id.event_ids
        for e in record:
            if e.date_debut>= contract_record.date_end or e.date_fin >= contract_record.date_end:
                record=record - e
        for event in record:
            if event.impact_salaire and datetime.strptime(event.periode.date_start, DEFAULT_SERVER_DATE_FORMAT)> datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT):
                record=record - event

        res['value'].update({'events':record})
        return res

    @api.multi
    def compute_sheet(self):
        for i in self._ids:
            pay=self.env['hr.payslip'].browse(i)
            ### Ajour de cette ligne pour mettre a jour le solde de congé lors du calcule de la feuille
            pay.sum_jrs_acquis()
            ###
            pay.cumul_annuel()
            pay.add_event_in_rules()
            sal_base=0
            for rub in pay.rubriques_ids:
                if rub.name.code=='BASE':
                    sal_base=rub.montant
            super(HrPayslip, pay).compute_sheet()
            '''if x:
                for e in x:
                    self.env['hr.payroll.structure'].browse([pay.struct_id.id]).write({'rule_ids': [(3, e, False)]})'''
        return True

    @api.one
    @api.depends('periode', 'employee_id')
    def get_arrondi_prec(self):
        self.arr_prec=0.00
        if self.periode.name=='01/2016':
            self.arr_prec=0
        else:
            bp_precedent=self.search([('employee_id','=',self.employee_id.id),('simulation','=',False)])
            if bp_precedent:
                for b in bp_precedent:
                    if datetime.strptime(b.date_from, DEFAULT_SERVER_DATE_FORMAT).month==datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).month-1:
                        for r in b.details_by_salary_rule_category:
                            if r.code=='arrondiEnCours':
                                self.arr_prec=r.total
                                break
                    break

    @api.multi
    def hr_verify_sheet(self):
        res = super(HrPayslip, self).hr_verify_sheet()
        events=self.env['hr.salary.rule'].search([['code','=',str(self.id)]])
        for evt in events:
            evt.unlink()
        self.check_payroll()
        return res

    @api.multi
    def cumul_annuel(self):
        payslips=self.env['hr.payslip'].search([('employee_id','=',self.employee_id.id),('simulation','=',False)])
        somme_net=0
        for i in payslips:
            for k in i.line_ids:
                if k.code=='NET':
                    somme_net=somme_net+k.total

    @api.multi
    def regul_ir(self):
        payslips=self.env['hr.payslip'].search([('employee_id','=',self.employee_id.id),('simulation','=',False)])
        somme_cumul_imposable=0
        somme_ir_payes=0
        pay_year=[]
        for p in payslips:
            if datetime.strptime(p.date_from, DEFAULT_SERVER_DATE_FORMAT).year == datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).year:
                pay_year.append(p)
        for i in pay_year:
            for k in i.line_ids:
                if k.code=='C_IMPR':
                    somme_cumul_imposable+=k.total
        return somme_cumul_imposable

    def recompute_sheet(self):
        bp_ids=self.search([])
        for bp in bp_ids:
            bp.compute_sheet()

    @api.multi
    def check_payroll(self):
        if self.employee_id:
            payrolls = self.search([['simulation','=',False],['date_from','<=',self.date_from],['date_to','>=',self.date_from],'|',['date_from','<=',self.date_to],['date_to','>=',self.date_to],['employee_id','=',self.employee_id.id],['state','=','done' ]])
            if len(payrolls)>0:
                raise exceptions.Warning('Vous ne pouvez pas avoir deux bulletins validés pour un employé dans la même période!')
            # else:
            #     xs=self.env['hr.holidays'].create({'holiday_type': 'employee','name':'Jours acquis du %s'%self.periode.name, 'number_of_days_temp': self.jours_acquis,'type':'add','employee_id':self.employee_id.id,'state':'cancel','holiday_status_id':1,'posted_date':self.date_to})
            #     workflow.trg_validate(self._uid, 'hr.holidays', xs.id, 'validate', self._cr)

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        resultat = super(HrPayslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=None)
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')
        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        parent_rule_ids=sorted_rule_ids
        for id in sorted_rule_ids:
            rule=rule_obj.browse(cr, uid,id, context=context)
            if rule.parent_rule_id:
                parent_rule_ids.remove(rule.id)
        for id in parent_rule_ids:
            rule=rule_obj.browse(cr, uid,id, context=context)
            if rule.child_ids:
                for child in rule.child_ids:
                    if child.date_debut <= date_from and child.date_fin >= date_to:
                        parent_rule_ids.append(child.id)
                        parent_rule_ids.remove(rule.id)
                        break;
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, parent_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                        inputs = {
                             'name': input.name,
                             'code': input.code,
                             'contract_id': contract.id,
                        }
                        res += [inputs]
        return res

    def get_rib(self):
        rib=0
        if self.employee_id.status=="valide":
            if(self.employee_id.rib_code_ville==False and self.employee_id.rib_code_banque==False) and self.employee_id.rib_code_guichet==False and self.employee_id.rib_numero_de_banque==False and self.employee_id.cle_rib==False:
                rib=' '
            else:
                rib=str(self.employee_id.rib_code_ville)+''+str(self.employee_id.rib_code_banque)+''+str(self.employee_id.rib_code_guichet)+''+str(self.employee_id.rib_numero_de_banque)+''+str(self.employee_id.cle_rib)
        return rib

    def get_nbr_deduction(self):
        rules=self.details_by_salary_rule_category
        nbr_ded=0
        for r in rules:
            if r.code=='NbrPerso':
                nbr_ded=r.total
                break
        return int(nbr_ded)

    def get_nbr_enfant(self):
        nbr_enf=self.employee_id.nbre_enfants
        return int(nbr_enf)

    @api.one
    @api.depends('contract_id','periode')
    def get_salaire_journalier(self):
        salaire_de_base=0
        salaire_par_jour=0
        rubriques=self.rubriques_ids
        for rub in rubriques:
            if str(rub.name.name)=='Salaire de base':
                salaire_de_base=rub.montant
                break
        for rule in self.struct_id.rule_ids:
            if rule['code'] == 'JrTravailParMois':
                nbr_jr_de_travail_par_mois= rule['amount_fix']
                break
        salaire_par_jour = salaire_de_base/nbr_jr_de_travail_par_mois
        self.sal_journalier=salaire_par_jour

    def get_salaire_par_jour(self):
        salaire_de_base=0
        salaire_par_jour=0
        rubriques=self.rubriques_ids
        for rub in rubriques:
            if str(rub.name.name)=='Salaire de base':
                salaire_de_base=rub.montant
                break
        for rule in self.struct_id.rule_ids:
            if rule['code'] == 'JrTravailParMois':
                nbr_jr_de_travail_par_mois= rule['amount_fix']
                break
        salaire_par_jour = salaire_de_base/nbr_jr_de_travail_par_mois
        return locale.format("%.2f", salaire_par_jour, grouping=True)

    def get_base_with_taux(self):
        base_caad = 0
        base_part_sal_sc = 0
        base_partsalsm = 0
        base_rappel_salaire_jrs = 0
        base_rcar_rc = 0
        base_rcar_rg = 0
        base_recore_sal = 0
        base_ANCIENNETE = 0
        base_congpaye2 = 0
        base_iccp = 0
        base_reprcong2 = 0
        base_reprise_absence_irr = 0
        base_stc = 0
        base_congespayes = 0
        base_repriseconge = 0
        base_reprisesalaire = 0
        nombre_reprisesalaire = 0
        nbr_iccp = 0
        nbr_stc = 0
        nbr_reprise_abs_irr = 0
        rub_reprisesalaire = 0
        mont = 0
        base = {'base_caad': 0, 'base_part_sal_sc': 0,
                'base_base_part_sal_sm': 0,
                'base_rappel_salaire_jrs': 0, 'base_rcar_rc': 0,
                'base_rcar_rg': 0, 'base_recore_sal': 0, 'base_ANCIENNETE': 0, 'taux_anciennete': 0, 'base_congpaye2': 0,
                'base_iccp': 0, 'base_reprcong2': 0, 'base_reprise_absence_irr': 0, 'base_stc': 0, 'base_congespayes': 0,
                'base_repriseconge': 0, 'base_reprisesalaire': 0, 'nombre_reprisesalaire': 0,'nbr_jours': 0,'nbr_iccp': 0,'nbr_stc': 0, 'nbr_reprise_abs_irr': 0, 'rub_reprisesalaire': 0}
        rubs=self.details_by_salary_rule_category
        taux_anciennete = 0
        dure_anciennete = self.sudo().get_duree()[0]
        self.sudo().get_nbr_jr_conges_payes()
        self.sudo().get_salaire_journalier()
        nbr_jours = self.nbr_jours
        for r in rubs:
            if r.code=='rappel':
                rappel = r.total
            if r.category_id.code=='HS':
                mont = mont + r.total
        for rub in rubs:
            if rub.code=='caad':
                base_caad = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='part_sal_sc':
                base_part_sal_sc = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='partsalsm':
                base_partsalsm = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='rappel_salaire_jrs':
                base_rappel_salaire_jrs = self.sal_journalier
            if rub.code=='rcar_rc':
                base_rcar_rc = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='rcar_rg':
                base_rcar_rg = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='recore_sal':
                base_recore_sal = rub.total*100/rub.salary_rule_id.taux_rapport
            if rub.code=='ANCIENNETE':
                if dure_anciennete>2 and dure_anciennete<5:
                    taux_anciennete = 5
                elif dure_anciennete>=5 and dure_anciennete<12:
                    taux_anciennete = 10
                elif dure_anciennete>=12 and dure_anciennete<20:
                    taux_anciennete = 15
                elif dure_anciennete>=20 and dure_anciennete<25:
                    taux_anciennete = 20
                elif dure_anciennete>=25:
                    taux_anciennete = 25
                else:
                    taux_anciennete = 0
                if taux_anciennete != 0:
                    base_ANCIENNETE = (rub.total+rappel+mont)*100/taux_anciennete
                else:
                    base_ANCIENNETE = 0
            if rub.code==u'congpayé2':
                base_congpaye2 = self.sal_journalier
            if rub.code=='iccp':
                for r in self.rubriques_ids:
                    if r.name.code == 'iccp':
                        nbr_iccp = r.montant
                if nbr_iccp >0:
                    base_iccp = rub.total/nbr_iccp
            if rub.code=='reprcong2':
                base_reprcong2 = self.sal_journalier
            if rub.code=='reprise_absence_irr':
                base_reprise_absence_irr = self.sal_journalier
                nbr_reprise_abs_irr = rub.total/self.sal_journalier
            if rub.code=='stc':
                for r in self.rubriques_ids:
                    if r.name.code == 'stc':
                        nbr_stc = r.montant
                if nbr_stc > 0:
                    base_stc = rub.total/nbr_stc
            if rub.code=='congespayes':
                base_congespayes = self.sal_journalier
            if rub.code=='repriseconge':
                base_repriseconge = self.sal_journalier
            if rub.code=='reprisesalaire':
                base_reprisesalaire = self.sal_journalier
                nombre_reprisesalaire = abs(rub.total/self.sal_journalier)
                rub_reprisesalaire = abs(rub.total)



        base['base_caad'] = locale.format("%.2f", base_caad, grouping=True)
        base['base_part_sal_sc'] = locale.format("%.2f", base_part_sal_sc, grouping=True)
        base['base_partsalsm'] = locale.format("%.2f", base_partsalsm, grouping=True)
        base['base_rappel_salaire_jrs'] = locale.format("%.2f", base_rappel_salaire_jrs, grouping=True)
        base['base_rcar_rc'] = locale.format("%.2f", base_rcar_rc, grouping=True)
        base['base_rcar_rg'] = locale.format("%.2f", base_rcar_rg, grouping=True)
        base['base_recore_sal'] = locale.format("%.2f", base_recore_sal, grouping=True)
        base['base_ANCIENNETE'] = locale.format("%.2f", base_ANCIENNETE, grouping=True)
        base['taux_anciennete'] = locale.format("%.2f", taux_anciennete, grouping=True)
        base['base_congpaye2'] = locale.format("%.2f", base_congpaye2, grouping=True)
        base['base_iccp'] = locale.format("%.2f", base_iccp, grouping=True)
        base['base_reprcong2'] = locale.format("%.2f", base_reprcong2, grouping=True)
        base['base_reprise_absence_irr'] = locale.format("%.2f", base_reprise_absence_irr, grouping=True)
        base['base_stc'] = locale.format("%.2f", base_stc, grouping=True)
        base['base_congespayes'] = locale.format("%.2f", base_congespayes, grouping=True)
        base['base_repriseconge'] = locale.format("%.2f", base_repriseconge, grouping=True)
        base['base_reprisesalaire'] = locale.format("%.2f", base_reprisesalaire, grouping=True)
        base['nombre_reprisesalaire'] = locale.format("%.2f", nombre_reprisesalaire, grouping=True)
        base['nbr_jours'] = locale.format("%.2f", nbr_jours, grouping=True)
        base['nbr_stc'] = locale.format("%.2f", nbr_stc, grouping=True)
        base['nbr_iccp'] = locale.format("%.2f", nbr_iccp, grouping=True)
        base['nbr_reprise_abs_irr'] = locale.format("%.2f", nbr_reprise_abs_irr, grouping=True)
        base['rub_reprisesalaire'] = locale.format("%.2f", rub_reprisesalaire, grouping=True)

        return base

    def get_cumuls_annuel(self):
        #!!! CETTE METHODE NE DONNE PAS LA BONNE VALEUR SI IL EST POSSIBLE D'AVOIR 2
        # BULLETINS OU PLUS SUR UNE MÊME PÉRIODE (HORS BULLETIN DE SIMULATION)
        cumuls = {
                  'JrTravailParMois': self.nbr_jours_travail,
                  'Net_a_payer': 0,
                  'BrutCNSSma': 0,
                  'Net_imposable': 0,
                  'Charges salariales': 0,
                  'FPRO': 0,
                  'Déd.logement': 0.00,
                  'Déd.charges familiales': 0.00,
                  'cumul_BrutCNSSma': self.brutCNSSma, # modifiable dans le bulletin champs Cumul Brut Imposable
                  'cumul_Net_imposable': self.cumul_Net_imposable, # modifiable dans le bulletin champs Cumul Net Imposable Régul
                  'cumul_Net_imposable_nr': self.cumul_Net_imposable_nr, # modifiable dans le bulletin champs Cumul Net Imposable
                  'cumul_Charges_salariales': self.cumul_Charges_salariales, # modifiable dans le bulletin champs Cumul charges salariales
                  'cumul_FPRO': self.cumul_FPRO, # modifiable dans le bulletin champs Cumul frais professionnels
                  'cumul_Déd.logement': self.cumul_deductions_log, # modifiable dans le bulletin champs Cumul déductions logement
                  'cumul_Déd.charges familiales': self.ded_cachrges_famil, # modifiable dans le bulletin champs Cumul Déd.Charges Familiales
                  'cumul_jours travaillés': 0.00,
                  'code_irpp': 0.00,
                  'cumul_code_irpp': 0.00,
                  'recore_sal': 0.00,
                  'cumul_recore_sal': 0.00,
                  'regul_jr_ir': 0.00,
                  'cumul_jours regul_jr_ir': 0.00
                  }
        # maj cumuls periode et annuel
        for line in self.details_by_salary_rule_category:
            if line.code == 'NbrPerso':
                cumuls['Déd.charges familiales'] = line.total * 30
                cumuls['cumul_Déd.charges familiales'] += line.total * 30
            if line.code == 'NET':
                cumuls['Net_a_payer'] = line.total
            if line.code == 'BRUT':
                cumuls['BrutCNSSma'] = line.total
                cumuls['cumul_BrutCNSSma'] += line.total
            if line.code == 'CS':
                cumuls['Charges salariales'] = line.total
                cumuls['cumul_Charges_salariales'] += line.total
            if line.code == 'FPRO':
                cumuls['FPRO'] = line.total
            if line.code == 'cumul_FPRO':
                cumuls['cumul_FPRO'] = line.total
            if line.code == 'ded_pret_immob':
                cumuls['Déd.logement'] = line.total
                cumuls['cumul_Déd.logement'] += line.total
            if line.code == 'C_IMPR':
                cumuls['Net_imposable'] = line.total
                cumuls['cumul_Net_imposable'] += line.total
            #Ajout le 09/11 ppour le cumul net imposable non régul
            if line.code == 'C_IMP':
                cumuls['cumul_Net_imposable_nr'] += line.total
            #Fin modif
            if line.code == 'cumul_regul_jr_ir':
                cumuls['cumul_jours travaillés'] = line.total
            if line.code == 'regul_jr_ir':
                cumuls['regul_jr_ir'] = line.total
            if line.code == 'IRPP':
                cumuls['code_irpp'] = line.total
            if line.code == 'cumul_IRPP':
                cumuls['cumul_code_irpp'] = line.total
            if line.code == 'recore_sal':
                a = 0
                for l in self.details_by_salary_rule_category:
                    if l.code == 'regul_recore_ps':
                        a = l.total
                cumuls['recore_sal'] = line.total + a
            if line.code == 'cumul_recore_sal':
                cumuls['cumul_recore_sal'] += line.total

        cumuls['cumul_recore_sal'] = locale.format("%.2f", cumuls['cumul_recore_sal'], grouping=True)
        cumuls['recore_sal'] = locale.format("%.2f", cumuls['recore_sal'], grouping=True)
        cumuls['regul_jr_ir'] = locale.format("%.2f", cumuls['regul_jr_ir'], grouping=True)
        cumuls['code_irpp'] = locale.format("%.2f", cumuls['code_irpp'], grouping=True)
        cumuls['cumul_code_irpp'] = locale.format("%.2f", cumuls['cumul_code_irpp'], grouping=True)
        cumuls['Déd.logement']=locale.format("%.2f", cumuls['Déd.logement'], grouping=True)
        cumuls['cumul_BrutCNSSma']=locale.format("%.2f", cumuls['cumul_BrutCNSSma'], grouping=True)
        cumuls['cumul_Déd.charges familiales']=locale.format("%.2f", cumuls['cumul_Déd.charges familiales'], grouping=True)
        cumuls['cumul_FPRO']=locale.format("%.2f", cumuls['cumul_FPRO'], grouping=True)
        cumuls['cumul_jours travaillés']=locale.format("%.2f", cumuls['cumul_jours travaillés'], grouping=True)
        cumuls['cumul_Net_imposable']=locale.format("%.2f", cumuls['cumul_Net_imposable'], grouping=True)
        cumuls['cumul_Net_imposable_nr']=locale.format("%.2f", cumuls['cumul_Net_imposable_nr'], grouping=True)
        cumuls['cumul_Charges_salariales']=locale.format("%.2f", cumuls['cumul_Charges_salariales'], grouping=True)
        cumuls['Déd.charges familiales']=locale.format("%.2f", cumuls['Déd.charges familiales'], grouping=True)
        cumuls['JrTravailParMois']=locale.format("%.2f", cumuls['JrTravailParMois'], grouping=True)
        cumuls['Net_a_payer']=locale.format("%.2f", cumuls['Net_a_payer'], grouping=True)
        cumuls['BrutCNSSma']=locale.format("%.2f", cumuls['BrutCNSSma'], grouping=True)
        cumuls['Charges salariales']=locale.format("%.2f", cumuls['Charges salariales'], grouping=True)
        cumuls['FPRO']=locale.format("%.2f", cumuls['FPRO'], grouping=True)
        cumuls['cumul_Déd.logement']=locale.format("%.2f", cumuls['cumul_Déd.logement'], grouping=True)
        cumuls['Net_imposable']=locale.format("%.2f", cumuls['Net_imposable'], grouping=True)
        return cumuls

    @api.multi
    @api.onchange('struct_id','name','employee_id','periode')
    def primes_variables(self):

        rub_ids=[]
        if self.contract_id:
            avenants=self.contract_id.avenant_ids
            date_payslip_from = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
            date_payslip_to = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
            if avenants:

                self.rubriques_ids=[]
                lol=[]
                for av in avenants:
                    date_limite_ids = self.env['hr.date.event'].search([])
                    date_start_avenant=datetime.strptime(av.date_start, DEFAULT_SERVER_DATE_FORMAT)
                    date_end_avenant=datetime.strptime(av.date_end, DEFAULT_SERVER_DATE_FORMAT)
                    if date_limite_ids:
                        date_limite = date_limite_ids[0]
                        limite=date_limite.date_limite
                        delta = relativedelta(days=int(limite)-1)
                        payslip_date_start = date_payslip_from+delta
                    else:
                        payslip_date_start = date_payslip_from
                    if date_start_avenant<=payslip_date_start and date_end_avenant>=date_payslip_to:
                        rubo=av.rubrique_ids
                        for ri in rubo:
                            lol.append((0,0,{'name':ri.name.id,'montant':ri.montant,'modifiable':True}))
                self.rubriques_ids=lol
                rub_ids=lol
                #return self.rubriques_ids
            else:
                rub=self.env['hr.contract.rubrique'].search([['contract_id','=',self.contract_id.id]])
                for r in rub:
                    rub_ids.append((0,0,{'name':r.name.id,'montant':r.montant,'modifiable':r.modifiable}))
                else:
                    self.rubriques_ids=[]
                    pv=self.env['hr.payslip.primes_variables'].search([['periode','=',self.periode.name]and ['matricule_emlpoyee','=',self.employee_id.matricule]])
                    ap=self.struct_id.rule_ids
                    ap_ap=[]
                    for r in ap:
                        if r.category_id.code=='AP':
                            ap_ap.append(r)
                    ap_ap_name=[]
                    for pc in ap_ap:
                        ap_ap_name.append(pc.name)
                    for pr in pv:
                        if pr.name in ap_ap_name:
                            for pp in ap_ap:
                                if pr.name==pp.name:
                                    rub_ids.append((0,0,{'name':pp.id,'montant':pr.montant,'modifiable':True}))
                    self.rubriques_ids=rub_ids

	#
	# Cette partie concerne la mise à jour de l'onglet Reprise, à isoler dans une méthode séparée
	#
	
	# Initialisation à 0 par défaut des variables qui vont être calculées
        self.nbr_mois = 0
        self.brutCNSSma = 0
        self.cumul_Net_imposable = 0
        self.cumul_Net_imposable_nr = 0
        self.cumul_IRPP = 0
        self.ded_cachrges_famil = 0
        self.cumul_FPRO = 0
	self.cumul_deductions_log = 0
	self.cumul_interet = 0
        self.cumul_jours = 0
        self.cumul_regul_jr_ir = 0
	self.cumul_epargne = 0
	self.cumul_CAAD = 0
	self.cumul_MODEP = 0
	self.cumul_assurance = 0
        self.cumul_Charges_salariales = 0
        self.arrprec = 0
        self.cumul_recore_sal = 0
        self.cumul_cnops = 0
        self.cumul_rcar_rc = 0
        self.cumul_rcar_rg = 0
        self.cumul_tcompma = 0
        self.brutnimposable = 0
	
        if self.employee_id and int(self.mois_en_cours)!=1:
	    # le mois ne cours n'est pas le mois de janvier
	    # on récupère tous les bulletins de l'employé validés qui ne sont pas des simulations et qui sont sur la période actuelle
            payslips=self.search([('employee_id','=',self.employee_id.id),('simulation','=',False),('state','=','done'),('periode','!=',self.periode.id)])
            payslip_prec=[]
	    # on ne garde que les bulletins de l'année actuelle
            for p in payslips:
                if datetime.strptime(p.date_from, DEFAULT_SERVER_DATE_FORMAT).year == datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT).year:
                    payslip_prec.append(p)

            if payslip_prec:
		# il y a une liste de bulletin précédent on prend le premier
		# !! LE CODE SUIVANT FAIT COMME SI CETTE LISTE ETAIT TRIEE CE QUI N'EST PAS FORCEMENT LE CAS !!
                self.payslip_used_for_cumuls = payslip_prec[0] # on considère que c'est le premier bulletin de l'année
                for payslip in payslip_prec:
                    if datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)>datetime.strptime(self.payslip_used_for_cumuls.date_from, DEFAULT_SERVER_DATE_FORMAT) and datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)<datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT):
                        self.payslip_used_for_cumuls = payslip

		# on a récupéré le bulletin précédent on en parcours les détails par catégorie de règle salariales
                self.nbr_mois=self.payslip_used_for_cumuls.nbr_mois+1
                for line in self.payslip_used_for_cumuls.details_by_salary_rule_category:
                    if line.code == 'cumul_BRUT':		self.brutCNSSma = line.total
                    if line.code == 'C_IMPR':			self.cumul_Net_imposable = line.total + self.payslip_used_for_cumuls.cumul_Net_imposable
                    if line.code == 'C_IMP':			self.cumul_Net_imposable_nr = line.total + self.payslip_used_for_cumuls.cumul_Net_imposable_nr
                    if line.code == 'cumul_IRPP':		self.cumul_IRPP = line.total
                    if line.code == 'cumul_NbrPerso':		self.ded_cachrges_famil = line.total
                    if line.code == 'cumul_FPRO':		self.cumul_FPRO = line.total
                    if line.code == 'ded_pret_immob':		self.cumul_deductions_log = line.total + self.payslip_used_for_cumuls.cumul_deductions_log
                    if line.code == 'cumul_ded_interet_pret': 	self.cumul_interet = line.total
                    if line.code == 'regul_ded_pret_immob': 	self.cumul_interet += line.total
                    if line.code == 'cumul_nbr_jrs':		self.cumul_jours = line.total
                    if line.code == 'cumul_regul_jr_ir': 	self.cumul_regul_jr_ir = line.total
                    if line.code == 'cumul_caad': 		self.cumul_CAAD = line.total
                    if line.code == 'cumul_modep': 		self.cumul_MODEP = line.total
                    if line.code == 'cumul_assurance': 		self.cumul_assurance = line.total
                    if line.code == 'cumul_recore_sal':        self.cumul_recore_sal = line.total
                    if line.code == 'cumul_CS': 		self.cumul_Charges_salariales = line.total
                    if line.code == 'arrondiEnCours': 		self.arrprec = line.total
                    if line.code == 'cumul_recore_sal':        self.cumul_recore_sal = line.total
                    if line.code == 'cumul_cnops':        self.cumul_cnops = line.total
                    if line.code == 'cumul_rcar_rc':        self.cumul_rcar_rc = line.total
                    if line.code == 'cumul_rcar_rg':        self.cumul_rcar_rg = line.total
                    if line.code == 'cumul_TCOMPMA':        self.cumul_tcompma = line.total
                    if line.code == 'cumul_BRUTNIMPOSABLE':        self.brutnimposable = line.total
            else:
		# la liste des bulletins précédent est vide
		self.payslip_used_for_cumuls = None
                self.nbr_mois=1
        else:
	    # la liste des bulletins précédent est vide
	    self.payslip_used_for_cumuls = None
            self.nbr_mois=1

	#########
	# cette partie ne concerne plus l'onglet reprise
        indemnites=[]
        name_ind=[]
        if self.employee_id:
            prime_ids=self.env['hr.primes'].search([('employee_id','=',self.employee_id.id),('periode','=',self.periode.id)])
            for prime_id in prime_ids:
                indemnites.append((0,0,{'name':prime_id.rubrique_id.id,'montant':prime_id.montant,'modifiable':True}))
            for ind in indemnites:
                name_ind.append(ind[2]['name'])
            for x in rub_ids:
                if x[2]['name'] in name_ind:
                    rub_ids.remove(x)
        self.rubriques_ids=rub_ids+indemnites

        return self.rubriques_ids

    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, date_from,date_to, context=None):
            mois= '%02d'%datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT).month+'/'+'%02d'%datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT).year
            period=self.pool.get('account.period').search(cr,uid,[('name','=',mois)])
            res = False
            #day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('periode','=',period)])
            if holiday_ids:
                res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
            return holiday_ids

        res = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            attendances = {
                 'name': _("Jours travaillés 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 26.0,
                 'number_of_hours': 191.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            # for day in range(0, nb_of_days):
                #working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                #if working_hours_on_day:
                    #the employee had to work
            leave_type = was_on_leave(contract.employee_id.id,date_from,date_to, context=context)
            if leave_type:
                    #if he was on leave, fill the leaves dict
                    # if not leave_type in leaves:
                for hol in leave_type:
                    hol_id=self.pool.get('hr.holidays').browse(cr, uid, hol, context=context)
                    leaves[hol] = {
                            'name': hol_id.name,
                            'sequence': 5,
                            'code': hol_id.holiday_status_id.name,
                            'number_of_days': hol_id.number_of_days,
                            'number_of_hours': hol_id.number_of_days_temp*191/float(26),
                            'contract_id': contract.id,
                        }
        leaves = [value for key,value in leaves.items()]
        res += [attendances] + leaves
        return res

    def get_all_events_employee_by_contract(self):
        events=self.employee_id.event_ids
        events_in_contract=[]
        for e in events:
            if e.date_debut>=self.contract_id.date_start and e.date_fin <= self.contract_id.date_end:
                events_in_contract.append(e)
        return events_in_contract

    def get_events_impact_conge(self):
        event_impact_conge = self.get_all_events_employee_by_contract()
        for e in event_impact_conge:
            if e.impact_conge==False:
                event_impact_conge.remove(e)
        return event_impact_conge

    def get_events_impact_salaire(self):
        events_impact_salaire=[]
        event_impact_salaire = self.get_all_events_employee_by_contract() and self.get_event_du_mois()
        for e in event_impact_salaire:
            if e.impact_salaire==True:
                events_impact_salaire.append(e)
        return events_impact_salaire

    def get_event_du_mois(self):
        events=[]
        for event in self.get_all_events_employee_by_contract():
            if event.date_debut >= self.date_from:
                events.append(event)
        return events

    #à vérifier
    def get_events_maladie(self):
        events=self.get_all_events_employee_by_contract() and self.get_event_du_mois()
        events_maladie=[]
        for e in events:
            if e.event_type.name=='Maladie' and e.impact_salaire==True and e.deduire_jr_autorise==False:
                events_maladie.append(e)
        return events_maladie

    def get_events_maladie_a_deduire(self):
        events=self.get_all_events_employee_by_contract() and self.get_event_du_mois()
        events_maladie=[]
        for e in events:
            if e.event_type.name=='Maladie' and e.impact_salaire==True and e.deduire_jr_autorise==True:
                events_maladie.append(e)
        return events_maladie

    @api.one
    @api.depends('events','periode')
    def add_event_in_rules(self):
        list_events=[]
        salaire_de_base=0
        rubriques=self.rubriques_ids
        for rub in rubriques:
            if str(rub.name.name)=='Salaire de base':
                salaire_de_base=rub.montant
                break
        nbr_jr_de_travail_par_mois = 1
        nbr_jr_maladie_autorise_par_an = 0
        for rule in self.struct_id.rule_ids:
            if rule['code'] == 'JrTravailParMois':
                nbr_jr_de_travail_par_mois= rule['amount_fix']
            elif rule['code']=='NbrJrAbsAuto':
                nbr_jr_maladie_autorise_par_an=rule['amount_fix']
        salaire_par_jour = salaire_de_base/nbr_jr_de_travail_par_mois
        category = self.env['hr.salary.rule.category'].search([('name','=','Absence/maladie')])
        somme_deduite=self.somme_jr_maladie_a_deuire()
        nbr_jr_restant = nbr_jr_maladie_autorise_par_an-somme_deduite
        somme_du_mois_a_deuire=self.somme_jour_maladie_du_mois_en_cours_a_deduire()
        somme_du_mois = self.somme_jour_maladie_du_mois_en_cours()
        if nbr_jr_restant>=0:
            nbr_jr_restant=nbr_jr_restant-somme_du_mois_a_deuire
            if nbr_jr_restant<0:
                somme_du_mois=somme_du_mois-nbr_jr_restant
                nbr_jr_restant=0
        else:
            somme_du_mois=somme_du_mois+somme_du_mois_a_deuire
        self.nbr_jours_absence=somme_du_mois
        return self.nbr_jours_absence

    def somme_jr_maladie(self):
        somme=0
        events_maladie = self.get_events_maladie()
        for event in events_maladie:
            if event.date_fin<self.date_from:
                somme=somme+event.duree
        return somme

    def somme_jour_maladie_du_mois_en_cours(self):
        somme=0
        events_maladie=self.get_events_maladie()
        for event in events_maladie:
            if event.date_debut>=self.date_from and event.date_fin<=self.date_to:
                somme=somme+event.duree
        return somme

    def somme_jr_maladie_a_deuire(self):
        somme=0
        events_maladie = self.get_events_maladie_a_deduire()
        for event in events_maladie:
            if event.date_fin<self.date_from:
                somme=somme+event.duree
        return somme

    def somme_jour_maladie_du_mois_en_cours_a_deduire(self):
        somme=0
        events_maladie=self.get_events_maladie_a_deduire()
        for event in events_maladie:
            if event.date_debut>=self.date_from and event.date_fin<=self.date_to:
                somme=somme+event.duree
        return somme

class hr_payslip_primes(models.Model):

    _name = 'hr.payslip.primes'
    _inherit = 'hr.contract.rubrique'

    payslip_id = fields.Many2one('hr.payslip','primes')


class hr_payslip_run(models.Model):

    _inherit = 'hr.payslip.run'

    move_id = fields.One2many('account.move', 'lot_de_paie_id', copy=False)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('close', 'Fermé'),
        ], 'Status', select=True, readonly=True, copy=False)


    def get_default_period(self):
        today = datetime.today().date()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        periods = self.env['account.period'].search([['name','=',period]])
        if not periods.state_paie:
            return periods
        else:
            return False
    periode = fields.Many2one('account.period','Période',default=get_default_period)

    @api.multi
    @api.onchange('periode')
    def onchange_period(self):
        if self.periode:
            self.date_start=self.periode.date_start
            self.date_end=self.periode.date_stop
        # else:
        #     raise exceptions.Warning('veuillez choisir une période valide')

    def _get_default_journal(self):
        journals=self.env['account.journal'].search([['code','=','JPaie']])
        return journals or False

    journal_id=fields.Many2one('account.journal', 'Salary Journal', states={'draft': [('readonly', False)]}, readonly=True,default=_get_default_journal,required=True)

    # @api.multi
    # def comptabiliser(self):
    #     period_pool = self.env['account.period']
    #     move_pool = self.env['account.move']
    #     precision = self.env['decimal.precision'].precision_get('Payroll')
    #     timenow = time.strftime('%Y-%m-%d')
    #     period_id = self.periode.id
    #     line_ids = []
    #     debit_sum = 0.0
    #     credit_sum = 0.0
    #     journal_id=self.journal_id.id
    #     #default_partner_id = slip.employee_id.address_home_id.id
    #     #name = _('Payslip of %s') % (slip.employee_id.name)
    #     move = {
    #         #'narration': name,
    #         #'date': timenow,
    #         'ref': self.name,
    #         'journal_id': journal_id,
    #         'period_id': period_id,
    #     }
    #     x_mv=''
    #     if len(self.move_id)>0 :
    #         raise exceptions.Warning('Ce lot est déjà comptabilisé')
    #         for mv in self.move_id:
    #             if mv.state=='draft':
    #                 x_mv=mv
    #                 break
    #     if x_mv:
    #         for lline in x_mv.line_id:
    #             ll_line = (0, 0, {
    #                     'name': lline.name,
    #                     'account_id': lline.account_id.id,
    #                     'journal_id': journal_id,
    #                     'period_id': period_id,
    #                     'debit': lline.debit,
    #                     'credit': lline.credit,
    #                     'analytic_account_id': lline.analytic_account_id,
    #                     'tax_code_id': False,
    #                     'tax_amount': 0.0,
    #                 })
    #             line_ids.append(ll_line)
    #     line_ids_name=[]
    #     for slip in self.slip_ids:
    #         for lin in line_ids:
    #             print lin[2]['name']
    #             line_ids_name.append(lin[2]['name'])
    #         if slip.state=='done' and not slip.comptabilise:
    #             s=self.env['hr.payslip'].browse([slip.id])
    #             for line in slip.details_by_salary_rule_category:
    #                 amt = slip.credit_note and -line.total or line.total
    #                 if float_is_zero(amt, precision_digits=precision):
    #                     continue
    #                 #partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
    #                 debit_account_id = line.salary_rule_id.account_debit.id
    #                 credit_account_id = line.salary_rule_id.account_credit.id
    #                 if debit_account_id:
    #                     debit_line = (0, 0, {
    #                     'name': line.name+' debit',
    #                     #'date': timenow,
    #                     #'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_debit.type in ('receivable', 'payable')) and partner_id or False,
    #                     'account_id': debit_account_id,
    #                     'journal_id': journal_id,
    #                     'period_id': period_id,
    #                     'debit': amt > 0.0 and amt or 0.0,
    #                     'credit': amt < 0.0 and -amt or 0.0,
    #                     'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
    #                     'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
    #                     'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
    #                 })
    #
    #                     if debit_line[2]['name'] not in line_ids_name:
    #                         line_ids.append(debit_line)
    #                         debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
    #                     else:
    #                         for ln in line_ids:
    #                             if ln[2]['name']==debit_line[2]['name']:
    #                                 ln[2]['debit']+=debit_line[2]['debit']
    #                                 ln[2]['credit']+=debit_line[2]['credit']
    #                                 debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
    #                                 break
    #                 if credit_account_id:
    #                     credit_line = (0, 0, {
    #                     'name': line.name+' credit',
    #                     #'date': timenow,
    #                     #'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_credit.type in ('receivable', 'payable')) and partner_id or False,
    #                     'account_id': credit_account_id,
    #                     'journal_id': journal_id,
    #                     'period_id': period_id,
    #                     'debit': amt < 0.0 and -amt or 0.0,
    #                     'credit': amt > 0.0 and amt or 0.0,
    #                     'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
    #                     'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
    #                     'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
    #                 })
    #                     if credit_line[2]['name'] not in line_ids_name:
    #                         line_ids.append(credit_line)
    #                         credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
    #                     else:
    #                         for lnn in line_ids:
    #                             if lnn[2]['name']==credit_line[2]['name']:
    #                                 lnn[2]['debit']+=credit_line[2]['debit']
    #                                 lnn[2]['credit']+=credit_line[2]['credit']
    #                                 credit_sum += credit_line[2]['credit']-credit_line[2]['debit']
    #                                 break
    #             s.write({'comptabilise':True})
    #     if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
    #         acc_id = self.journal_id.default_credit_account_id.id
    #         if not acc_id:
    #             raise exceptions.Warning(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
    #         adjust_credit = (0, 0, {
    #             'name': _('Adjustment Entry'),
    #             'date': timenow,
    #             'partner_id': False,
    #             'account_id': acc_id,
    #             'journal_id': journal_id,
    #             'period_id': period_id,
    #             'debit': 0.0,
    #             'credit': abs(debit_sum - credit_sum),
    #             })
    #         if adjust_credit[2]['name'] not in line_ids_name:
    #             line_ids.append(adjust_credit)
    #         else:
    #             for li in line_ids:
    #                 if li[2]['name']==adjust_credit[2]['name']:
    #                     li[2]['credit']+=adjust_credit[2]['credit']
    #     elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
    #         acc_id = self.journal_id.default_debit_account_id.id
    #         if not acc_id:
    #             raise exceptions.Warning(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
    #         adjust_debit = (0, 0, {
    #             'name': _('Adjustment Entry'),
    #             'date': timenow,
    #             'partner_id': False,
    #             'account_id': acc_id,
    #             'journal_id': journal_id,
    #             'period_id': period_id,
    #             'debit': abs(credit_sum - debit_sum),
    #             'credit': 0.0,
    #             })
    #         if adjust_debit[2]['name'] not in line_ids_name:
    #             line_ids.append(adjust_debit)
    #         else:
    #             for li in line_ids:
    #                 if li[2]['name']==adjust_debit[2]['name']:
    #                     li[2]['debit']+=adjust_debit[2]['debit']
    #     if line_ids:
    #         for line in line_ids:
    #             print line[2]['name'],line[2]['credit'],line[2]['debit']
    #
    #         move.update({'line_id': line_ids})
    #         move_id = move_pool.create(move)
    #         if x_mv:
    #             xx=self.env['account.move'].browse([x_mv.id])
    #             move_line_ids=[]
    #             for n in xx.line_id:
    #                 move_line_ids.append(n.id)
    #             xx.line_id.unlink()
    #             xx.write({'line_id':line_ids})
    #         else:
    #             self.write({'move_id': [(4, move_id.id, False)]})
    #         #self.move_id.append(move_id)
    #         #self.write({'move_id': move_id})
    #         if self.journal_id.entry_posted:
    #             move_pool.post([move_id])
    #     else:
    #         print 'aucun bP validé'
    #         #self.move_id=''
    #     #return super(hr_payslip, self).process_sheet([slip.id])






    @api.multi
    def comptabiliser(self):
        period_pool = self.env['account.period']
        move_pool = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Payroll')
        timenow = time.strftime('%Y-%m-%d')
        period_id = self.periode.id
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        journal_id=self.journal_id.id
        #default_partner_id = slip.employee_id.address_home_id.id
        #name = _('Payslip of %s') % (slip.employee_id.name)
        move = {
            #'narration': name,
            #'date': timenow,
            'ref': self.name,
            'journal_id': journal_id,
            'period_id': period_id,
        }
        x_mv=''
        if len(self.move_id)>0 :
            raise exceptions.Warning('Ce lot est déjà comptabilisé')
            for mv in self.move_id:
                if mv.state=='draft':
                    x_mv=mv
                    break
        if x_mv:
            for lline in x_mv.line_id:
                ll_line = (0, 0, {
                        'name': lline.name,
                        'account_id': lline.account_id.id,
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'debit': lline.debit,
                        'credit': lline.credit,
                        'analytic_account_id': lline.analytic_account_id,
                        'tax_code_id': False,
                        'tax_amount': 0.0,
                    })
                line_ids.append(ll_line)
        line_ids_name=[]
        for slip in self.slip_ids:
            for lin in line_ids:
                line_ids_name.append(lin[2]['name'])
            if slip.state=='done' and not slip.comptabilise:
                s=self.env['hr.payslip'].browse([slip.id])
                for line in slip.details_by_salary_rule_category:

                    partner=False
                    name=False
                    if line.code=='notes_frais':
                        partner=slip.employee_id.user_id.partner_id.id
                        name='Notes de frais '+slip.employee_id.name

                    amt = slip.credit_note and -line.total or line.total
                    if float_is_zero(amt, precision_digits=precision):
                        continue
		                       #partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id
                    if debit_account_id:
                        debit_line = (0, 0, {
                        #'name': line.name+' debit',
			            'name':(name or line.name+' debit'),
                        'partner_id':partner,

			            #'date': timenow,
                        #'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_debit.type in ('receivable', 'payable')) and partner_id or False,
                        'account_id': debit_account_id,
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'debit': amt > 0.0 and amt or 0.0,
                        'credit': amt < 0.0 and -amt or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                        'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                        'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                    })

                        if debit_line[2]['name'] not in line_ids_name:
                            line_ids.append(debit_line)
                            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                        else:
                            for ln in line_ids:
                                if ln[2]['name']==debit_line[2]['name']:
                                    ln[2]['debit']+=debit_line[2]['debit']
                                    ln[2]['credit']+=debit_line[2]['credit']
                                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                                    break
                    if credit_account_id:
                        credit_line = (0, 0, {
                        #'name': line.name+' credit',
			            'name':(name or line.name+' credit'),
			            #'date': timenow,
                        #'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_credit.type in ('receivable', 'payable')) and partner_id or False,
			            'partner_id':partner,
			            'account_id': credit_account_id,
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'debit': amt < 0.0 and -amt or 0.0,
                        'credit': amt > 0.0 and amt or 0.0,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                        'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                        'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                    })
                        if credit_line[2]['name'] not in line_ids_name:
                            line_ids.append(credit_line)
                            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                        else:
                            for lnn in line_ids:
                                if lnn[2]['name']==credit_line[2]['name']:
                                    lnn[2]['debit']+=credit_line[2]['debit']
                                    lnn[2]['credit']+=credit_line[2]['credit']
                                    credit_sum += credit_line[2]['credit']-credit_line[2]['debit']
                                    break
                s.write({'comptabilise':True})
        if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
            acc_id = self.journal_id.default_credit_account_id.id
            if not acc_id:
                raise exceptions.Warning(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
            adjust_credit = (0, 0, {
                'name': _('Adjustment Entry'),
                'date': timenow,
                'partner_id': False,
                'account_id': acc_id,
                'journal_id': journal_id,
                'period_id': period_id,
                'debit': 0.0,
                'credit': abs(debit_sum - credit_sum),
                })
            if adjust_credit[2]['name'] not in line_ids_name:
                line_ids.append(adjust_credit)
            else:
                for li in line_ids:
                    if li[2]['name']==adjust_credit[2]['name']:
                        li[2]['credit']+=adjust_credit[2]['credit']
        elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
            acc_id = self.journal_id.default_debit_account_id.id
            if not acc_id:
                raise exceptions.Warning(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
            adjust_debit = (0, 0, {
                'name': _('Adjustment Entry'),
                'date': timenow,
                'partner_id': False,
                'account_id': acc_id,
                'journal_id': journal_id,
                'period_id': period_id,
                'debit': abs(credit_sum - debit_sum),
                'credit': 0.0,
                })
            if adjust_debit[2]['name'] not in line_ids_name:
                line_ids.append(adjust_debit)
            else:
                for li in line_ids:
                    if li[2]['name']==adjust_debit[2]['name']:
                        li[2]['debit']+=adjust_debit[2]['debit']
        if line_ids:
            for line in line_ids:
                print line[2]['name'],line[2]['credit'],line[2]['debit']

            move.update({'line_id': line_ids})
            move_id = move_pool.create(move)
            if x_mv:
                xx=self.env['account.move'].browse([x_mv.id])
                move_line_ids=[]
                for n in xx.line_id:
                    move_line_ids.append(n.id)
                xx.line_id.unlink()
                xx.write({'line_id':line_ids})
            else:
                self.write({'move_id': [(4, move_id.id, False)]})
            #self.move_id.append(move_id)
            #self.write({'move_id': move_id})
            if self.journal_id.entry_posted:
                move_pool.post([move_id])
        else:
            print 'aucun bP validé'
            #self.move_id=''
        #return super(hr_payslip, self).process_sheet([slip.id])

    @api.multi
    def close_payslip_run(self):
        for slip in self.slip_ids:
            if slip.state!='done':
                raise exceptions.Warning('Veuillez valider tous les bulletin de paie avant de fermer le lot')
        return self.write({'state': 'close'})

class hr_payslip_employees(models.Model):

    _inherit ='hr.payslip.employees'

    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date_start', 'date_end', 'credit_note','journal_id','periode'])[0]
        from_date =  run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)

        journal_id = run_data.get('journal_id',False)[0]
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise exceptions.Warning(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)

            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),

                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
                'journal_id':journal_id,
                'periode':run_data.get('periode',False)[0]
            }
            sl=slip_pool.create(cr, uid, res, context=context)
            sll=slip_pool.browse(cr,uid,[sl],context=context)
            sll.primes_variables()
            slip_ids.append(sl)
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}


    @api.model
    def emp_act(self):
        #period=self.pool.get('hr.payslip.run').read(cr, uid, [context['active_id']], ['periode'])[0]
        emp=[]
        emp_ids=self.env['hr.employee'].search([])
        payslip_run_date_start=self.env['hr.payslip.run'].browse([self._context['active_id']]).date_start
        payslip_run_date_end=self.env['hr.payslip.run'].browse([self._context['active_id']]).date_end
        ######Date limite
        date_limite_ids = self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite = date_limite_ids[0]
            limite = date_limite.date_limite
            delta = relativedelta(days=int(limite) - 1)
            payslip_run_date_start = datetime.strptime(payslip_run_date_start,'%Y-%m-%d').date() + delta
        for e in emp_ids:
            contracts=self.env['hr.contract'].search([['employee_id','=',e.id]])
            for c in contracts:
                if c.date_start<=str(payslip_run_date_start) and c.date_end>=payslip_run_date_end:
                    emp.append(e.id)
                    break
        return [('id','in',emp)]
    employee_ids= fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',domain=emp_act)


class Account_move(models.Model):
    _inherit = 'account.move'

    lot_de_paie_id=fields.Many2one('hr.payslip.run','move_ids')


class PrimesVariables(models.Model):
    _name='hr.payslip.primes_variables'

    name=fields.Char('nom',translate=True)
    periode=fields.Char('Période')
    matricule_emlpoyee=fields.Char('Matricule')
    montant=fields.Float('Montant')

    @api.model
    def create(self,vals):
        emp= self.env['hr.employee'].search([['matricule','=',vals['matricule_emlpoyee']]])
        rules=emp.categorie_id.structure_id.rule_ids
        rules_name=[]
        for r in rules:
            rules_name.append(r.name)
        if vals['name'] in rules_name:
            s=super(PrimesVariables,self).create(vals)
            return s
        else:
            return False


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    def _calculate_total(self, cr, uid, ids, name, args, context):
        if not ids: return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = float(line.quantity) * line.amount * line.rate / 100
        return res

    @api.depends('employee_id')
    def calculate_total_prec(self):
        res = {}
        for i in self:
            bp_prec=self.env['hr.payslip'].search([('employee_id','=',i.employee_id.id),('state','=','done')])
            print bp_prec
            if bp_prec:
                last_bp = bp_prec[0]
                for bp in bp_prec:
                    if bp.date_from > last_bp.date_from:
                        last_bp = bp
                for line in last_bp.details_by_salary_rule_category:
                    if line.code==i.code:
                        i.total_prec=line.total
                        break
                return res
            else:
                return 0.00

    total_prec = fields.Float(compute=calculate_total_prec,string='Total m-1', store=True )
    code_rub = fields.Integer(related='salary_rule_id.code_rub',string='Code rubrique',store=True)
    periode_id = fields.Many2one('account.period', string='Period',
                                 related='slip_id.periode', store=True, readonly=True)

