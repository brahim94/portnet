# -*- coding: utf-8 -*-
from openerp import fields, models, api
from datetime import time, datetime
from openerp import exceptions


class HrPoste(models.Model):
    _name = 'poste'

    date_debut_poste = fields.Date('Date début',translate=True)
    date_fin_poste = fields.Date('Date fin',translate=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    job_id = fields.Many2one('hr.job', 'Poste')
    department_id = fields.Many2one('hr.department', 'Departement')
    responsable_id = fields.Many2one('hr.employee', 'Responsable')
    moniteur_id = fields.Many2one('hr.employee', 'Mentor')
    responsable = fields.Boolean('Est un responsable')
    contrat_postes = fields.One2many('hr.contract','postes')
    code_postal_pro = fields.Char('Code postal')
    adresse_pro = fields.Char('Adresse professionnelle')
    ville_pro = fields.Char('Ville')
    tel_fixe_pro = fields.Char('Téléphone fixe')
    tel_mobile_pro = fields.Char('Téléphone mobile')
    email_pro = fields.Char('Email')
    pays_pro = fields.Many2one('res.country', 'Pays', ondelete='restrict')
    executive_manager = fields.Many2one('hr.employee', 'Directeur')


    @api.multi
    @api.onchange('job_id')
    def onchage_job_id(self):
        self.department_id=self.job_id.department_id
        return self.department_id

    @api.multi
    def name_get(self):
        if not len(self._ids):
            return []
        res=[]
        for emp in self.browse(self._ids):
            res.append((emp.id, emp.job_id.name + ',  [' + emp.date_debut_poste +' - '+emp.date_fin_poste+']'))
        return res

    @api.one
    @api.constrains('date_debut_poste','date_fin_poste')
    def _check_dates(self):
        postes= self.search([('employee_id','=',self.employee_id.id)])
        po=[]
        for p in postes:
            if p.date_debut_poste<=self.date_debut_poste<=p.date_fin_poste or p.date_debut_poste<=self.date_fin_poste<=p.date_fin_poste:
                po.append(p)
        if len(po)>1:
            raise exceptions.ValidationError('Vous ne pouvez pas créer des postes pour des périodes qui se chevauchent!')

        if self.date_fin_poste < self.date_debut_poste:
            raise exceptions.ValidationError('La date début du poste doit être inférieure à la date fin du poste!')


    def onchange_department_id(self, cr, uid, ids, department_id, context=None):
        print 'ihiohioho'

        value = {'parent_id': False}
        if department_id:
            department = self.pool.get('hr.department').browse(cr, uid, department_id)
            value['parent_id'] = department.manager_id.id
        return {'value': value}


    @api.multi
    def unlink(self):
        contrats=self.env['hr.contract'].search([['postes','=',self.id]])
        if len(contrats)>0:
            raise exceptions.ValidationError('Vous ne pouvez pas supprimer ce poste car il est lié à un contrat')
        return super(HrPoste,self).unlink()




