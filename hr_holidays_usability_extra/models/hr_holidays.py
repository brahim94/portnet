# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning as UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import logging
from dateutil import parser
from datetime import date, timedelta
from dateutil import rrule
logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _set_remaining_days(self, cr, uid, empl_id, name, value, arg, context=None):
        employee = self.browse(cr, uid, empl_id, context=context)
        diff = value - employee.remaining_leaves
        type_obj = self.pool.get('hr.holidays.status')
        holiday_obj = self.pool.get('hr.holidays')
        # Find for holidays status
        status_ids = type_obj.search(cr, uid, [('limit', '=', False)], context=context)
        if len(status_ids) != 1 :
            raise osv.except_osv(_('Warning!'),_("The feature behind the field 'Remaining Legal Leaves' can only be used when there is only one leave type with the option 'Allow to Override Limit' unchecked. (%s Found). Otherwise, the update is ambiguous as we cannot decide on which leave type the update has to be done. \nYou may prefer to use the classic menus 'Leave Requests' and 'Allocation Requests' located in 'Human Resources \ Leaves' to manage the leave days of the employees if the configuration does not allow to use this field.") % (len(status_ids)))
        status_id = status_ids and status_ids[0] or False
        if not status_id:
            return False
        if diff > 0:
            leave_id = holiday_obj.create(cr, uid, {'name': _('Allocation for %s') % employee.name, 'employee_id': employee.id, 'holiday_status_id': status_id, 'type': 'add', 'holiday_type': 'employee', 'number_of_days_temp': diff}, context=context)
        elif diff < 0:
            raise osv.except_osv(_('Warning!'), _('You cannot reduce validated allocation requests'))
        else:
            return False
        for sig in ('confirm', 'validate','validate2', 'second_validate'):
            holiday_obj.signal_workflow(cr, uid, [leave_id], sig)
        return True

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'To Approve'),
                               ('refuse', 'Refused'), ('validate1', 'Second Approval'), ('validate2', 'Triple Approval'),('validate', 'Approved')],default='draft')
    manager_id1 = fields.Many2one('hr.employee', 'third Approval', invisible=False, readonly=True, copy=False,
                                      help='This area is automatically filled by the user who validate the leave')


    def holidays_reset(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {
            'state': 'draft',
            'manager_id': False,
            'manager_id2': False,
            'manager_id1':False,
        })
        to_unlink = []
        for record in self.browse(cr, uid, ids, context=context):
            for record2 in record.linked_request_ids:
                self.holidays_reset(cr, uid, [record2.id], context=context)
                to_unlink.append(record2.id)
        if to_unlink:
            self.unlink(cr, uid, to_unlink, context=context)
        return True

    def holidays_refuse(self, cr, uid, ids, context=None):

        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        for holiday in self.browse(cr, uid, ids, context=context):
            if holiday.state == 'validate1':
                self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id': manager})
            elif holiday.state == 'validate2':
                self.write(cr,uid,[holiday.id],{'state':'refuse','manager_id1':manager})
            else:
                self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id2': manager})
        self.holidays_cancel(cr, uid, ids, context=context)
        return True

    # def onchange_employee(self, cr, uid, ids, employee_id):
    #     result=super(HrHolidays,self).onchange_employee(cr, uid, ids, employee_id)
    #     list=self.pool['hr.holidays.status'].search(cr, uid, [])
    #     list_ob=self.pool['hr.holidays.status'].browse(cr, uid, list)
    #     default_status=False
    #     for l in list_ob:
    #         if default_status:
    #             if l.year and l.year<default_status.year and l.get_days(employee_id)[l.id]['remaining_leaves']!=0:
    #                 default_status=l
    #         else:
    #             if l.year and l.get_days(employee_id)[l.id]['remaining_leaves']!=0:
    #                 default_status=l
    #     result.update({'value':{'holiday_status_id':default_status}})
    #     return result

    def _needaction_domain_get(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        empids = emp_obj.search(cr, uid, [('parent_id.user_id', '=', uid)], context=context)
        dom = ['&', ('state', '=', 'confirm'), ('employee_id', 'in', empids)]
        # if this user is a hr.manager, he should do second validations
        if self.pool.get('res.users').has_group(cr, uid, 'base.group_hr_manager'):
            dom = ['|'] + dom + [('state', '=', 'validate1'),('state','=','validate2')]
        return dom
    ##
    def holidays_second_validate(self, cr, uid, ids, context=None):
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        #self.holidays_first_validate_notificate(cr, uid, ids, context=context)
        return self.write(cr, uid, ids, {'state':'validate2', 'manager_id': manager})

    @api.model
    def create(self, vals):
        context = dict(self._context, mail_create_nolog=True)
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not self.env['res.users'].has_group('base.group_hr_user'):
            raise osv.except_osv(_('Warning!'), _('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % vals.get('state'))
        obj = super(HrHolidays, self).create(vals)
        # obj= osv.osv.create(self,vals)
        # if obj.state == 'draft':
        #     obj.write({'state':'validate'})
        if obj.type == 'remove':
            days = obj._compute_number_of_days()
            obj.number_of_days_temp = days
        return obj



    def _actualiser_solde(self):
        soldes=self.employee_id.conges_ids
        year_date_now=datetime.now().year
        last_year=year_date_now-1
        duree=self.number_of_days_temp
        reste=duree

        for y in soldes:
            if y.year==last_year:
                if y.solde>0:
                    if y.solde>=duree:
                        y.solde=y.solde-duree
                        y.solde_annuel=y.solde-duree
                        reste=0
                        break
                    else:
                        reste=duree-y.solde
                        y.solde=0
                        y.solde_annuel=0

                        break
        if reste!=0:
            for y in soldes:
                if y.year==year_date_now:
                    y.solde=y.solde-reste
                    y.solde_annuel=y.solde_annuel-reste
                    break