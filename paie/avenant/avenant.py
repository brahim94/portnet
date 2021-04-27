# -*- coding: utf-8 -*-
from openerp import fields, models, api
from openerp import exceptions

class Avenant(models.Model):
    _name = "avenant"

    rubrique_ids = fields.One2many('hr.contract.rubrique','contrat_avenant_id', 'rubrique')
    horaire_salarie=fields.Char('Horaire du salarié')
    temps_plein=fields.Char('Temps plein/partiel',default='100%', help='Indiquez le pourcentage correspondant au temps travaillé')
    horaire_hebdo=fields.Char('Horaire hebdomadaire')
    date_start = fields.Date('Date début')
    date_end = fields.Date('Date fin')
    nbr_jr_conge = fields.Float('Nombre de jours de congé/mois', default='1.5')
    le_13_mois = fields.Boolean('13 ème mois', default=False)
    qualif = fields.Char('Qualification')
    niveau = fields.Char('Niveau')
    coef = fields.Char('Coefficient')
    contract_id = fields.Many2one('hr.contract','Contrat')
    preavis = fields.Char('Préavis')
    working_hours = fields.Many2one('resource.calendar','Nombre H/Semaine de travail')
    struct_id=fields.Many2one('hr.payroll.structure', 'Structure')
    net_negocie=fields.Float('Net négocié')
    piece_jointe= fields.Binary('Pièce Jointe')
    employee_id = fields.Many2one('hr.employee','Employé')



    @api.model
    def create(self, vals):
        if "active_id" in self._context.keys():
            vals.update({'contract_id':self._context['active_id']})
        contract=self.env['hr.contract'].browse(vals.get('contract_id'))
        for avenant in contract.avenant_ids:
            if vals.get('date_start') <= avenant.date_start:
                raise exceptions.Warning('''il y'a déjà un avenant pour cette date ''')
        if vals.get('date_start')< contract.date_start or vals.get('date_end') > contract.date_end:
            raise exceptions.Warning('''vous ne pouvez créer des  avenants que durant la période du contrat''')
        avenant_id=super(Avenant,self).create(vals)
        return avenant_id

    @api.multi
    def write(self,vals):
        if 'active_id' in self._context:
            vals['contract_id']=vals.get('active_id')
            contract=self.env['hr.contract'].browse(self._context['active_id'])
            for avenant in contract.avenant_ids:
                if vals.get('date_start')== avenant.date_start:
                    raise exceptions.Warning('''il y'a déjà un avenant pour cette date ''')
            if vals.get('date_start') < contract.date_start or vals.get('date_end') > contract.date_end:
                raise exceptions.Warning('''vous ne pouvez créer des  avenants que durant la période du contrat''')

        elif self.contract_id:
            for avenant in self.contract_id.avenant_ids:
                if vals.get('date_start') and vals.get('date_start')== avenant.date_start:
                    raise exceptions.Warning('''il y'a déjà un avenant pour cette date ''')
            if vals.get('date_start') and vals.get('date_start')< self.contract_id.date_start or vals.get('date_end')>self.contract_id.date_end:
                raise exceptions.Warning('''vous ne pouvez créer des  avenants que durant la période du contrat''')
        super(Avenant,self).write(vals)
        return True

    @api.multi
    @api.onchange('postes')
    def get_date_start_poste(self):
        self.date_start=self.postes.date_debut_poste
        self.date_end = self.postes.date_fin_poste
        if 'active_id' in self._context:
            if self._context.get('active_model') and self._context.get('active_model') == 'hr.contract':
                contract=self.env['hr.contract'].browse(self._context['active_id'])
                self.struct_id = contract.employee_id.categorie_id.structure_id
            elif self._context.get('active_model') and self._context.get('active_model') == 'hr.employee':
                employee = self.env['hr.employee'].browse(self._context['active_id'])
                self.struct_id = employee.categorie_id.structure_id
            for rule in self.struct_id.rule_ids:
                    if rule['code'] == 'nbrJrConge':
                        self.nbr_jr_conge = rule['amount_fix']
        else:
            return False

    @api.model
    def get_postes(self):
        if 'active_id'in self._context :
            if self._context['active_model']!='hr.employee':
                contract=self.env['hr.contract'].browse(self._context['active_id'])
                postes=contract.employee_id.poste_ids
                po=[]
                for p in postes:
                    if p.date_debut_poste >= contract.date_start and p.date_fin_poste<= contract.date_end:
                        po.append(p.id)
                return [('id','in',po)]
            else:
                return False
        else:
            return False

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        print "######"
        contract = self.contract_id
        if contract and contract.employee_id:
            self.employee_id = contract.employee_id
            self.horaire_salarie = contract.horaire_salarie
            self.horaire_hebdo = contract.horaire_hebdo
            if contract.postes and contract.struct_id:
                self.postes = contract.postes
                self.struct_id = contract.struct_id


    postes = fields.Many2one('poste',domain=get_postes)




