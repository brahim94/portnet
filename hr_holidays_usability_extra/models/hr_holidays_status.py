# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import datetime


class hr_holidays_status(models.Model):
    _name = 'hr.holidays.status'
    _inherit = 'hr.holidays.status'

    account_id = fields.Many2one(comodel_name="account.analytic.account", string="Compte analytique")
 #spec portnet
    type_holiday = fields.Boolean('Congés payés', default=False)
    year = fields.Selection([(num, str(num)) for num in range(1900, (datetime.now().year) + 1)], 'Année')

    @api.multi
    @api.onchange('year', 'type_holiday')
    def onchange_type_holiday(self):
        if self.type_holiday:
            if self.year:
                self.name = 'Congés payés' + ' ' + str(self.year)
            else:
                self.name = 'Congés payés'


    # @api.model
    # def alert_holidays(self):
    #     list=self.env['hr.holidays.status'].search([['year','=',datetime.now().replace(year=datetime.now().year - 1).year]])
    #     list_ids=[]
    #     for i in list:
    #         list_ids.append(i.id)
    #     self._ids=list_ids
    #     if list:
    #         for obj in self.env['hr.employee'].search([]):
    #             x=self.get_days(obj.id)
    #             post_vars = {'subject': "Message subject", 'body': "Il vous reste %s jours de congé payés de l'année %s"% (x[list_ids[0]]['remaining_leaves'],list[0].year), 'partner_ids': [(4, 3)],}
    #             obj.message_post(type="notification", subtype="mt_comment", **post_vars)

    @api.model
    def alert_holidays(self):
        employee_ids=self.env['hr.employee'].search([])
        #for employee in employee_ids:
        #    for holiday in employee.conges_ids:
        #        if holiday.year==(datetime.now().replace(year=datetime.now().year - 1).year) and holiday.solde>0:
        #            post_vars = {'subject': "Message subject", 'body': "Il vous reste %s jours de congé payés de l'année %s"% (holiday.solde,holiday.year)}
        #            employee.message_post(type="notification", subtype="mt_comment", **post_vars)





    def get_days(self, cr, uid, ids, employee_id, context=None):
        type_holidays_ids=self.pool['hr.holidays.status'].search(cr,uid,[])
        result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
                                virtual_remaining_leaves=0)) for id in type_holidays_ids)
        holiday_ids = self.pool['hr.holidays'].search(cr, uid, [('employee_id', '=', employee_id),
                                                                ('state', 'in',
                                                                 ['confirm', 'validate1', 'validate2', 'validate']),
                                                                ('holiday_status_id', 'in', type_holidays_ids)
                                                                ], context=context)

        type_holidays=self.pool['hr.holidays.status'].browse(cr,uid,type_holidays_ids)
        solde_conges_ids=self.pool['hr.employee.solde'].search(cr,uid,[('employee_id','=',employee_id)])
        solde_conges=self.pool['hr.employee.solde'].browse(cr,uid,solde_conges_ids)
        solde=0
        if solde_conges:
            for sol in solde_conges:

                if sol.year==datetime.today().year or sol.year==datetime.today().year-1:

                    solde+=sol.solde_annuel

        for ty in type_holidays:
            if ty.name=='Congés payés':
                status_dict=result[ty.id]
                status_dict['max_leaves'] =solde
                #status_dict['remaining_leaves']=self.number_of_days_temp

        for holiday in self.pool['hr.holidays'].browse(cr, uid, holiday_ids, context=context):
            status_dict = result[holiday.holiday_status_id.id]
            if holiday.holiday_status_id.name=='Congés payés':
            # #     status_dict['remaining_leaves'] =holiday.number_of_days_temp
                  status_dict['max_leaves']=solde

            # elif holiday.holiday_status_id.year<=datetime.now().replace(year=datetime.now().year - 2).year:
            #     status_dict['max_leaves'] = 0
            if holiday.holiday_status_id.name!='Congés payés':
                if holiday.type == 'add':
                    status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
                    if holiday.state == 'validate':
                        status_dict['max_leaves'] += holiday.number_of_days_temp
                        status_dict['remaining_leaves'] += holiday.number_of_days_temp
                elif holiday.type == 'remove':  # number of days is negative
                    status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
                    if holiday.state == 'validate':
                        status_dict['leaves_taken'] += holiday.number_of_days_temp
                        status_dict['remaining_leaves'] -= holiday.number_of_days_temp
        return result

#end spenc portnet
hr_holidays_status()

