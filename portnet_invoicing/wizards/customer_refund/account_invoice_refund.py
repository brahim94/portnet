# -*- coding: utf-8 -*-

import time
from openerp import models, fields, api, exceptions, _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import osv
from openerp import workflow
import psycopg2

class account_invoice_refund(models.TransientModel):
    """Refunds Customer invoice"""

    _inherit = "account.invoice.refund"


    def default_is_operation(self):
        inv_id=self._context.get('active_ids')[0]
        inv_type=self._context.get('type')
        invoice_id = self.env['account.invoice'].search([('id','=',inv_id)])
        if invoice_id.line_store_ids and inv_type=='out_invoice' :
           return True
        else :
            return False

    @api.onchange('is_operation','filter_refund')
    def onchange_is_operation(self):
        if self.is_operation :
            self.filter_refund='modify'
    @api.v7
    def get_tuple(self,list):
        if len(list) ==1 :
            return "('"+str(list[0])+"')"
        else :
            return tuple(list)

    @api.v7
    def compute_refund(self, cr, uid, ids, mode='refund', is_operation=False,code_list=False,filter_column=False ,context=None):
        print"""
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice refund’s ID or list of IDs

        """
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        if context is None:
            context = {}

        for form in self.browse(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.journal_id.id
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error!'), _('Cannot %s draft/proforma/cancel invoice.') % (mode))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise osv.except_osv(_('Error!'), _('Cannot %s invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.') % (mode))
                if form.period.id:
                    period = form.period.id
                else:
                    period = inv.period_id and inv.period_id.id or False

                if not journal_id:
                    journal_id = inv.journal_id.id

                if form.date:
                    date = form.date
                    if not form.period.id:
                            cr.execute("select name from ir_model_fields \
                                            where model = 'account.period' \
                                            and name = 'company_id'")
                            result_query = cr.fetchone()
                            if result_query:
                                cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                                    and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                            else:
                                cr.execute("""SELECT id
                                        from account_period where date(%s)
                                        between date_start AND  date_stop  \
                                        limit 1 """, (date,))
                            res = cr.fetchone()
                            if res:
                                period = res[0]
                else:
                    date = inv.date_invoice
                if form.description:
                    description = form.description
                else:
                    description = inv.name

                if not period:
                    raise osv.except_osv(_('Insufficient Data!'), \
                                            _('No period found on the invoice.'))

                refund_id = inv_obj.refund(cr, uid, [inv.id], date, period, description, journal_id, context=context)
                refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                inv_obj.write(cr, uid, [refund.id], {'date_due': date,
                                                'check_total': inv.check_total})
                #Changement de la quantité à 1 si le prix est forfaitaire
                if is_operation:
                    update_qty_on_refund = False
                    op_ids=self.pool.get('operation.type').search(cr,uid,[('partner_categ_id','=',inv.partner_id.categ_id.id),
                                                                          ('product_id','=',inv.invoice_line[0].product_id.id)])
                    if not op_ids:
                        raise except_orm (_("Merci de configurer un type d'opération pour la catégorie %s "),
                          _("%s"%inv.partner_id.categ_id.name))
                    operations = self.pool.get('operation.type').browse(cr,uid,op_ids)
                    for op in operations :
                        if not op.product_id.property_account_income:
                            raise except_orm (_("Merci de configurer le compte de revenus du produit %s "),
                          _("%s"%op.product_id.name))
                    for line in refund.invoice_line :
                        if operations[0].fixed_price:
                            line.write({'quantity':1})
                            update_qty_on_refund = True
                #Changement de la quantité à 1 si le prix est forfaitaire
                inv_obj.button_compute(cr, uid, refund_id)

                created_inv.append(refund_id[0])
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_id
                    to_reconcile_ids = {}
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconcile_id:
                            line.reconcile_id.unlink()
                    refund.signal_workflow('invoice_open')
                    refund = inv_obj.browse(cr, uid, refund_id[0], context=context)
                    refund.invoice_print_auto()
                    #MAJ de la quantité si le prix est forfaitaire
                    if is_operation:
                        if update_qty_on_refund:
                            for line in refund.invoice_line :
                                line.write({'quantity':inv.invoice_line[0].quantity})
                                line.write({'price_subtotal':inv.invoice_line[0].price_unit})
                                line.invoice_id.write({'amount_untaxed':inv.invoice_line[0].price_unit,
                                                       'amount_total':inv.invoice_line[0].price_unit + inv.invoice_line[0].invoice_id.amount_tax})
                    #MAJ de la quantité si le prix est forfaitaire
                    for tmpline in  refund.move_id.line_id:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_ids[tmpline.account_id.id].append(tmpline.id)
                    for account in to_reconcile_ids:
                        account_m_line_obj.reconcile(cr, uid, to_reconcile_ids[account],
                                        writeoff_period_id=period,
                                        writeoff_journal_id = inv.journal_id.id,
                                        writeoff_acc_id=inv.account_id.id
                                        )
                    if mode == 'modify':
                        print "----------modify mode : avoir des opérations facturées---------------------------"
                        invoice = inv_obj.read(cr, uid, [inv.id],
                                    ['name', 'type', 'number', 'reference',
                                    'comment', 'date_due', 'partner_id',
                                    'partner_insite', 'partner_contact',
                                    'partner_ref', 'payment_term', 'account_id',
                                    'currency_id', 'invoice_line', 'tax_line',
                                    'journal_id', 'period_id', 'date_invoice'], context=context)
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(cr, uid, invoice['invoice_line'], context=context)
                        invoice_lines = inv_obj._refund_cleanup_lines(cr, uid, invoice_lines, context=context)
                        tax_lines = inv_tax_obj.browse(cr, uid, invoice['tax_line'], context=context)
                        tax_lines = inv_obj._refund_cleanup_lines(cr, uid, tax_lines, context=context)
                        invoice.update({
                            'origin':inv.origin,
                            'op_id':inv.op_id.id,
                            'type': inv.type,
                            'date_invoice': date,
                            'state': 'draft',
                            'number': False,
                            'invoice_line': invoice_lines,
                            'tax_line': tax_lines,
                            'period_id': invoice['period_id'][0],
                            'name': description,
                        })
                        for field in ('partner_id', 'account_id', 'currency_id',
                                         'payment_term', 'journal_id'):
                                invoice[field] = invoice[field] and invoice[field][0]
                        inv_id = inv_obj.create(cr, uid, invoice, {})
                        print "inv_id =",inv_id
                        if is_operation :
                            #self.update_invoice_line_store(cr,uid,code_list,refund,inv)
                            database_id=self.pool.get('op.store.db.settings').search(cr,uid,[('is_db_store','=',True)])
                            for db in self.pool.get('op.store.db.settings').browse(cr,uid,database_id) :
                                dbcr=self.pool.get('op.store.db.settings').get_cursor_database(cr,uid,ids,db.server,db.port,db.dbname,db.user,db.password)
                                result_ids = []
                                for code in code_list:
                                    code_tuple = self.get_tuple([code])
                                    code_to_refund="select id from invoice_line_store where state='done' and " \
                                   "%s in %s  and invoice_id='%s'"%(filter_column,code_tuple,str(inv.id))
                                    dbcr.execute(code_to_refund)
                                    result = map(lambda x: x[0], dbcr.fetchall())
                                    if not result :
                                        raise except_orm (_("Attention"),_("Le code '"+str(code)+"' est incorrect ou déjà utilisé pour un autre avoir"))
                                    else:
                                        result_ids.append(result[0])
                                # list=self.get_tuple(code_list)
                                # select_to_refund="select id from invoice_line_store where state='done' and " \
                                #    "%s in %s  and invoice_id='%s'"%(filter_column,list,str(inv.id))
                                # dbcr.execute(select_to_refund)
                                # result_ids = map(lambda x: x[0], dbcr.fetchall())
                                # if not result_ids :
                                #     raise except_orm (_("Attention"),_("Les codes sont incorrectes ou déjà utilisés pour d'autres avoirs"))
                                list2=self.get_tuple(result_ids)
                                req_to_refund="update invoice_line_store set state='refund', refund_id='%s' where id in %s"%(refund.id,list2)
                                dbcr.execute(req_to_refund)
                                codes=inv.line_store_ids.replace("(","")
                                codes=codes.replace(")","")
                                codes=codes.replace(" ","")
                                codes=codes.split(",")
                                list3=[]
                                for code in codes:
                                    list3.append(int(code))
                                new_store_ids=set(list3)-set(result_ids)
                                inv_obj.write(cr,uid,inv_id,{'line_store_ids':tuple(new_store_ids)})
                                #update invoice in in op line store to link it the new generated invoice from refund
                                if len(new_store_ids) > 1 :
                                    update_op_new_invoice="update invoice_line_store set  invoice_id="+str(inv_id)+" where id in "+str(tuple(new_store_ids))
                                else :
                                    a=str(tuple(new_store_ids))
                                    update_op_new_invoice="update invoice_line_store set  invoice_id="+str(inv_id)+" where id = "+a[1:2]
                                #update invoice in in op line store to link it the new generated invoice from refund
                                dbcr.execute(update_op_new_invoice)
                                invoice = inv_obj.read(cr, uid, [inv_id], ['invoice_line'], context=context)
                                invoice_lines = inv_line_obj.browse(cr, uid, invoice[0]['invoice_line'], context=context)
                                #Changement de la quantité à 1 si le prix est forfaitaire
                                update_qty_on_new_invoice = False
                                op_ids=self.pool.get('operation.type').search(cr,uid,[('partner_categ_id','=',invoice_lines[0].invoice_id.partner_id.categ_id.id),
                                                                                      ('product_id','=',invoice_lines[0].product_id.id)])
                                if not op_ids:
                                    raise except_orm (_("Merci de configurer un type d'opération pour la catégrorie "),
                                      _("%s"%invoice_lines[0].invoice_id.partner_id.categ_id.name))
                                operations = self.pool.get('operation.type').browse(cr,uid,op_ids)
                                for op in operations :
                                    if not op.product_id.property_account_income:
                                        raise except_orm (_("Merci de configurer le compte de revenus du produit %s "),
                                      _("%s"%op.product_id.name))
                                for line in invoice_lines :
                                    if operations[0].fixed_price:
                                        line.write({'quantity':1})
                                        update_qty_on_new_invoice = True
                                    else:
                                        line.write({'quantity':len(new_store_ids)})
                                #Changement de la quantité à 1 si le prix est forfaitaire
                                invoice=inv_obj.browse(cr,uid,inv_id)
                                invoice.button_reset_taxes()
                                workflow.trg_validate(uid, 'account.invoice',inv_id, 'invoice_open',cr)
                                #MAJ de la quantité si le prix est forfaitaire
                                if update_qty_on_new_invoice:
                                    for line in invoice_lines :
                                        line.write({'quantity':len(new_store_ids)})
                                        line.write({'price_subtotal':line.price_unit})
                                        line.invoice_id.write({'amount_untaxed':line.price_unit,
                                                               'amount_total':line.price_unit + line.invoice_id.amount_tax})
                                #MAJ de la quantité si le prix est forfaitaire
                                inv_obj.browse(cr,uid,inv_id).invoice_print_auto(operation=True)
                                inv_obj.browse(cr, uid, inv_id).action_send_mail_auto()
                                dbcr.execute("COMMIT")
                        if inv.payment_term.id:
                            data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv.payment_term.id, date)
                            if 'value' in data and data['value']:
                                inv_obj.write(cr, uid, [inv_id], data['value'])
                        created_inv.append(inv_id)

            xml_id = (inv.type == 'out_refund') and 'action_invoice_tree1' or \
                     (inv.type == 'in_refund') and 'action_invoice_tree2' or \
                     (inv.type == 'out_invoice') and 'action_invoice_tree3' or \
                     (inv.type == 'in_invoice') and 'action_invoice_tree4'
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False

            result = act_obj.read(cr, uid, [id], context=context)[0]
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
    @api.v7
    def invoice_refund(self, cr, uid, ids, context=None):
        wizard_id=self.browse(cr,uid,ids[0])
        data_refund = self.read(cr, uid, ids, ['filter_refund'],context=context)[0]['filter_refund']
        code_list=[]
        filter_column=False
        if wizard_id.is_operation :
            if not wizard_id.operation_ids :
                raise except_orm (_("Attention"),_("Merci de saisir les codes des opérations avant la validation"))
            filter_column=wizard_id.filter_column
            if not filter_column :
                raise except_orm (_("Attention"),_("Merci de configurer le numéro au niveau de type opération de la facture"))
            for line in wizard_id.operation_ids :
                code_list.append(str(line.code))
        res =self.compute_refund(cr, uid, ids, data_refund, wizard_id.is_operation,code_list,filter_column,context=context)
        #raise except_orm (_("RES"),_("rrr"))
        return res

    def get_filter_column(self):
        if self._context.get('active_ids') :
            inv_id=self._context.get('active_ids')[0]
            inv_type=self._context.get('type')
            invoice_id = self.env['account.invoice'].search([('id','=',inv_id)])
            if invoice_id.line_store_ids and inv_type=='out_invoice' :
                filters=self.env['operation.type']._get_op_filters(invoice_id.op_id)
                return filters['code_op'] or False



    is_operation=fields.Boolean(string="Lié aux oéprations", default=default_is_operation)
    operation_ids = fields.One2many(comodel_name="operation.to.cancel",inverse_name="wizard_id", string="Opérations à annuler", required=False)
    filter_column=fields.Char(string="Filtre", default=get_filter_column)


account_invoice_refund()

class operation_to_cancel(models.TransientModel):

    _name = "operation.to.cancel"

    wizard_id=fields.Many2one(comodel_name="account.invoice.refund", string="Wizard ID")
    code=fields.Char(string="Code opération",required=True)

operation_to_cancel()



