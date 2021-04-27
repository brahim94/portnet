#-*- coding:utf-8 -*-

from openerp import models, fields, api
from openerp import exceptions


class Holidays(models.Model):
    _name = "hr.holidays"
    _inherit = "hr.holidays"

    def _default_approver(self):
        employee = self.env['hr.employee'].browse(self._employee_get())
        if employee and employee.holidays_approvers:
            if employee.holidays_approvers[0].approver:
                return employee.holidays_approvers[0].approver.id

    pending_approver = fields.Many2one('hr.employee', string="Utilisateur pour la validation", readonly=True, default=_default_approver)
    pending_approver_user = fields.Many2one('res.users', string='Pending approver user', related='pending_approver.user_id', related_sudo=True, store=True, readonly=True)
    current_user_is_approver = fields.Boolean(string= 'Current user is approver', compute='_compute_current_user_is_approver')
    approbations = fields.One2many('hr.employee.holidays.approbation', 'holidays', string='Approvals', readonly=True)
    pending_transfered_approver_user = fields.Many2one('res.users', string='Pending transfered approver user', compute="_compute_pending_transfered_approver_user", search='_search_pending_transfered_approver_user')
    can_reset_holiday = fields.Boolean(compute='onchange_can_reset')

    @api.one
    def onchange_can_reset(self):
        can_reset_holiday=False
        #if self._uid==self.sudo().user_id.id and not self.approbations and self.state=='confirm':
        if self.state=='confirm':
            can_reset_holiday=True
        self.can_reset_holiday=can_reset_holiday
        return self.can_reset_holiday

    def holidays_confirm(self, cr, uid, ids, context=None):
        sel=self.browse(cr, uid, ids, context=context)[0]
        holidays=self.pool.get('hr.holidays').search(cr,uid,[('employee_id','=',sel.employee_id.id),('state','not in',['refuse','validate','draft']),('holiday_status_id','=',sel.holiday_status_id.id)])
        if len(holidays)>1:
            raise exceptions.ValidationError('''Vous avez déjà une demande de congé de ce type qui n'est pas encore validée''')
        a=False
        for record in self.browse(cr, uid, ids, context=context):
            a=record.sudo().pending_approver.id
            #b=record.pending_approver.user_id.id

            if len(record.employee_id.holidays_approvers)==1:
                super(Holidays, record).holidays_confirm()

            #
            # if record.employee_id and record.employee_id.parent_id and record.employee_id.parent_id.user_id:
            #     self.message_subscribe_users(cr, uid, [record.id], user_ids=[record.employee_id.parent_id.user_id.id], context=context)

        return self.write(cr, uid, ids, {'pending_approver':a,'state': 'confirm'})


    @api.multi
    def action_confirm(self):
        super(Holidays, self).action_confirm()
        for holiday in self:
            if holiday.employee_id.holidays_approvers:
                holiday.pending_approver = holiday.employee_id.holidays_approvers[0].approver.id
    
    @api.multi
    def action_approve(self):
        for holiday in self:
            is_last_approbation = False
            sequence = 0
            next_approver = None
            for approver in holiday.employee_id.holidays_approvers:
                sequence = sequence + 1
                if holiday.pending_approver.id == approver.approver.id:
                    if sequence == len(holiday.employee_id.holidays_approvers):
                        is_last_approbation = True
                    else:
                        next_approver = holiday.employee_id.holidays_approvers[sequence].approver
            if is_last_approbation:
                holiday.sudo().action_validate()
                self.sudo()._actualiser_solde()

            else:
                holiday.sudo().write({'state': 'confirm', 'pending_approver': next_approver.id})
                self.env['hr.employee.holidays.approbation'].create({'holidays': holiday.id, 'approver': self.env.uid, 'sequence': sequence, 'date': fields.Datetime.now()})
            
    @api.multi
    def action_validate(self):
        self.write({'pending_approver': None})
        # for holiday in self:
        #     self.env['hr.employee.holidays.approbation'].create({'holidays': holiday.id, 'approver': self.env.uid, 'date': fields.Datetime.now()})
        super(Holidays, self).holidays_validate()

    
    @api.one
    def _compute_current_user_is_approver(self):
        if self.pending_approver.sudo().user_id.id == self.env.user.id or self.pending_approver.sudo().transfer_holidays_approvals_to_user.id == self.env.user.id :
            self.current_user_is_approver = True
        else:
            self.current_user_is_approver = False


    def onchange_employee(self, cr, uid, ids, employee_id):
        pending_approver=False
        emp=self.pool['hr.employee'].browse(cr,uid,employee_id)
        if emp and emp.holidays_approvers:
            pending_approver = self.pool['hr.employee'].browse(cr,uid,emp.holidays_approvers[0].approver.id)
        else:
            pending_approver = False

        result=super(Holidays,self).onchange_employee(cr, uid, ids, employee_id)
        if pending_approver:
            result['value'].update({'pending_approver':pending_approver.id})
        # list=self.pool['hr.holidays.status'].search(cr, uid, [])
        # list_ob=self.pool['hr.holidays.status'].browse(cr, uid, list)
        # default_status=False
        # for l in list_ob:
        #     if default_status:
        #         if l.year and l.year<default_status.year and l.get_days(employee_id)[l.id]['remaining_leaves']!=0:
        #             default_status=l
        #     else:
        #         if l.get_days(employee_id)[l.id]['remaining_leaves']!=0:
        #             default_status=l
        # result.update({'value':{'holiday_status_id':default_status,'pending_approver':pending_approver}})
        return result


            
    @api.one
    def _compute_pending_transfered_approver_user(self):
        self.pending_transfered_approver_user = self.pending_approver.transfer_holidays_approvals_to_user
    
    def _search_pending_transfered_approver_user(self, operator, value):
        replaced_employees = self.env['hr.employee'].search([('transfer_holidays_approvals_to_user', operator, value)])
        employees_ids = []
        for employee in replaced_employees:
            employees_ids.append(employee.id)
        return [('pending_approver', 'in', employees_ids)]


    def check_holidays(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):

            if record.sudo().holiday_type != 'employee' or record.sudo().type != 'remove' or not record.sudo().employee_id or record.sudo().holiday_status_id.limit:
                continue
            leave_days = self.pool.get('hr.holidays.status').get_days(cr, uid, [record.sudo().holiday_status_id.id], record.sudo().employee_id.id, context=context)[record.sudo().holiday_status_id.id]
            if leave_days['remaining_leaves'] < 0 or leave_days['virtual_remaining_leaves'] < 0:
                # Raising a warning gives a more user-friendly feedback than the default constraint error
                raise Warning(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                'Please verify also the leaves waiting for validation.'))
            if record.sudo().holiday_status_id.name=='Congés payés':
                if leave_days['max_leaves']<record.sudo().number_of_days_temp:
                    raise Warning(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                'Please verify also the leaves waiting for validation.'))


        return True



