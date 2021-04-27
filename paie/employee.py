# -*- coding: utf-8 -*-
from openerp import fields, models, api
from datetime import datetime, time, timedelta
from openerp import exceptions
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )


class Employee(models.Model):
    _inherit = 'hr.employee'


    conges_ids=fields.One2many('hr.employee.solde','employee_id','Historique des soldes de congé')
    contrat_compl_ids = fields.One2many('hr.contrat.complementaire','employee_id','événement')

    num_rcar=fields.Integer('N°RCAR')
    num_retraite=fields.Integer('N°Retraite')
    categorie_id=fields.Many2one('hr.employee.categorie','Catégorie employé')
    event_ids = fields.One2many('hr.event','employee_id','événement')
    status = fields.Selection([
        ('brouillon', "Brouillon"),
        ('modifie', "Modifié"),
        ('valide', "Validé"),
        ], default='brouillon')
    # birthday = fields.Date("Date of Birth")
    # adresse_personnelle=fields.Char(related="address_id.street",string="Adresse",store=True)
    # cin = fields.Char(String="CIN")
    # pays_id = fields.Many2one(related='address_id.country_id',string='Pays',store=True)
    # ville = fields.Char(related='address_id.city', string='Ville',store=True)
    # code_postal = fields.Char(related='address_id.zip',string='Code postal',store=True)
    # telephone_fixe = fields.Char(related='address_id.phone',string='Téléphone fixe',store=True)
    # telephone_mobile = fields.Char(related='address_id.mobile',string="Téléphone mobile",store=True)
    # email = fields.Char(related='address_id.email',string='Email',store=True)
    # nbre_enfants  = fields.Integer('''Nombre d'enfants''')
    # lieu_de_naissance = fields.Char('A')
    # date_change_situation_familiale = fields.Date('date')
    birthday = fields.Date("Date of Birth",translate=True)
    adresse_personnelle=fields.Char(related="address_id.street",string="Adresse",store=True)
    cin = fields.Char(String="CIN")
    pays_id = fields.Many2one(related='address_id.country_id',string='Pays',store=True)
    ville = fields.Char(related='address_id.city', string='Ville',store=True)
    code_postal = fields.Char(related='address_id.zip',string='Code postal',store=True)
    telephone_fixe = fields.Char(related='address_id.phone',string='Téléphone fixe',store=True)
    telephone_mobile = fields.Char(related='address_id.mobile',string="Téléphone mobile",store=True)
    email = fields.Char(related='address_id.email',string='Email',store=True)
    nbre_enfants  = fields.Integer('''Nombre d'enfants''')
    lieu_de_naissance = fields.Char('A')
    date_change_situation_familiale = fields.Date('date',translate=True)
    matricule_cnss = fields.Char('matricule cnss')
    niveau_etudes = fields.Selection([('1', 'Bac+5 et plus'), ('2', 'Bac+5'), ('3', 'Bac+4'), ('4', 'Bac+3'),
                                     ('5', 'Bac+2'), ('6', 'Bac'), ('7', 'Niveau Bac'), ('8', 'Secondaire'), ('9', 'Primaire'),
                                     ('10', 'Aucun')], 'niveauu')
    diplome = fields.Char('Diplome')
    carte_sejour = fields.Char('Carte séjour')
    validite = fields.Date('Validité',translate=True)
    contrat = fields.Char('''Contrat de travail d'étranger''')
    date_validite_contrat = fields.Date('Date validité contrat',translate=True)
    enfant_ids = fields.One2many('enfant', 'employee_id', 'Enfants')
    manager = fields.Boolean('Est un responsable')
    property_account_receivable = fields.Many2one(string="Débit", store=True,related='address_id.property_account_receivable')
    property_account_receivable_1 = fields.Many2one(string="Débit", store=True, related='address_id.property_account_receivable')
    property_account_payable = fields.Many2one(string="Crédit", store=True, related='address_id.property_account_payable')
    property_account_payable_1 = fields.Many2one(string="Débit", store=True, related='address_id.property_account_payable')
    mode_de_paiement = fields.Selection([('1','Virement'),('9', 'Chèque'),('3','Espèce')], 'Mode de paiement')
    banque = fields.Selection([('1','Attijariwafa bank'),('2','Banque centrale populaire '),('3','Banque populaire '),
                               ('4','''BANQUE POPULAIRE D'AGADIR-SOUS '''),('5','BANQUE POPULAIRE D’EL JADIDA-SAFI '),
                               ('6','BANQUE POPULAIRE D’OUJDA'),('7','BANQUE POPULAIRE DE CASABLANCA '),('9','''BANQUE POPULAIRE DE FES-TAZA '''),
                               ('10','''BANQUE POPULAIRE DE LAAYOUNE '''),('11','''BANQUE POPULAIRE DE MARRAKECH - BENI MELLAL'''),
                               ('12','''BANQUE POPULAIRE DE MEKNES'''),('13','''BANQUE POPULAIRE DE NADOR-AL HOCEIMA '''),
                               ('14','''BANQUE POPULAIRE DE RABAT-KENITRA '''),('15','''BANQUE POPULAIRE DE TANGER-TETOUAN '''),
                               ('16','''BMCE Bank'''),('17','''BMCI'''),('18','''CFG Bank '''),('19','''CIH Bank'''),
                               ('20','''Crédit agricole du Maroc '''),('21','''Crédit du Maroc '''),('22','''Société générale Maroc'''),('23','''AL Barid Banque''')],'Banque')
    employee_ids = fields.One2many('hr.expense.expense','employee_id', 'Expenses')
    conge_ids = fields.One2many('hr.holidays', 'employee_id', 'Congés')
    name_expense = fields.Char(string='Description',related='employee_ids.name',store=True)
    date = fields.Date(string='Date', related='employee_ids.date',translate=True)
    nom = fields.Char('Nom',translate=True)
    prenom = fields.Char('Prénom',translate=True)
    matricule = fields.Char('Matricule')
    profil = fields.Char('Profil')
    poste_ids = fields.One2many('poste', 'employee_id', 'postes',domain=[])
    #poste_date_debut=fields.Date(related='poste_ids.date_debut')
    date_debut = fields.Date('Date début',translate=True)
    date_fin = fields.Date('Date fin',translate=True)
    code_postal_pro = fields.Char('Code postal')
    adresse_pro = fields.Char('Adresse professionnelle')
    ville_pro = fields.Char('Ville')
    tel_fixe_pro = fields.Char('Téléphone fixe')
    tel_mobile_pro = fields.Char('Téléphone mobile')
    email_pro = fields.Char('Email')
    pays_pro = fields.Many2one('res.country', 'Pays', ondelete='restrict')
    rib_code_ville=fields.Char(size=3)
    rib_code_banque=fields.Char(size=3)
    rib_code_guichet=fields.Char(size=5)
    rib_numero_de_banque=fields.Char(size=11)
    cle_rib=fields.Char(size=2)

    deduire_charges_enfants=fields.Boolean('Déduires charges enfants', default=False)
    executive_manager = fields.Many2one('hr.employee', 'Directeur')

    _sql_constraints = [
        ('cin_unique','UNIQUE(cin)','You can not have two employees with the same cin !'),
        ('matricule_unique','UNIQUE(matricule)','You can not have two employees with the same matricule !')
    ]

    def check_rib(self):
        check_digit={'A':1,'J' : 1,'B':2,'K':2,'S':2,'C':3,'L':3,'T':3,'D':4,'M':4,'U':4,'E':5,'N':5,'V':5,'F':6,'O':6,'W':6,'G':7,'P':7,'X':7,'H':8,'Q':8,'Y':8,'I':9,'R':9,'Z':9}
        if self.mode_de_paiement=='1':
            if self.rib_code_ville!=False and self.rib_code_banque!=False or self.rib_code_guichet!=False or self.cle_rib!=False or self.rib_numero_de_banque!=False:
                if len(self.rib_code_ville)<2 or len(self.rib_code_banque)<3 or len(self.rib_code_guichet)<5 or len(self.cle_rib)<2 or len(self.rib_numero_de_banque)<11:
                    raise exceptions.ValidationError('Veuillez remplir les champs du rib correctemet')

                else:
                    if self.rib_code_ville.isdigit():
                        code_ville=int(self.rib_code_ville)
                    else:
                        code_ville=list(self.rib_code_ville)
                        for l,i in enumerate(self.rib_code_ville):
                            if not i.isdigit():
                                for k in check_digit:
                                    if k==i.upper():
                                        code_ville[l]=str(check_digit[k])
                        code_ville= ''.join(code_ville)
                        code_ville=int(code_ville)
                        print code_ville
                    if self.rib_code_guichet.isdigit():
                        code_guichet=int(self.rib_code_guichet)
                        print 'code guiuchet is %s' %code_guichet
                    else:
                        code_guichet=list(self.rib_code_guichet)
                        for l,i in enumerate(self.rib_code_guichet):
                            if not i.isdigit():
                                for k in check_digit:
                                    if k==i.upper():
                                        code_guichet[l]=str(check_digit[k])
                        code_guichet= ''.join(code_guichet)
                        code_guichet=int(code_guichet)
                        print code_guichet
                    if self.rib_code_banque.isdigit():
                        code_banque=int(self.rib_code_banque)
                    else:
                        code_banque=list(self.rib_code_banque)
                        for l,i in enumerate(self.rib_code_banque):
                            if not i.isdigit():
                                for k in check_digit:
                                    if k==i.upper():
                                        code_banque[l]=str(check_digit[k])
                        code_banque= ''.join(code_banque)
                        code_banque=int(code_banque)
                    if self.cle_rib.isdigit():
                        cle_rib=int(self.cle_rib)
                    else:
                        cle_rib=list(self.cle_rib)
                        for l,i in enumerate(self.cle_rib):
                            if not i.isdigit():
                                for k in check_digit:
                                    if k==i.upper():
                                        cle_rib[l]=str(check_digit[k])
                        cle_rib= ''.join(cle_rib)
                        cle_rib=int(cle_rib)
                    if self.rib_numero_de_banque.isdigit():
                        rib_numero_de_banque=int(self.rib_numero_de_banque)
                    else:
                        rib_numero_de_banque=list(self.rib_numero_de_banque)
                        for l,i in enumerate(self.rib_numero_de_banque):
                            if not i.isdigit():
                                for k in check_digit:
                                    if k==i.upper():
                                        rib_numero_de_banque[l]=str(check_digit[k])
                        rib_numero_de_banque= ''.join(rib_numero_de_banque)
                        rib_numero_de_banque=int(rib_numero_de_banque)
            code_ville_banque=str(code_ville)+''+(str(code_banque))
            sum_rib=97-((89*int(code_ville_banque)+15*code_guichet+3*rib_numero_de_banque)%97)
            if sum_rib!=cle_rib and cle_rib<97 and cle_rib:
                raise exceptions.ValidationError('rib invalide')

    @api.model
    def create(self, vals):
        vals.update({'name': vals.get('nom')+' '+vals.get('prenom')})
        #if vals.get('user_id'):
        context=self.env.context
        user = self.env['res.users'].browse([vals.get('user_id')])
        # user.name=vals.get('name')
        # user.name=vals.get('nom')+' '+vals.get('prenom')
        # user.partner_id.employee = True
        user.phone = vals.get('telephone_fixe')
        user.mobile = vals.get('telephone_mobile')
        user.street = vals.get('adresse_personnelle')
        user.zip = vals.get('code_postal')
        user.email = vals.get('email')
        user.city = vals.get('ville')
        user.country_id = vals.get('pays_id')
        vals.update({'address_id':user.partner_id.id})
        new_record = super(Employee, self).create(vals)
        user.name=new_record.name
        new_record.validation_poste()
        return new_record

    @api.multi
    def write(self, vals,):
        partner = self.env['res.partner'].browse([self.address_id['id']])
        super(Employee, self).write(vals)
        #super(Employee,self).write({'name': self.nom+' '+self.prenom})
        return True

    @api.model
    def _execute_onchange_positions(self):
        monthly_cron=True
        employees=self.env['hr.employee'].search([])
        for emp in employees:
            emp.get_poste()
            print emp.name

    def onchange_user(self, cr, uid, ids, user_id, context=None):
        # email = False
        # phone = False
        # mobile = False
        # street = False
        # zip = False
        # country_id = False
        # city = False
        address_id=False
        if user_id:
             address_id = self.pool.get('res.users').browse(cr, uid, user_id, context=context).partner_id
        #     email = self.pool.get('res.users').browse(cr, uid, user_id, context=context).email
        #     phone = self.pool.get('res.users').browse(cr, uid, user_id, context=context).phone
        #     mobile = self.pool.get('res.users').browse(cr, uid, user_id, context=context).mobile
        #     zip = self.pool.get('res.users').browse(cr, uid, user_id, context=context).zip
        #     street = self.pool.get('res.users').browse(cr, uid, user_id, context=context).street
        #     country_id = self.pool.get('res.users').browse(cr, uid, user_id, context=context).country_id
        #     city = self.pool.get('res.users').browse(cr, uid, user_id, context=context).city
        # return {'value': {'email': email, 'telephone_fixe': phone, 'telephone_mobile': mobile, 'adresse': street,
        #                   'ville': city, 'code_postal': zip, 'pays': country_id,'address_id':address_id}}
        return {'value':{'address_id':address_id}}


    @api.multi
    def validation_poste(self):
        vals={}
        vals['employee_id'] = self.id
        vals['date_fin_poste'] = datetime.strptime(self.date_fin, DEFAULT_SERVER_DATE_FORMAT)
        vals['date_debut_poste'] = datetime.strptime(self.date_debut, DEFAULT_SERVER_DATE_FORMAT)
        vals['moniteur_id'] = self.coach_id.id
        vals['responsable'] = self.manager
        vals['responsable_id'] = self.parent_id.id
        vals['department_id'] = self.department_id.id
        vals['job_id'] = self.job_id.id
        vals['code_postal_pro'] = self.code_postal_pro
        vals['adresse_pro'] = self.adresse_pro
        vals['pays_pro'] = self.pays_pro.id
        vals['tel_mobile_pro'] = self.job_id.id
        vals['tel_fixe_pro'] = self.job_id.id
        vals['ville_pro'] = self.ville_pro
        vals['email_pro'] = self.email_pro
        while vals['date_debut_poste'] > vals['date_fin_poste']:
            raise exceptions.Warning('date fin poste doit etre inférieure à date début poste!')
            return False
        if self.poste_ids:
            if self.date_debut<self.poste_ids[-1].date_fin_poste:
                poste= self.poste_ids[-1]
                poste.write({'date_fin_poste':datetime.strptime(self.date_debut, DEFAULT_SERVER_DATE_FORMAT)-timedelta(days=1)})
        poste_id = self.env['poste'].create(vals)
        self.write({'poste_ids': [(4, poste_id.id, False)]})
        self.status='modifie'
        return True

    @api.multi
    def modification_poste(self):
        vals={}
        vals['employee_id'] = self.id
        vals['date_fin_poste'] = datetime.strptime(self.date_fin, DEFAULT_SERVER_DATE_FORMAT)
        vals['date_debut_poste'] = datetime.strptime(self.date_debut, DEFAULT_SERVER_DATE_FORMAT)
        vals['moniteur_id'] = self.coach_id.id
        vals['responsable'] = self.manager
        vals['responsable_id'] = self.parent_id.id
        vals['department_id'] = self.department_id.id
        vals['job_id'] = self.job_id.id
        while vals['date_debut_poste'] > vals['date_fin_poste']:
            raise exceptions.Warning('date fin poste doit etre inférieure à date début poste!')
            return False
        if self.poste_ids:
            if self.date_debut< self.poste_ids[-1].date_fin_poste:
                poste= self.poste_ids[-1]
                poste.write({'date_fin_poste':datetime.strptime(self.date_debut, DEFAULT_SERVER_DATE_FORMAT)-timedelta(days=1)})
            res = self.poste_ids[-1].write(vals)
        else:
            res = self.poste_ids.write(vals)
        if self.status!='modifie':
            self.status='modifie'
        return res

    @api.multi
    def details_enfants(self):
        _form = self.env.ref('paie.childs_list', False)
        wizard_id = self.env['hr.employee.wizard'].create({'enfant_ids': [(6, False, self.enfant_ids.ids)]})
        return {
            'name': 'Les Enfants',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id':wizard_id.id,
            'target': 'new',
            'views': [(_form.id, 'form')],
            'view_id': '_form.id',
        }


    # @api.onchange('job_id')
    # def onchange_job_id(self):
    #     self.department_id=self.job_id.department_id.id


    @api.multi
    def action_valider(self):
        print self.cin,self.marital,self.nbre_enfants,self.banque,self.mode_de_paiement
        # self.check_rib()
        if self.marital==False or self.nbre_enfants=='' or self.cin==False or self.mode_de_paiement==False or self.banque==False:
            raise exceptions.Warning('''Un ou plusieurs champs obligatoires pour la validation de l'employé ne sont pas renseigné :
            - Situation familiale,
            - Nombre d'enfant,
            - CIN,
            - Banque et mode de paiement''')


        self.status= 'valide'


    """@api.multi
    @api.onchange('date_debut', 'date_fin', 'job_id', 'parent_id', 'department_id', 'coach_id', 'manger')
    def check_change(self):
        return True"""

    @api.one
    @api.onchange('poste_ids')
    def get_poste(self):
        if len(self.poste_ids)>0:
            self.job_id=self.poste_ids[-1].job_id
            self.date_debut=self.poste_ids[-1].date_debut_poste
            self.date_fin=self.poste_ids[-1].date_fin_poste
            self.parent_id=self.poste_ids[-1].responsable_id
            self.department_id=self.poste_ids[-1].department_id
            self.coach_id=self.poste_ids[-1].moniteur_id
            self.manager=self.poste_ids[-1].responsable

            self.code_postal_pro=self.poste_ids[-1].code_postal_pro
            self.adresse_pro=self.poste_ids[-1].adresse_pro
            self.pays_pro=self.poste_ids[-1].pays_pro
            self.tel_mobile_pro=self.poste_ids[-1].tel_mobile_pro
            self.tel_fixe_pro=self.poste_ids[-1].tel_fixe_pro
            self.ville_pro= self.poste_ids[-1].ville_pro
            self.email_pro=self.poste_ids[-1].email_pro
            self.executive_manager=self.poste_ids[-1].executive_manager
        elif len(self.poste_ids)==1:
            self.job_id=self.poste_ids[0].job_id
            self.date_debut=self.poste_ids[0].date_debut_poste
            self.date_fin=self.poste_ids[0].date_fin_poste
            self.parent_id=self.poste_ids[0].responsable_id
            self.department_id=self.poste_ids[0].department_id
            self.coach_id=self.poste_ids[0].moniteur_id
            self.manager=self.poste_ids[0].responsable

            self.code_postal_pro=self.poste_ids[0].code_postal_pro
            self.adresse_pro=self.poste_ids[0].adresse_pro
            self.pays_pro=self.poste_ids[0].pays_pro
            self.tel_mobile_pro=self.poste_ids[0].tel_mobile_pro
            self.tel_fixe_pro=self.poste_ids[0].tel_fixe_pro
            self.ville_pro= self.poste_ids[0].ville_pro
            self.email_pro=self.poste_ids[0].email_pro
            self.executive_manager=self.poste_ids[0].executive_manager
        else:
            self.job_id=''
            self.date_debut=''
            self.date_fin=''
            self.parent_id=''
            self.department_id=''
            self.coach_id=''
            self.manager=''
            self.code_postal_pro=''
            self.adresse_pro=''
            self.pays_pro=''
            self.tel_mobile_pro=''
            self.tel_fixe_pro=''
            self.ville_pro= ''
            self.email_pro=''
            self.executive_manager=''
        return True

class categorie_employe(models.Model):
    _name='hr.employee.categorie'

    name = fields.Char('Catégorie')
    structure_id = fields.Many2one('hr.payroll.structure','Structure salariale')


class contrat_complementaire(models.Model):
    _name='hr.contrat.complementaire'

    type_contrat=fields.Selection([('new','Nouveau'),('old','Ancien'),],string='Type de contrat')
    cotisation_fixe=fields.Boolean('Cotisation mensuelle fixe',default=False)
    montant_retraite=fields.Float('Montant')
    date_effet=fields.Date('''Date d'effet''')
    date_fin_cont_comp=fields.Date('Date fin')
    compte_versement=fields.Char('Compte de versement')
    employee_id=fields.Many2one('hr.employee','employé')


class solde_conge_employe(models.Model):
    _name='hr.employee.solde'

    year = fields.Integer('Année')
    solde = fields.Float('Solde de congé',help="""Le nombre de jours de congés disponibles au titre de l'année saisie. Au moment de la saisie de ce champ:

        - si l'année saisie est une année passée: cela représente le nombre de jours qui sera disponible pour l'année en cours
        - si l'année saisie est l'année actuelle: cela représente le nombre de jours que l'employé peut prendre par "anticipation" sur l'année actuelle.
    
        """)
    # solde_compute = fields.Float('Solde de congé', compute='_execute_compute_solde')
    solde_annuel=fields.Float('Solde annuel',help="""Le nombre de jours de congés "légalement" disponible pour l'année saisie pour cet employé (en prenant en compte par exemple sa date d'embauche)""")
    employee_id=fields.Many2one('hr.employee','employé')


    # def _update_year_history(self,employee,emp_holidays_ids,history_year_id,number_of_days,year):
    #     ##L'ANNÉE COURANTE N'EST PAS PRIS EN CHARGE DANS CETTE METHODE
    #     if history_year_id.year != datetime.now().year:
    #         if history_year_id:
    #             nbr_days = number_of_days
    #             solde_year = history_year_id.solde_annuel
    #              #Il faut prendre en considération la date d'embauche
    #             solde = history_year_id.solde
    #
    #             diff_solde = solde - nbr_days
    #             diff = solde_year - nbr_days
    #             if diff >= 0:
    #                 history_year_id.write({'solde_annuel':diff})
    #                 if diff_solde >= 0:
    #                     history_year_id.write({'solde': diff_solde})
    #                 else:
    #                     history_year_id.write({'solde': 0})
    #                 return True
    #             else:
    #                 history_year_id.write({'solde': 0})
    #                 history_year_id.write({'solde_annuel': 0})
    #                 history_year_after_id = self.search([('employee_id', '=', employee.id), ('year', '=', history_year_id.year+1)])
    #                 self._update_year_history(employee,emp_holidays_ids,history_year_after_id,-diff,year+1)
    #             return False
    #         return False
    #     return False
    #
    # def _verify_number_of_years(self,conges_history):
    #     year_now = datetime.now().year
    #     year_to_delete = []
    #     #Cette fonction permet de ne garder que les soldes de N, N-1 et N-2, Si elle trouve une année de plus, elle supprime la plus anciènne
    #     for conge in conges_history:
    #         if conge.year<year_now-2:
    #             conge.unlink()
    #     return True
    #
    # @api.model
    # # @api.depends('employee_id')
    # def _execute_compute_solde(self):
    #     year_date_now=datetime.now().year
    #     emp=self.env['hr.employee'].search([('id','=',self._context['default_employee_id'])])
    #
    #     # history = self._verify_number_of_years(emp.conges_ids)
    #     # Récupération des congés (demandes et attribution depuis la listes d'historique sur la fiche employé
    #     emp_holidays_ids = emp.conge_ids.search([('employee_id','=',emp.id),('used_in_history','=',False),('state','=','validate'),('type','=','remove')])
    #     nbr_days = 0 #C'est la somme des nombres de jours pris et acquis pour un employee
    #     # Fin récupération
    #     a=0
    #     years=[]
    #     if emp.poste_ids:
    #         nbr_days_year = 0
    #         date_embauche=emp.poste_ids[0].date_debut_poste
    #         conges_ids=emp.conges_ids
    #         nbr_mois=0
    #         for con in conges_ids:
    #             years.append(con.year)
    #         for holiday in emp_holidays_ids:
    #             nbr_days += holiday.number_of_days_temp
    #         #ANNÉE N-2
    #         if year_date_now-2 in years and emp_holidays_ids:
    #             history_year = self.search([('employee_id','=',emp.id),('year','=',year_date_now-2)],limit=1)
    #             self._update_year_history(emp,emp_holidays_ids,history_year,nbr_days,year_date_now-2)
    #         ##ANNÉE N-1
    #         elif year_date_now-1 in years and emp_holidays_ids:
    #             history_year = self.search([('employee_id', '=', emp.id), ('year', '=', year_date_now - 2)],limit=1)
    #             self._update_year_history(emp, emp_holidays_ids, history_year, nbr_days, year_date_now - 2)
    #         ####ANNÉÉ EN COURS
    #         elif year_date_now in years:
    #             nbr_days_year = 0
    #             for holiday in emp_holidays_ids:
    #                 nbr_days_year += holiday.number_of_days_temp
    #             history_year = self.search([('employee_id', '=', emp.id), ('year', '=', year_date_now)], limit=1)
    #             # solde=a*1.75
    #             solde=history_year.solde
    #             # solde_annuel = (12-nbr_mois)*1.75
    #             solde_annuel = history_year.solde_annuel
    #             #SOLDE AVEC PRISE EN COMPTE DES DEMANDE DE CONGÉ
    #             solde = solde - nbr_days_year
    #             solde_annuel = solde_annuel - nbr_days_year
    #             #Récupération de l'année en cours
    #             # history_year = self.search([('employee_id', '=', emp.id), ('year', '=', year_date_now)],limit=1)
    #             history_year.solde=solde
    #             history_year.solde_annuel=solde_annuel
    #         else:
    #             for holiday in emp_holidays_ids:
    #                 nbr_days_year += holiday.number_of_days_temp
    #             if datetime.strptime(date_embauche, DEFAULT_SERVER_DATE_FORMAT)>datetime.strptime(str(year_date_now)+'-01-01', DEFAULT_SERVER_DATE_FORMAT):
    #                 a= (datetime.now() - datetime.strptime(date_embauche, DEFAULT_SERVER_DATE_FORMAT)).days/30
    #             else:
    #                 nbr_mois=datetime.strptime(date_embauche, DEFAULT_SERVER_DATE_FORMAT).month
    #                 a= (datetime.now() - datetime.strptime(str(year_date_now)+'-01-01', DEFAULT_SERVER_DATE_FORMAT)).days/30
    #             solde=a*1.75 - nbr_days_year
    #             solde_annuel=(12-nbr_mois)*1.75 -nbr_days_year
    #             self.create({'employee_id':emp.id,'year':year_date_now,'solde':solde,'solde_annuel':solde_annuel})
    #     for holiday in emp_holidays_ids:
    #         holiday.write({'used_in_history':True})
    #     print "Fin maj historique"
    #     # return True



    @api.model
    def remettre_solde_a_zero(self):
        year_date_now=datetime.now().year
        employees=self.env['hr.employee'].search([])
        for emp in employees:
            conge_ids=emp.conges_ids
            for con in conge_ids:
                if con.year==year_date_now-2:
                    con.solde_annuel=0
                    break
