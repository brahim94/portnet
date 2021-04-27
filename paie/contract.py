# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from openerp import fields, models, api
from openerp import exceptions
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )


class Contract(models.Model):
    _inherit = 'hr.contract'

    rubrique_ids = fields.One2many('hr.contract.rubrique', 'contract_id', 'rubrique')
    horaire_salarie=fields.Char('Horaire du salarié')
    temps_plein=fields.Char('Temps plein/partiel',default='100%', help='Indiquez le pourcentage correspondant au temps travaillé')
    horaire_hebdo=fields.Char('Horaire hebdomadaire')
    duree_essai=fields.Integer('''Durée période d'essai''')
    qualif = fields.Char('Qualification')
    niveau = fields.Char('Niveau')
    coef = fields.Char('Coefficient')
    date_anciennetee=fields.Date('''Date d'ancienneté''',translate=True)
    preavis = fields.Char('Préavis')
    renouvelable = fields.Integer('Renouvelable')
    type_paiement = fields.Selection([('1', 'Mensuel'),('2', 'Annuel')], 'Type de paiment')
    nbr_jr_conge = fields.Float('Nombre de jours de congé/mois', default='1.5', store=True)
    le_13_mois = fields.Boolean('13 ème mois', default=False)
    matricule = fields.Char(related='employee_id.matricule', store=True)
    poste_ids = fields.One2many(related='employee_id.poste_ids')
    actif =fields.Boolean(related='employee_id.active', store=True)
    prime_ids = fields.One2many('prime', 'contrat_id', 'primes')
    postes = fields.Many2one('poste')
    mode_paiement=fields.Selection([
            ('monthly', 'Mensuel'),
            ('quarterly', 'Quarterly'),
            ('semi-annually', 'Semi-annually'),
            ('annually', 'Annuel'),
            ('weekly', 'Weekly'),
            ('bi-weekly', 'Bi-weekly'),
            ('bi-monthly', 'Bi-monthly'),
            ],default= 'monthly', select=True)
    #type_id = fields.Selection([(1,'CDI'),(2,'CDD'),(3,'Stagiaire Anapec'),(4,'Stagiaire PFE'),(5,'Vacataire')],select=True)
    avenant_ids = fields.One2many('avenant', 'contract_id', 'Avenant')
    event_ids = fields.One2many('hr.event','contract_id','Evénements')
    avenants_ids = fields.One2many('hr.contract', 'name', 'Avenant')

    taux_augmentation=fields.Float('''Taux d'augmentation''')
    net_negocie=fields.Float('Net négocié')
    net_augmente=fields.Float(compute='get_net',string='''Net après augmentation''')

    @api.one
    @api.depends('net_negocie','taux_augmentation')
    def get_net(self):
        if self.net_negocie and self.taux_augmentation:
            self.net_augmente=self.taux_augmentation*self.net_negocie/100+self.net_negocie
        else:
            self.net_augmente=0




    #duree_ancienneteee=fields.Integer('Durée',compute='get_duree',store=True)

    _sql_constraints = [
        ('ref_unique','UNIQUE(name)','You can not have two contracts with the same ref !'),
    ]


    @api.multi
    def write(self, vals,):
        print self.avenant_ids
        bp=self.env['hr.payslip'].search([['contract_id','=',self.id]])
        if bp:
            print bp
            super(Contract, self).write(vals)
            #raise exceptions.ValidationError('Vous ne pouvez pas modifié ce contrat car il est déjà utilisé dans un bulletin de paie')
        else:
            super(Contract, self).write(vals)
        return True

    @api.multi
    def add_avenant(self):
        vals= dict(self._context)
        vals1={}
        rub=[]
        for r in self.rubrique_ids:
            print r
            rub.append((0,0,{'name':r.name.id,'montant':r.montant,'modifiable':r.modifiable}))
        print rub
        vals.update({'default_rubrique_ids':rub,'default.qualif':self.qualif,
                     'default_horaire_salarie':self.horaire_salarie,'default_niveau':self.niveau,
                     'default_coef':self.coef,'default_contract_id':self.id,
                     'default_postes':self.postes.id})
        #.update({'rubrique_ids':rub,'employee_id':self.employee_id,'horaire_salarie':'hih'})
        print vals
        print 'vals1 %s' %vals1
        return {
            'name':('Nouveau avenant'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'avenant',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': vals,
            'target': 'new',
            'flags': {'form': {'action_buttons': True}}
            }

    @api.multi
    def edit_avenant(self):
        vals= self._context
        dict(vals).update({'employee_id':self.employee_id})
        return {
            'name':('Avenants'),
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'avenant',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': vals,
            'target': 'new',
            'flags': {'form': {'action_buttons': True}}

            }


    @api.depends('date_start','date_anciennetee')
    def get_duree(self):
        a= (datetime.strptime(self.env['hr.payslip'].date_from, DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(self.date_anciennetee, DEFAULT_SERVER_DATE_FORMAT)).days/365
        self.duree_ancienneteee=a
    '''
    @api.multi
    def avantages(self):
        return {
            'name':('Autres avantages'),
            'view_mode': 'tree',
            'view_id': False,
            'view_type': 'tree',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            }
    '''

    @api.multi
    def autres_primes(self):
        vals = {}
        _form = self.env.ref('paie.primes', False)
        wizard_id = self.env['hr.contract.wizard'].create({'prime_ids': [(6, False, self.prime_ids.ids)]})
        return {
            'name': 'Les primes',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wizard_id.id,
            'target': 'new',
            'views': [(_form.id, 'form')],
            'view_id': '_form.id',
        }

    @api.multi
    @api.onchange('date_start','date_end')
    def set_job(self):
        if self.employee_id:
            if self.date_start<self.postes.date_debut_poste:
                self.date_start=self.postes.date_debut_poste
                return {'warning' :{'title':'Warning','message':"La date de début du contrat ne peut pas être inferieur à la date de début du poste renseigné dans la fiche de l'employé"}}
            elif self.date_end<self.postes.date_fin_poste:
                self.date_end=self.postes.date_fin_poste
                return {'warning' :{'title':'Warning','message':"La date de fin du contrat doit être supérieure au égale à la date de fin de poste renseigné dans la fiche de l'employé"}}

            '''job = self.env['poste'].search([['date_debut_poste','<=',self.date_start],['employee_id','=',self.employee_id.id]])
            if len(job)>1:
                self.job_id=job[-1].job_id
            else:
                self.job_id=job.job_id'''

    @api.multi
    @api.onchange('date_anciennetee')
    def set_anciennetee(self):
        if self.employee_id:
            if self.date_anciennetee>self.postes.date_debut_poste:
                self.date_anciennetee=self.postes.date_debut_poste
                return {'warning': {'title': 'Warning',
                                    'message': "La date d'ancienneté ne peut pas être supérieur à la date de début de poste de l'employé"}}

    @api.multi
    @api.onchange('postes')
    def get_date_start_poste(self):
        self.date_start=self.postes.date_debut_poste
        self.date_end = self.postes.date_fin_poste

    @api.multi
    @api.onchange('type_id')
    def get_date_end_contract(self):
        rubrique_ids1=self.type_id.rubrique_ids
        rub_ids=[]
        value={}
        for i in rubrique_ids1:
            print i.id
            rub_ids.append((0,0,{'name':i.id}))
        self.rubrique_ids=rub_ids
        if (self.type_id.name=='CDI'):
            print 'cdi'
            self.date_end=(datetime.now() + timedelta(days=(25550))).strftime('%Y-%m-%d')
        else:
            self.date_end=self.postes.date_fin_poste

    @api.multi
    @api.onchange('date_start','date_end')
    def check_contract(self):
        if self.employee_id:
            contracts = self.env['hr.contract'].search([['date_start','<=',self.date_start],['date_end','>=',self.date_start],'|',['date_start','<=',self.date_end],['date_end','>=',self.date_end],['employee_id','=',self.employee_id.id]])
            if len(contracts)>0:
                raise exceptions.Warning('''l'employé %s a déjà un contrat pour ce poste!''' %self.employee_id.name)

    @api.model
    def get_postes(self,employee_id):
        postes = self.env['poste'].search([['employee_id', '=', employee_id]])
        return postes

    @api.multi
    @api.onchange('employee_id')
    def onchange_employee_id(self,employee_id):
        if employee_id:
            value = {'postes':""}
            #self.ensure_one()
            super(Contract,self).onchange_employee_id(employee_id)
            domain={'postes':[('id','in',False)]}
            postes_emp=self.env['poste'].search([('employee_id','=',employee_id)])
            postes_emp_ids=[]
            for o in postes_emp:
                postes_emp_ids.append(o.id)
            domain['postes']=[('id','in',postes_emp_ids)]
            return {'value':value,'domain':domain}

    @api.onchange('matricule')
    def onchange_matricule(self):
        i=0
        if self.employee_id:
            self.struct_id=self.employee_id.categorie_id.structure_id
            for rule in self.struct_id.rule_ids:
                if rule['code'] == 'nbrJrConge':
                    self.nbr_jr_conge = rule['amount_fix']
                if rule['code']=='HoraireMaroc':
                    self.horaire_salarie='HoraireMaroc-%s'%int(rule['amount_fix'])
                    i=1
        if i==0 and self.id:
            raise exceptions.ValidationError('Attention la règle salariale HoraireMAroc doit être existante dans votre structure')


    @api.multi
    @api.onchange('struct_id')
    def onchange_struct_id(self):
        if self.struct_id!=self.employee_id.categorie_id.structure_id:
            for rule in self.struct_id.rule_ids:
                if rule['code']=='nbrJrConge':
                    print 'nbrjrConge'
                    self.nbr_jr_conge=rule['amount_fix']
                if rule['code']=='HoraireMaroc':
                    print int(rule['amount_fix'])
                    self.horaire_salarie='HoraireMaroc-%s'%int(rule['amount_fix'])
                    print self.horaire_salarie
            raise exceptions.Warning('''Attention l'employé %s appartient à la catégorie %s'''%(self.employee_id.name ,self.employee_id.categorie_id.name))

    @api.onchange('nbr_jr_conge')
    def onchange_nbr_jr_conge(self):
        jr_conge=0
        for rule in self.struct_id.rule_ids:
            if rule['code']=='nbrJrConge':
                jr_conge=rule['amount_fix']
        if self.nbr_jr_conge<jr_conge:
            self.nbr_jr_conge = jr_conge
            return {'warning' :{'title':'Warning','message':'vous ne pouvez pas mettre une valeur inférieure à celle mentionnée dans la structure'}}

    @api.multi
    def check_trial_dates(self):
        print self
        if self.date_start and self.trial_date_end:
            if self.trial_date_start<self.date_start:
                return False
            return True
        return True

    @api.multi
    def check_trial_dates_period(self):
        print self
        if self.trial_date_start and self.trial_date_end:
            if self.trial_date_end<self.trial_date_start:
                return False
            return True
        return True

    _constraints=[(check_trial_dates_period, '''La date fin de la période d'essai doit être supérieure à date la date de début ''',['trial_date_start','trial_date_end']),
                  (check_trial_dates, '''La période d'essai doit etre avant la période de travail ''',['trial_date_end','date_start'])
                ]

    @api.onchange('duree_essai','trial_date_start')
    def get_date_trial_end(self):
        if self.duree_essai and self.trial_date_start:
            print self.trial_date_start
            print self.duree_essai
            date=datetime.strptime(self.trial_date_start, DEFAULT_SERVER_DATE_FORMAT)
            self.trial_date_end = date+relativedelta(months=self.duree_essai)-relativedelta(days=1)

            #self.trial_date_end=''


class rubriques_contrat(models.Model):
    _name='hr.contract.rubrique'

    name = fields.Many2one('hr.salary.rule','Rubrique',domain="[('negociable','=',True)]")
    montant = fields.Float('Montant')
    modifiable=fields.Boolean('Modifiable sur le bulletin',default=True)
    contract_id = fields.Many2one('hr.contract','Contrat')
    contrat_id = fields.Many2one('hr.payslip','Contrat')
    contrat_avenant_id= fields.Many2one('avenant','Avenant')


class type_contrat(models.Model):
    _inherit = 'hr.contract.type'

    rubrique_ids = fields.One2many('hr.salary.rule','rule_id','Rubriques')
