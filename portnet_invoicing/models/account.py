# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp.osv import  osv,orm
import time
from openerp import workflow


class account_period(models.Model):
    _inherit = "account.period"

    @api.returns('self')
    def next_period(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start','>',period.date_start),('special','=',False)])
        if len(ids)>=step:
            return ids[step-1]
        return False
    @api.multi
    def _get_period_months(self):
        date_start = datetime.strptime(str(self.date_start),'%Y-%m-%d')
        return  date_start.month

    @api.multi
    def _get_period_fiscalyear(self):
        date_start = datetime.strptime(str(self.fiscalyear_id.date_start),'%Y-%m-%d')
        return  date_start.year

account_period()


class account_move_line(models.Model):
    _inherit = "account.move.line"

    date_treasury=fields.Date(string='Date trésorerie')

    @api.onchange('date_maturity')
    def onchange_date_maturity(self):
        self.date_treasury = self.date_maturity

    @api.v7
    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        if context is None:
            context = {}
        company_list = []
        for line in lines:
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)
        for line in unrec_lines:
            if line.state <> 'valid':
                raise osv.except_osv(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit

        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')

        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s '\
                   'GROUP BY account_id,reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        if len(r) != 1:
            raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        if not unrec_lines:
            raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        account = account_obj.browse(cr, uid, account_id, context=context)
        if not account.reconcile:
            raise osv.except_osv(_('Error'), _('The account is not defined to be reconciled !'))
        if r[0][1] != None:
            raise osv.except_osv(_('Error!'), _('Some entries are already reconciled.'))

        if (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
           (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):
            if not writeoff_acc_id:
                raise osv.except_osv(_('Warning!'), _('You have to provide an account for the write off/exchange difference entry.'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle = context['comment']
            else:
                libelle = _('Write-Off')

            cur_obj = self.pool.get('res.currency')
            cur_id = False
            amount_currency_writeoff = 0.0
            if context.get('company_currency_id',False) != context.get('currency_id',False):
                cur_id = context.get('currency_id',False)
                for line in unrec_lines:
                    if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                        amount_currency_writeoff += line.amount_currency
                    else:
                        tmp_amount = cur_obj.compute(cr, uid, line.account_id.company_id.currency_id.id, context.get('currency_id',False), abs(line.debit-line.credit), context={'date': line.date})
                        amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount

            writeoff_lines = [
                (0, 0, {
                    'name': libelle,
                    'debit': self_debit,
                    'credit': self_credit,
                    'account_id': account_id,
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and -1 * amount_currency_writeoff or (account.currency_id.id and -1 * currency or 0.0)
                }),
                (0, 0, {
                    'name': libelle,
                    'debit': debit,
                    'credit': credit,
                    'account_id': writeoff_acc_id,
                    'analytic_account_id': context.get('analytic_id', False),
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and amount_currency_writeoff or (account.currency_id.id and currency or 0.0)
                })
            ]

            writeoff_move_id = move_obj.create(cr, uid, {
                'period_id': writeoff_period_id,
                'journal_id': writeoff_journal_id,
                'date':date,
                'state': 'draft',
                'line_id': writeoff_lines
            })

            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            if account_id == writeoff_acc_id:
                writeoff_line_ids = [writeoff_line_ids[1]]
            ids += writeoff_line_ids

        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_id': map(lambda x: (4, x, False), ids),
            'line_partial_ids': map(lambda x: (3, x, False), ids)
        }, context=reconcile_context)
        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            workflow.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id

    @api.v7
    def reconcile_old_lines(self, cr, uid, ids, type_rec,line_id,type='auto', context=None):
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        lines = self.browse(cr, uid, ids, context=context)
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
        }, context=reconcile_context)

        for id in ids:
            cr.execute("""update account_move_line set reconcile_id=%s ,reconcile_partial_id=null,
                         reconcile_ref=(select name from account_move_reconcile where id=%s) where id=%s"""%(r_id,r_id,id))
            workflow.trg_trigger(uid, 'account.move.line', id, cr)
        if type_rec=='partner' and line_id :
            if lines and lines[0]:
                partner_obj.mark_as_reconciled(cr, uid, [line_id], context=context)
        return r_id

account_move_line()

class account_move(models.Model):
    _inherit = "account.move"

    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Facture", required=False, )

    @api.multi
    def action_update_maturity_dates(self):
        if self.invoice_id and self.journal_id.type == 'sale':
            for line in self.line_id:
                if line.debit > 0:

                    #Recherche des conditions de règlement pour le calcul
                    if self.invoice_id.partner_id.property_payment_term:
                        payment_term_id = self.invoice_id.partner_id.property_payment_term.id
                    elif self.invoice_id.partner_id.categ_id and self.invoice_id.partner_id.categ_id.payment_term_id:
                        payment_term_id = self.invoice_id.partner_id.categ_id.payment_term_id.id
                    else:
                        payment_term_id = False
                    #Recherche des conditions de règlement pour le calcul

                    #Recherche des conditions de règlement tréso pour le calcul
                    if self.invoice_id.partner_id.treasury_term_id:
                        treasury_term_id = self.invoice_id.partner_id.treasury_term_id
                    else:
                        treasury_term_id = False
                    #Recherche des conditions de règlement tréso pour le calcul

                    #Calcul date échéance
                    date_maturity = False
                    if not payment_term_id:
                        date_maturity = self.invoice_id.date_invoice
                    else:
                        trterm = self.env['account.payment.term'].browse(payment_term_id)
                        trterm_list = trterm.compute(value=1, date_ref=self.invoice_id.date_invoice)[0]
                        if trterm_list:
                           date_maturity=max(line[0] for line in trterm_list)
                    #Calcul date échéance

                    #Calcul date échéance trésorerie
                    date_treasury = False
                    if not treasury_term_id:
                        date_treasury = date_maturity or self.invoice_id.date_invoice
                    else:
                        trterm = self.env['account.payment.term'].browse(treasury_term_id)
                        trterm_list = trterm.compute(value=1, date_ref=self.invoice_id.date_invoice)[0]
                        if trterm_list:
                           date_treasury=max(line[0] for line in trterm_list)
                    #Calcul date échéance trésorerie



                    line.write({'date_maturity':date_maturity,'date_treasury':date_treasury})
                    self.invoice_id.write({'date_due':date_maturity,'prevision_date': date_treasury})

        return True

account_move()


class account_account(models.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    prepaid_revenue = fields.Boolean(string="Produits constatés d'avance")
    prepaid_expense = fields.Boolean(string="Charges constatées d'avance")


account_account()

class account_journal(models.Model):
    _name = 'account.journal'
    _inherit = 'account.journal'

    prepaid_revenue = fields.Boolean(string="Produits constatés d'avance")
    prepaid_expense = fields.Boolean(string="Charges constatées d'avance")


account_journal()

class account_cutoff(models.Model):
    _name = 'account.cutoff'
    _inherit = 'account.cutoff'

    def _prepare_prepaid_lines(
            self, cr, uid, ids, aml, cur_cutoff, mapping, context=None):
        start_date = datetime.strptime(aml['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(aml['end_date'], '%Y-%m-%d')
        cutoff_date_str = cur_cutoff['cutoff_date']
        cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d')
        # Here, we compute the amount of the cutoff
        # That's the important part !
        total_days = (end_date - start_date).days + 1
        if aml['start_date'] > cutoff_date_str:
            after_cutoff_days = total_days
            cutoff_amount = -1 * (aml['credit'] - aml['debit'])
        else:
            after_cutoff_days = (end_date - cutoff_date).days
            if total_days:
                cutoff_amount = -1 * (aml['credit'] - aml['debit'])\
                    * after_cutoff_days / total_days
            else:
                raise orm.except_orm(
                    _('Error:'),
                    "Should never happen. Total days should always be > 0")

        # we use account mapping here
        if aml['account_id'] in mapping:
            cutoff_account_id = mapping[aml['account_id']]
        else:
            cutoff_account_id = aml['account_id']
        res = {
            'parent_id': ids[0],
            'move_line_id': aml['id'],
            'partner_id': aml['partner_id'] and aml['partner_id'] or 'null',
            'name': aml['name'],
            'start_date': aml['start_date'],
            'end_date': aml['end_date'],
            'account_id': aml['account_id'],
            'cutoff_account_id': cutoff_account_id,
            'analytic_account_id': (aml['analytic_account_id']
                                    if aml['analytic_account_id'] else 'null'),
            'total_days': total_days,
            'after_cutoff_days': after_cutoff_days,
            'amount': aml['credit'] - aml['debit'],
            'currency_id': cur_cutoff['company_currency_id'][0],
            'cutoff_amount': cutoff_amount,
            'budget_item_id': (aml['budget_item_id']
                               if aml['budget_item_id'] else 'null'),
        }
        return res

    def get_prepaid_lines(self, cr, uid, ids, context=None):
        print "in inherited get_prepaid_lines"
        assert len(ids) == 1,\
            'This function should only be used for a single id at a time'
        aml_obj = self.pool['account.move.line']
        line_obj = self.pool['account.cutoff.line']
        mapping_obj = self.pool['account.cutoff.mapping']
        cur_cutoff = self.read(
            cr, uid, ids[0], [
                'line_ids', 'source_journal_ids', 'cutoff_date', 'company_id',
                'type', 'company_currency_id'
            ],
            context=context)
        src_journal_ids = cur_cutoff['source_journal_ids']
        if not src_journal_ids:
            raise orm.except_orm(
                _('Error:'), _("You should set at least one Source Journal."))
        cutoff_date_str = cur_cutoff['cutoff_date']
        # Delete existing lines
        if cur_cutoff['line_ids']:
            line_ids_string = str(cur_cutoff['line_ids'])
            line_ids_string = line_ids_string.replace('[','(')
            line_ids_string = line_ids_string.replace(']',')')
            #line_obj.unlink(cr, uid, cur_cutoff['line_ids'], context=context)
            cr.execute("DELETE FROM account_cutoff_line WHERE id in "+line_ids_string)
        # Search for account move lines in the source journals
        src_journal_ids_string = str(src_journal_ids)
        src_journal_ids_string = src_journal_ids_string.replace('[','(')
        src_journal_ids_string = src_journal_ids_string.replace(']',')')

        req = "SELECT id " \
              " FROM account_move_line " \
              " WHERE start_date IS NOT NULL AND journal_id IN "+src_journal_ids_string+" AND end_date > '"+cutoff_date_str+"' AND date <= '"+cutoff_date_str+"' "
        cr.execute(req)
        aml_ids = [x[0] for x in cr.fetchall()]

        # aml_ids = aml_obj.search(cr, uid, [
        #     ('start_date', '!=', False),
        #     ('journal_id', 'in', src_journal_ids),
        #     ('end_date', '>', cutoff_date_str),
        #     ('date', '<=', cutoff_date_str)
        # ], context=context)
        # Create mapping dict
        mapping = mapping_obj._get_mapping_dict(
            cr, uid, cur_cutoff['company_id'][0], cur_cutoff['type'],
            context=context)
        # Loop on selected account move lines to create the cutoff lines
        aml_ids_string = str(aml_ids)
        aml_ids_string = aml_ids_string.replace('[','(')
        aml_ids_string = aml_ids_string.replace(']',')')
        req = "SELECT id, credit, debit, start_date, end_date, account_id, analytic_account_id, budget_item_id, partner_id, name " \
              " FROM account_move_line " \
              " WHERE id in "+aml_ids_string+" "
        if aml_ids:
            cr.execute(req)

        # for aml in aml_obj.read(
        #         cr, uid, aml_ids, [
        #             'credit', 'debit', 'start_date', 'end_date', 'account_id',
        #             'analytic_account_id', 'partner_id', 'name'
        #         ],
        #         context=context):
        result = cr.dictfetchall()
        i = 0
        for aml in result:
            i+=1
            print i
            values = self._prepare_prepaid_lines(cr, uid, ids, aml, cur_cutoff, mapping, context=context)
            req=" INSERT INTO account_cutoff_line(parent_id,move_line_id,partner_id,name,start_date,end_date,account_id,cutoff_account_id,analytic_account_id,total_days," \
            "after_cutoff_days,amount,currency_id,cutoff_amount,budget_item_id)"
            req+= " VALUES("+str(values['parent_id'])+","+str(values['move_line_id'])+","+str(values['partner_id'])+",'"+str(values['name'][:64])+"','"
            req+= str(values['start_date'])+"','"+str(values['end_date'])+"',"+str(values['account_id'])+","+str(values['cutoff_account_id'])+","+str(values['analytic_account_id'])+","
            req+= str(values['total_days'])+","+str(values['after_cutoff_days'])+","+str(values['amount'])+","+str(values['currency_id'])+","+str(values['cutoff_amount'])+","+str(values['budget_item_id'])
            req+=")"
            print "req =",req
            cr.execute(req)
        return True


    @api.depends('line_ids','line_ids.cutoff_amount')
    @api.one
    def _compute_total_cutoff(self):
        amount = 0
        try:
            self._cr.execute('select sum(cutoff_amount) from account_cutoff_line where parent_id = '+str(self.id))
            result = self._cr.fetchone()[0]
            if result != None:
                amount = result
        except:
            amount = 0
        self.total_cutoff_amount = amount


    total_cutoff_amount = fields.Float(string="Total Cut-off Amount", readonly=True, compute="_compute_total_cutoff", )


    @api.multi
    def unlink(self):
        if self.state=='done':
            raise exceptions.ValidationError(_('Vous ne pouvez pas supprimer un report validé'))
        else:
            return super(account_cutoff, self).unlink()

    @api.one
    def _move_label(self, type, cutoff_date):
        if self._context is None:
            context = {}
        if cutoff_date:
            cutoff_date_label = ' dated %s' % cutoff_date
        else:
            cutoff_date_label = ''
        label = ''
        if type == 'accrued_expense':
            label = _('Accrued Expense%s') % cutoff_date_label
        elif type == 'accrued_revenue':
            label = _('Accrued Revenue%s') % cutoff_date_label
        elif type == 'prepaid_revenue':
            label = _('Prepaid Revenue%s') % cutoff_date_label
        elif type == 'prepaid_expense':
            label = _('Prepaid Expense%s') % cutoff_date_label
        return str(label)

    @api.onchange('cutoff_date')
    def cutoff_date_onchange(self):
        if self._context is None:
            context = {}
        res = {'domain': {}}
        if self.type and self.cutoff_date:
            self.move_label = self._move_label(self.type,self.cutoff_date)
            if self.type in ["prepaid_expense","prepaid_revenue"]:
                accounts = self.env['account.account'].search([(self.type,'=',True)])
                if accounts:
                    res['domain']['cutoff_account_id'] = [('id','in',[ac.id for ac in accounts])]
                else:
                    res['domain']['cutoff_account_id'] = [('id','in',[])]
                if len(accounts) == 1:
                    self.cutoff_account_id = accounts[0].id
                journals = self.env['account.journal'].search([(self.type,'=',True)])
                if journals:
                    res['domain']['cutoff_journal_id'] = [('id','in',[j.id for j in journals])]
                else:
                    res['domain']['cutoff_journal_id'] = [('id','in',[])]
                if len(journals) == 1:
                    self.cutoff_journal_id = journals[0].id

        return res

account_cutoff()


class account_cutoff_line(models.Model):
    _name = 'account.cutoff.line'
    _inherit = 'account.cutoff.line'

    before_cutoff_days = fields.Integer(string="Nbr jours consommés",compute="_get_before_cutoff_days")
    residual_amount = fields.Float(string="Montant déja consommé", digits_compute=dp.get_precision('Account'), compute="_get_residual_amount")
    budget_item_id = fields.Many2one(comodel_name='crossovered.budget.lines',string='Ligne de budget')

    @api.one
    @api.depends('after_cutoff_days','total_days')
    def _get_before_cutoff_days(self):
        days = self.total_days - self.after_cutoff_days
        if days >= 0:
            self.before_cutoff_days = days
        else:
            self.before_cutoff_days = 0


    @api.one
    @api.depends('before_cutoff_days','total_days','amount')
    def _get_residual_amount(self):
        if self.before_cutoff_days > 0 and self.total_days > 0:
            self.residual_amount = (self.amount/self.total_days)*self.before_cutoff_days
        else:
            self.residual_amount = 0.00

account_cutoff_line()

