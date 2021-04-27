# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class hr_analytic_timesheet(models.Model):
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'


    emp_id = fields.Many2one(comodel_name="hr.employee", string="Employé", required=False)

    @api.v7
    def on_change_user_id(self, cr, uid, ids, user_id):
        if not user_id:
            return {'value': {'emp_id': False}}
        entries = self.pool.get("hr.employee").search(cr, uid, [('user_id','=',user_id)])
        context = {'user_id': user_id}
        return {'value': {
            'product_id': self. _getEmployeeProduct(cr, uid, context),
            'product_uom_id': self._getEmployeeUnit(cr, uid, context),
            'general_account_id': self._getGeneralAccount(cr, uid, context),
            'journal_id': self._getAnalyticJournal(cr, uid, context),
            'emp_id':entries[0] or False
        }}

hr_analytic_timesheet()