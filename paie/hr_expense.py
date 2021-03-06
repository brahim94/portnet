from openerp import fields, models, api
from openerp import exceptions
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _

class expense(models.Model):
    _inherit = 'hr.expense.expense'

    def action_move_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
        #     if not exp.employee_id.address_home_id:
        #         raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
        #     if not exp.employee_id.address_home_id.property_account_payable.id:
        #         raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency

            # create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)

            # one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)

            # create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml,
                                                                     context=context)
            if not exp.employee_id.property_account_payable:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account.'))
            else:
                acc = exp.employee_id.property_account_payable.id
                eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total,
                    'account_id': acc,
                    'date_maturity': exp.date_confirm,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and exp.currency_id.id or False,
                    'ref': exp.name
                })

            # convert eml into an osv-valid format
            lines = map(lambda x: (
            0, 0, self.line_get_convert(cr, uid, x, exp.employee_id.address_home_id, exp.date_confirm, context=context)),
                        eml)
            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'done'}, context=context)
        return True