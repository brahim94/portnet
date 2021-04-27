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
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    )


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    add_validation_manager = fields.Boolean(
        string='Allocation validated by HR Manager',
        help="If enabled, allocation requests for this leave type "
        "can be validated only by an HR Manager "
        "(not possible by an HR Officer).")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    holiday_exclude_mass_allocation = fields.Boolean(
        string='Exclude from Mass Holiday Attribution')

    ##################################MAJ historique des congé

    def _update_year_history(self,employee,history_year_id,number_of_days,year):
        if history_year_id:
            nbr_days = number_of_days
            solde_year = history_year_id.solde_annuel
            solde = history_year_id.solde

            diff_solde = solde - nbr_days
            diff = solde_year - nbr_days
            if diff >= 0:
                history_year_id.write({'solde_annuel':diff})
                if diff_solde >= 0:
                    history_year_id.write({'solde': diff_solde})
                else:
                    history_year_id.write({'solde': 0})
                return True
            else:
                history_year_id.write({'solde': 0})
                history_year_id.write({'solde_annuel': 0})
                history_year_after_id = self.env['hr.employee.solde'].search([('employee_id', '=', employee.id), ('year', '=', history_year_id.year+1)])
                self._update_year_history(employee,history_year_after_id,-diff,year+1)
            return False
        return False

    def initialize_for_one_employee(self,emp):
        print "EMPLOYEE", emp.name
        hr_employee_solde = self.env['hr.employee.solde']
        solde = 0
        solde_annuel = 0
        nbr_days = 1.75
        nbr_days_per_year = 21
        year_n = datetime.now().year
        year_n_1 = datetime.now().year - 1
        year_n_2 = datetime.now().year - 2
        month_n = datetime.now().month
        date_embauche = datetime.strptime(emp.date_debut, DEFAULT_SERVER_DATE_FORMAT).date()
        date_embauche_year = date_embauche.year
        month_embauche = date_embauche.month
        emp_holidays_ids = self.env['hr.holidays'].search(
            [('employee_id', '=', emp.id), ('state', '=', 'validate'),
             ('type', '=', 'remove')])
        for holiday in emp_holidays_ids:
            holiday.write({'used_in_history': False})
        if emp.conges_ids:
            for conge in emp.conges_ids:
                conge.unlink()
        if date_embauche_year == year_n_2:
            solde = (12 - month_embauche +1 )* nbr_days
            solde_annuel = (12 - month_embauche + 1)* nbr_days
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': solde_annuel, 'solde': solde, 'year': year_n_2})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': 21, 'year': year_n_1})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': month_n * nbr_days, 'year': year_n})

        elif date_embauche_year == year_n_1:
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': 0, 'solde': 0,
                 'year': year_n_2})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': nbr_days_per_year,
                 'year': year_n_1})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': month_n * nbr_days, 'year': year_n})

        elif date_embauche_year == year_n:
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': 21, 'year': year_n_2})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': 21, 'year': year_n_1})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': nbr_days_per_year, 'solde': month_n * nbr_days, 'year': year_n})
        else:
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': 21, 'solde': 21, 'year': year_n_2})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': 21, 'solde': 21, 'year': year_n_1})
            hr_employee_solde.create(
                {'employee_id': emp.id, 'solde_annuel': 21, 'solde': month_n * nbr_days, 'year': year_n})

        return True

    @api.multi
    def button_initialize_history(self):
        for emp in self.search([]):
            emp.initialize_for_one_employee(emp)
        return True

    def calcul_solde(self,employee,year):
        hr_employee_solde = self.env['hr.employee.solde']
        solde = 0
        solde_annuel = 0
        nbr_days = 1.75
        nbr_days_per_year = 21
        date_embauche = self.date_debut
        date_embauche_year = date_embauche.year

        if date_embauche_year == year:
            month_embauche = date_embauche.month
            solde = (12 - month_embauche + 1)*nbr_days
            solde_annuel = (12 - month_embauche+1)*nbr_days
            hr_employee_solde.create({'employee_id':employee.id,'solde_annuel':solde_annuel,'solde':solde,'year':year_n_1})
        else:
            hr_employee_solde.create({'employee_id':employee.id,'solde_annuel':nbr_days_per_year,'solde':nbr_days_per_year,'year':year_n_1})
        return True


    def _verify_number_of_years(self, employee,conges_history):
        list_years =[]
        hr_employee_solde = self.env['hr.employee.solde']
        year_now = datetime.now().year
        year_to_delete = []
        # Cette fonction permet de ne garder que les soldes de N, N-1 et N-2, Si elle trouve une année de plus, elle supprime la plus anciènne
        for conge in conges_history:
            if conge.year < year_now - 2:
                conge.unlink()
            else:
                list_years.append(conge.year)
        #Ferifier l'année N, N-1 et N-2
        year_n_1 = year_now -1
        year_n_2 = year_now - 2
        if year_n_1 not in list_years or year_n_2 not in list_years or year_now not in list_years:
            self.initialize_for_one_employee(employee)

        return True

    @api.multi
    def button_holidays_history(self):
        hr_employee_solde = self.env['hr.employee.solde']
        year_n_2 = datetime.now().year -2
        year_n_1 = datetime.now().year -1
        for emp in self.search([]):
            #Verifie que le système et bien configurer avant de lancer le calcule
            self._verify_number_of_years(emp,emp.conges_ids)
            # Récupération des congés (demandes et attribution) de l'employee non envore utilisé dans le calcul de l'historique
            emp_holidays_ids = self.env['hr.holidays'].search(
                [('employee_id', '=', emp.id), ('used_in_history', '=', False), ('state', '=', 'validate'),
                 ('type', '=', 'remove')])
            nbr_days = 0  # C'est la somme des nombres de jours pris et acquis pour un employee
            # Fin récupération
            a = 0
            years = []
            if emp.poste_ids:
                nbr_days_year = 0
                date_embauche = emp.poste_ids[0].date_debut_poste
                conges_ids = emp.conges_ids
                nbr_mois = 0
                for con in conges_ids:
                    years.append(con.year)
                for holiday in emp_holidays_ids:
                    nbr_days += holiday.number_of_days_temp
                # ANNÉE N-2
                if year_n_2 in years:
                    history_year = hr_employee_solde.search([('employee_id', '=', emp.id), ('year', '=', year_n_2)], limit=1)
                    self._update_year_history(emp, history_year, nbr_days, year_n_2)
                elif year_n_1 in years:
                    history_year = hr_employee_solde.search([('employee_id', '=', emp.id), ('year', '=', year_n_2)],
                                                            limit=1)
                    self._update_year_history(emp, history_year, nbr_days, year_n_1)
                else:
                    history_year = hr_employee_solde.search([('employee_id', '=', emp.id), ('year', '=', year_n_2)],
                                                            limit=1)
                    emp.initialize_for_one_employee(emp)
                    self._update_year_history(emp, history_year, nbr_days, year_n_2)
            # taguer les congé utilisé
            for holiday in emp_holidays_ids:
                holiday.write({'used_in_history': True})
            print "Fin maj historique 2"
            # return True

            ###FIn maj




class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
    _order = 'type desc, date_from desc'

    def get_default_period(self):
        today = datetime.today()
        period =today.strftime("%m")+'/'+today.strftime("%Y")

        date_limite_ids=self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite=date_limite_ids[0]
            date_limite=str(datetime.today().year)+'-'+str(datetime.today().month)+'-'+str(date_limite.date_limite).zfill(2)

        next_period=str(today.month+1).zfill(2)+'/'+today.strftime("%Y")
        if date_limite and today<= datetime.strptime(date_limite, DEFAULT_SERVER_DATE_FORMAT) :
            periods = self.env['account.period'].search([['name','=',period]])
        else:
            periods=periods = self.env['account.period'].search([['name','=',next_period]])
        return periods or False

    # def get_default_period(self):
    #     today = datetime.today().date()
    #     period =today.strftime("%m")+'/'+today.strftime("%Y")
    #     periods = self.env['account.period'].search([['name','=',period]])
    #     return periods or False

    def get_periods(self):

        today = datetime.today()
        period =today.strftime("%m")+'/'+today.strftime("%Y")
        date_limite_ids=self.env['hr.date.event'].search([])
        if date_limite_ids:
            date_limite=date_limite_ids[0]
            date_limite=str(datetime.today().year)+'-'+str(datetime.today().month)+'-'+str(date_limite.date_limite).zfill(2)
        year = today.year
        month = today.month
        if today.month+1>12:
            month=0
            year=year + 1
        next_period=str(today.month+1).zfill(2)+'/'+today.strftime("%Y")
        if date_limite and today<= datetime.strptime(date_limite, DEFAULT_SERVER_DATE_FORMAT) :
            periods = self.env['account.period'].search([['name','=',period]])
        else:
            periods = self.env['account.period'].search([['name','=',next_period]])
        periods = self.env['account.period'].search([['date_start','>=',periods[0].date_start]])
        return [('id','in',periods.ids)]


    # def get_periods(self):
    #     date_limite_ids=self.env['hr.date.event']
    #
    #     today = datetime.today().date()
    #     period =today.strftime("%m")+'/'+today.strftime("%Y")
    #     period_id = self.env['account.period'].search([['name','=',period]])
    #     periods = self.env['account.period'].search([['date_start','>=',period_id.date_start]])
    #     period_ids=[]
    #     for p in periods:
    #         period_ids.append(p.id)
    #     return [('id','in',period_ids)]

    timesheets_create = fields.Boolean(string="Générer les feuilles de temps associées ?", default=True)
    include_saturday = fields.Boolean(string="Inclure les samedis ?", default=False)
    include_sunday = fields.Boolean(string="Inclure les dimanches ?", default=False)
    include_days_off = fields.Boolean(string="Inclure les jours fériés ?")
    double_validation = fields.Boolean(string="",related ="holiday_status_id.double_validation")
    periode = fields.Many2one('account.period','Période',default=get_default_period,)#domain=get_periods)
    # POUR LE CALCULE DE L'HISTORIQUE SUR LA FICHE EMPLOYÉ
    used_in_history = fields.Boolean(String="Utilisé dans l'historique", default=False)


    @api.model
    def _compute_number_of_days(self):
        hhpo = self.env['hr.holidays.public']
        days = 0.0

        if (
                self.type == 'remove' and
                self.holiday_type == 'employee' and
                self.vacation_date_from and
                self.vacation_time_from and
                self.vacation_date_to and
                self.vacation_time_to):

            date_dt = start_date_dt = fields.Date.from_string(
                self.vacation_date_from)
            end_date_dt = fields.Date.from_string(
                self.vacation_date_to)
            if end_date_dt < date_dt:
                self.vacation_date_to = False
                raise ValidationError(
                    _('The first day cannot be after the last day !'))

            while True:
                if hhpo.is_public_holiday(date_dt) and not self.include_days_off:
                    logger.info(
                        "%s is a bank holiday, don't count", date_dt)
                elif date_dt.weekday() == 5 and not self.include_saturday:
                    logger.info(
                        "%s is a saturday, don't count", date_dt)
                elif date_dt.weekday() == 6 and not self.include_sunday:
                    logger.info(
                        "%s is a sunday, don't count", date_dt)
                else:
                    days += 1.0
                if date_dt == end_date_dt:
                    break
                date_dt += relativedelta(days=1)
        return days

    @api.one
    @api.depends('holiday_type', 'employee_id', 'holiday_status_id')
    def _compute_current_leaves(self):
        total_allocated_leaves = 0
        current_leaves_taken = 0
        current_remaining_leaves = 0
        if (
                self.holiday_type == 'employee' and
                self.employee_id and
                self.holiday_status_id):

            days = self.holiday_status_id.get_days(self.employee_id.id)
            total_allocated_leaves =\
                days[self.holiday_status_id.id]['max_leaves']
            current_leaves_taken =\
                days[self.holiday_status_id.id]['leaves_taken']
            current_remaining_leaves =\
                days[self.holiday_status_id.id]['remaining_leaves']
        self.total_allocated_leaves = total_allocated_leaves
        self.current_leaves_taken = current_leaves_taken
        self.current_remaining_leaves = current_remaining_leaves

    vacation_date_from = fields.Date(
        string='First Day of Vacation', track_visibility='onchange',
        help="Enter the first day of vacation. For example, if "
        "you leave one full calendar week, the first day of vacation "
        "is Monday morning (and not Friday of the week before)")
    vacation_time_from = fields.Selection([
        ('morning', 'Morning'),
        ('noon', 'Noon'),
        ], string="Start of Vacation", track_visibility='onchange',
        default='morning',
        help="For example, if you leave one full calendar week, "
        "the first day of vacation is Monday Morning")
    vacation_date_to = fields.Date(
        string='Last Day of Vacation', track_visibility='onchange',
        help="Enter the last day of vacation. For example, if you "
        "leave one full calendar week, the last day of vacation is "
        "Friday evening (and not Monday of the week after)")
    vacation_time_to = fields.Selection([
        ('noon', 'Noon'),
        ('evening', 'Evening'),
        ], string="End of Vacation", track_visibility='onchange',
        default='evening',
        help="For example, if you leave one full calendar week, "
        "the end of vacation is Friday Evening")
    current_leaves_taken = fields.Float(
        compute='_compute_current_leaves', string='Current Leaves Taken',
        readonly=True)
    current_remaining_leaves = fields.Float(
        compute='_compute_current_leaves', string='Current Remaining Leaves',
        readonly=True)
    total_allocated_leaves = fields.Float(
        compute='_compute_current_leaves', string='Total Allocated Leaves',
        readonly=True)
    limit = fields.Boolean(  # pose des pbs de droits
        related='holiday_status_id.limit', string='Allow to Override Limit',
        readonly=True)
    posted_date = fields.Date(
        string='Posted Date', track_visibility='onchange')
    number_of_days_temp = fields.Float(string="Number of days")

    @api.one
    @api.constrains('vacation_date_from', 'vacation_date_to', 'holiday_type', 'type')
    def _check_vacation_dates(self):

        hhpo = self.env['hr.holidays.public']
        if self.type == 'remove':
            self.env['hr.employee'].button_holidays_history()
            if self.vacation_date_from > self.vacation_date_to:
                raise ValidationError(
                    _('The first day cannot be after the last day !'))
            #Pour le dépassement du solde de congé
            # somme = 0
            # nbr_of_days = self.number_of_days_temp
            # employee = self.employee_id
            # for holiday_history in employee.conges_ids:
            #     somme += holiday_history.solde_annuel
            # if somme > nbr_of_days:
            #     raise ValidationError('''Cette employé à dépassé le nombre de jours de congé disponible''')




    @api.onchange('vacation_date_from', 'vacation_time_from')
    def vacation_from(self):
        hour = 0  # = morning
        if self.vacation_time_from and self.vacation_time_from == 'noon':
            hour = 13
        datetime_str = False
        if self.vacation_date_from:
            date_dt = fields.Date.from_string(self.vacation_date_from)
            if self._context.get('tz'):
                localtz = pytz.timezone(self._context['tz'])
            else:
                localtz = pytz.utc
            datetime_dt = localtz.localize(datetime(
                date_dt.year, date_dt.month, date_dt.day, hour, 0, 0))
            datetime_str = fields.Datetime.to_string(
                datetime_dt.astimezone(pytz.utc))
        self.date_from = datetime_str

    @api.onchange('vacation_date_to', 'vacation_time_to')
    def vacation_to(self):
        hour = 23
        datetime_str = False
        if self.vacation_date_to:
            date_dt = fields.Date.from_string(self.vacation_date_to)
            if self._context.get('tz'):
                localtz = pytz.timezone(self._context['tz'])
            else:
                localtz = pytz.utc
            datetime_dt = localtz.localize(datetime(
                date_dt.year, date_dt.month, date_dt.day, hour, 0, 0))
            # we give to odoo a datetime in UTC
            datetime_str = fields.Datetime.to_string(
                datetime_dt.astimezone(pytz.utc))
        self.date_to = datetime_str

    @api.onchange(
        'vacation_date_from', 'vacation_time_from', 'vacation_date_to',
        'vacation_time_to', 'number_of_days_temp', 'type', 'holiday_type',
        'holiday_status_id','include_days_off','include_saturday','include_sunday')
    def leave_number_of_days_change(self):
        if self.type == 'remove':
            days = self._compute_number_of_days()
            self.number_of_days_temp = days
            if self.vacation_time_from == 'morning' and self.vacation_time_to == 'noon':
                self.number_of_days_temp -= 0.5
            elif self.vacation_time_from == 'noon' and self.vacation_time_to == 'evening':
                self.number_of_days_temp -= 0.5
            elif self.vacation_time_from == 'noon' and self.vacation_time_to == 'noon':
                self.number_of_days_temp -= 1

    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        return {}

    def holidays_first_validate(self, cr, uid, ids, context=None):
        da=self.browse(cr, uid, ids, context=context)
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.holidays_first_validate_notificate(cr, uid, ids, context=context)
        if da.type=='add':
            self.write(cr,uid,ids,{'state':'validate', 'manager_id': manager})
        else:
            self.write(cr, uid, ids, {'state':'validate1', 'manager_id': manager})
        return True

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        return {}

    @api.model
    def create(self, vals):
        context = dict(self._context, mail_create_nolog=True)
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not self.pool['res.users'].has_group('base.group_hr_user,paie.group_hr_payroll_manager,paie.group_officer_contract'):
            raise osv.except_osv(_('Warning!'), _('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % vals.get('state'))
        obj= osv.osv.create(self,vals)
        if obj.type == 'remove':
            days = obj._compute_number_of_days()
            obj.number_of_days_temp = days
        return obj

    @api.multi
    def write(self, vals):
        res = super(HrHolidays, self).write(vals)
        # res=self.write(vals)
        for obj in self:
            if obj.sudo().type == 'remove':
                days = obj.sudo()._compute_number_of_days()
                if days != obj.sudo().number_of_days_temp:
                    obj.sudo().number_of_days_temp = days
        return res

    @api.multi
    def holidays_check_before_validate(self):


        for holi in self:
            if holi.user_id == self.env.user:
                if holi.type == 'remove':
                    raise UserError(_(
                        "You cannot validate your own Leave request '%s'.")
                        % holi.name)
                elif (
                        holi.type == 'add' and
                        not self.pool['res.users'].has_group(
                            self._cr, self._uid, 'base.group_hr_manager')):
                    raise UserError(_(
                        "You cannot validate your own Allocation "
                        "request '%s'.")
                        % holi.name)
            if (
                    holi.type == 'add' and
                    holi.holiday_status_id.add_validation_manager and
                    not self.pool['res.users'].has_group(
                        self._cr, self._uid, 'base.group_hr_manager')):
                raise UserError(_(
                    "Allocation request '%s' has a leave type '%s' that "
                    "can be approved only by an HR Manager.")
                    % (holi.name, holi.holiday_status_id.name))

    def holidays_validate(self, cr, uid, ids, context=None):
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.write(cr, uid, ids, {'state':'validate'})
        data_holiday = self.browse(cr, uid, ids)
        for record in data_holiday:
            record.holidays_check_before_validate()
            if record.double_validation:
                self.write(cr, uid, [record.id], {'manager_id2': manager})
            else:
                self.write(cr, uid, [record.id], {'manager_id': manager})
            if record.holiday_type == 'employee' and record.type == 'remove':
                meeting_obj = self.pool.get('calendar.event')
                meeting_vals = {
                    'name': record.name or _('Leave Request'),
                    'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
                    'duration': record.number_of_days_temp * 8,
                    'description': record.notes,
                    'user_id': record.user_id.id,
                    'start': record.date_from,
                    'stop': record.date_to,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'class': 'confidential'
                }
                #Add the partner_id (if exist) as an attendee
                if record.user_id and record.user_id.partner_id:
                    meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]
                # analytic gen
                if record.timesheets_create:
                    dates_in_range = []
                    d1 = parser.parse(record.date_from).date()
                    d2 = parser.parse(record.date_to).date()
                    delta = d2 - d1
                    for i in range(delta.days+1):
                        date = (d1 + timedelta(days=i))
                        if not record.include_days_off:
                            days_off = self.pool.get('hr.holidays.public.line').search(cr, uid,[('date','=',date)])
                            if not days_off:
                                dates_in_range.append(date)
                        else:
                            dates_in_range.append(date)
                    if not record.include_saturday or not record.include_sunday:
                        if not record.include_saturday and not record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 5), dtstart=d1, until=d2)
                        elif record.include_saturday and record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 7), dtstart=d1, until=d2)
                        elif record.include_saturday and not record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 6), dtstart=d1, until=d2)
                        elif not record.include_saturday and record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 7), dtstart=d1, until=d2)
                        weekdays = list(weekdays)
                        i= 0
                        while i < len(weekdays):
                            if not record.include_saturday and record.include_sunday and weekdays[i].date().weekday() == 5:
                                print "date =",weekdays[i].date()
                                i+=1
                                continue
                            weekdays[i] = weekdays[i].date()
                            i+=1
                        dates_in_range = sorted(list(set(dates_in_range) & set(weekdays)))
                    for dt in dates_in_range:
                        context = dict(context, user_id = record.employee_id.user_id.id or False)
                        vals={}
                        vals['product_id']= self.pool.get('hr.analytic.timesheet')._getEmployeeProduct(cr, uid, context)
                        vals['product_uom_id']= self.pool.get('hr.analytic.timesheet')._getEmployeeUnit(cr, uid, context)
                        vals['general_account_id']=self.pool.get('hr.analytic.timesheet')._getGeneralAccount(cr, uid, context)
                        vals['journal_id']= self.pool.get('hr.analytic.timesheet')._getAnalyticJournal(cr, uid, context)
                        vals['account_id']= record.holiday_status_id.account_id.id or False
                        vals['date'] = dt
                        vals['emp_id'] = record.employee_id.id or False
                        vals['user_id'] = record.employee_id.user_id.id or False
                        vals['name'] = record.name
                        vals['unit_amount'] = record.employee_id.company_id.hours_per_day or 0
                        self.pool.get('hr.analytic.timesheet').create(cr, uid, vals)

                ctx_no_email = dict(context or {}, no_email=True)
                #meeting_id = meeting_obj.create(cr, uid, meeting_vals, context=ctx_no_email)
                self._create_resource_leave(cr, uid, [record], context=context)
                #self.write(cr, uid, ids, {'meeting_id': meeting_id})
            elif record.holiday_type == 'category':
                emp_ids = obj_emp.search(cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
                leave_ids = []
                for emp in obj_emp.browse(cr, uid, emp_ids):
                    vals = {
                        'name': record.name,
                        'type': record.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': record.holiday_status_id.id,
                        'date_from': record.date_from,
                        'date_to': record.date_to,
                        'notes': record.notes,
                        'number_of_days_temp': record.number_of_days_temp,
                        'parent_id': record.id,
                        'employee_id': emp.id
                    }
                    leave_ids.append(self.create(cr, uid, vals, context=None))

                    # analytic gen
                    if record.timesheets_create:
                        dates_in_range = []
                        d1 = parser.parse(record.date_from).date()
                        d2 = parser.parse(record.date_to).date()
                        delta = d2 - d1
                        for i in range(delta.days+1):
                            date = (d1 + timedelta(days=i))
                            if not record.include_days_off:
                                days_off = self.pool.get('hr.holidays.public.line').search(cr, uid,[('date','=',date)])
                                if not days_off:
                                    dates_in_range.append(date)
                            else:
                                dates_in_range.append(date)
                    if not record.include_saturday or not record.include_sunday:
                        if not record.include_saturday and not record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 5), dtstart=d1, until=d2)
                        elif record.include_saturday and record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 7), dtstart=d1, until=d2)
                        elif record.include_saturday and not record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 6), dtstart=d1, until=d2)
                        elif not record.include_saturday and record.include_sunday:
                            weekdays = rrule.rrule(rrule.DAILY, byweekday=range(0, 7), dtstart=d1, until=d2)
                        weekdays = list(weekdays)
                        i= 0
                        while i < len(weekdays):
                            if (not record.include_saturday and record.include_sunday) and weekdays[i].date().weekday() in (6):
                                continue
                            weekdays[i] = weekdays[i].date()
                            i+=1
                        dates_in_range = sorted(list(set(dates_in_range) & set(weekdays)))
                        for dt in dates_in_range:
                            context = dict(context, user_id = record.employee_id.user_id.id or False)
                            vals={}
                            vals['product_id']= self.pool.get('hr.analytic.timesheet')._getEmployeeProduct(cr, uid, context)
                            vals['product_uom_id']= self.pool.get('hr.analytic.timesheet')._getEmployeeUnit(cr, uid, context)
                            vals['general_account_id']=self.pool.get('hr.analytic.timesheet')._getGeneralAccount(cr, uid, context)
                            vals['journal_id']= self.pool.get('hr.analytic.timesheet')._getAnalyticJournal(cr, uid, context)
                            vals['account_id']= record.holiday_status_id.account_id.id or False
                            vals['date'] = dt
                            vals['emp_id'] = record.employee_id.id or False
                            vals['user_id'] = record.employee_id.user_id.id or False
                            vals['name'] = record.name
                            vals['unit_amount'] = record.employee_id.company_id.hours_per_day or 0
                            self.pool.get('hr.analytic.timesheet').create(cr, uid, vals)

                for leave_id in leave_ids:
                    # TODO is it necessary to interleave the calls?
                    for sig in ('confirm', 'validate', 'second_validate'):
                        self.signal_workflow(cr, uid, [leave_id], sig)
        return True


class ResCompany(models.Model):
    _inherit = 'res.company'

    mass_allocation_default_holiday_status_id = fields.Many2one(
        'hr.holidays.status', string='Default Leave Type for Mass Allocation')
