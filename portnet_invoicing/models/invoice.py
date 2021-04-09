# -*- encoding: utf-8 -*-

from openerp import SUPERUSER_ID,models, fields, api, _, exceptions
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import psycopg2
from openerp import workflow
from xml.dom import minidom
import base64
from dateutil.relativedelta import relativedelta
from dateutil import parser, rrule
from datetime import datetime
from openerp.osv import orm
import time
import os
import base64


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    contract_id = fields.Many2one(comodel_name="res.contract", string="Contrat")
    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Liste de prix", required=False, domain=[('active','=',True)])
    categ_pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Liste de prix liée à la catégorie du client", required=False,compute="_get_categ_pricelist" )
    op_id = fields.Many2one(comodel_name="operation.type", string="Type d'opération", required=False, domain=[('state','=','confirmed')])
    line_store_ids = fields.Char(string="IDs lignes de pré-facturation", required=False)
    prevision_date=fields.Date(string="Date d'écheance trésorerie")
    treasury_term_id=fields.Many2one(comodel_name='account.payment.term',string='réglement de trésorerie')
    from_picking = fields.Boolean(string="From picking")
    from_order = fields.Boolean(string="From purchase order")
    purchase_order_id=fields.Many2one(comodel_name='purchase.order',string='Purchase order')
    requisition_id=fields.Many2one('purchase.requisition',string="Demande d\'achat")
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False,default=datetime.now().strftime('%Y-%m-%d'))

    customer_categ_id = fields.Many2one(comodel_name="res.partner.category", string="Catégorie", related="partner_id.categ_id")
    partner_code = fields.Char(string="Code client", related="partner_id.code" )
    invoicing_op_id = fields.Many2one(comodel_name="invoicing.operation", string="Opération")
    op_qty = fields.Float(string="QTY Opérations")
    renewal = fields.Boolean(string="Renouvellement")
    majoration = fields.Boolean(string="Majoration")
    original_invoice_id = fields.Many2one(comodel_name="account.invoice", string="Facture originale", domain = [('state','!=','draft'),('type','=','out_invoice')])
    xml_history_ids = fields.One2many(comodel_name="xml.history", inverse_name="invoice_id", string="Historique XML")
    flag_60_days_contract_mail = fields.Boolean('Mail 60 jours envoyé', default=False)
    flag_0_day_contract_mail = fields.Boolean('Mail aniversaire contrat envoyé', default=False)
    flag_30_before_invoice_mail = fields.Boolean('Mail 30 jours avant échéance facture envoyé', default=False)
    flag_0_day_invoice_mail = fields.Boolean('Mail jour échéance facture envoyé', default=False)
    flag_30_after_invoice_mail = fields.Boolean('Mail jour échéance facture envoyé', default=False)


    @api.model
    def _cron_close_at_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        due_invoices = self.search([('state', '=', 'open'),('contract_id','!=',False),('flag_0_day_contract_mail','=',False),('user_id','=',SUPERUSER_ID)])
        for inv in due_invoices:
            inv_partner = inv.partner_id
            next_invoice_date = str(inv.contract_id.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff <= 0 and inv_partner.categ_id != False and inv_partner.categ_id.closed_related_contracts:
                #print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
                inv.contract_id.set_closed()
                # inv.action_send_mail_auto_notif()
                inv.flag_0_day_contract_mail = True
                self._cr.commit()

    @api.model
    def _cron_email_two_months_before_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        due_invoices = self.search([('state', '=', 'open'),('contract_id','!=',False),('flag_60_days_contract_mail','=',False)])
        for inv in due_invoices:
            inv_partner = inv.partner_id
            next_invoice_date = str(inv.contract_id.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff <= 61 and inv_partner.categ_id != False and inv_partner.categ_id.be_notified:
                # print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
                inv.action_send_mail_auto_notif('portnet_invoicing.email_template_edi_invoice_portnet_60_next_inv')
                inv.flag_60_days_contract_mail = True
                self._cr.commit()


    @api.model
    def _cron_email_month_after_due_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        due_invoices = self.search([('state', '=', 'open'),('contract_id','!=',False),('type','=','out_invoice'),('flag_30_after_invoice_mail','=',False)])
        for inv in due_invoices:
            if inv.date_due:
                inv_partner = inv.partner_id
                date_due = str(inv.date_due)
                d2 = datetime.strptime(date_due, date_format)
                daysDiff = (d1 - d2).days
                if daysDiff >= 31 and inv_partner.categ_id != False and inv_partner.categ_id.be_notified:
                    #print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
                    inv.action_send_mail_auto_notif('portnet_invoicing.email_template_edi_invoice_portnet_one_month_after_due_date')
                    inv.flag_30_after_invoice_mail = True
                    self._cr.commit()

    @api.model
    def _cron_email_month_at_due_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        due_invoices = self.search([('state', '=', 'open'),('contract_id','!=',False),('type','=','out_invoice'),('flag_0_day_invoice_mail','=',False)])
        for inv in due_invoices:
            print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
            if inv.date_due:
                inv_partner = inv.partner_id
                date_due = str(inv.date_due)
                d2 = datetime.strptime(date_due, date_format)
                daysDiff = (d2 - d1).days
                if daysDiff <= 1 and inv_partner.categ_id != False and inv_partner.categ_id.be_notified:
                    #print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
                    inv.action_send_mail_auto_notif('portnet_invoicing.email_template_edi_invoice_portnet_at_invoice_due_date')
                    inv.flag_0_day_invoice_mail = True
                    self._cr.commit()

    @api.model
    def _cron_email_month_before_due_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        due_invoices = self.search([('state', '=', 'open'),('contract_id','!=',False),('type','=','out_invoice'),('flag_30_before_invoice_mail','=',False)])
        for inv in due_invoices:
            if inv.date_due:
                inv_partner = inv.partner_id
                date_due = str(inv.date_due)
                d2 = datetime.strptime(date_due, date_format)
                daysDiff = (d2 - d1).days
                if daysDiff <= 29 and inv_partner.categ_id != False and inv_partner.categ_id.be_notified:
                    # print "Partenaire recevant l'email", inv.partner_id.name, " Categorie ", inv.partner_id.categ_id.name
                    inv.action_send_mail_auto_notif('portnet_invoicing.email_template_edi_invoice_portnet_one_month_before_due_date')
                    inv.flag_30_before_invoice_mail = True
                    self._cr.commit()


    @api.model
    def _cron_email_remaining_invoices(self):
        unsent_invoices = self.search([('sent','=',False),('type','=','out_invoice'),('state','=','open')],limit=100)
        print "Invoice identification"
        for inv in unsent_invoices:
            inv.action_send_mail_auto()
            self._cr.commit()

    # envoi les emails de notification de non paiement
    @api.multi
    def action_send_mail_auto_notif(self,template_id):
        """ Sends a notification mail
        """
        template = self.env.ref(template_id, False)

        context = self._context.copy()
        context['default_model'] = 'account.invoice'
        context['default_res_id'] = self.id
        context['default_use_template'] = bool(template)
        context['default_template_id'] = template.id
        context['default_composition_mode'] = 'comment'
        # context['make_invoice_as_sent'] = True
        invoice = self.env['account.invoice'].browse(context['default_res_id'])
        # invoice = invoice.with_context(mail_post_autofollow=True)
        # invoice.write({'sent': True})
        attachments_ids = []
        attachments = self.pool.get('ir.attachment').search_read(self._cr, 1,
                                                                 [('res_model', '=', context['default_model']),
                                                                  ('res_id', '=', context['default_res_id'])], ['id'])
        pj_ids = []
        for pj in attachments:
            pj_ids.append(pj['id'])
        pj_ids = sorted(pj_ids)
        if pj_ids:
            attachments_ids.append(pj_ids[0])
            if invoice.op_id:
                attachments_ids.append(pj_ids[1])
            if attachments_ids:
                context['attachment_ids'] = attachments_ids
        self.pool.get('email.template').send_mail(self._cr, self._uid, template.id, context['default_res_id'], True,
                                                  context=context)

    @api.multi
    def action_send_mail_auto(self):
        """ Sends an invoice mail
        """
        template = self.env.ref('portnet_invoicing.email_template_edi_invoice_portnet', False)

        context = self._context.copy()
        context['default_model']= 'account.invoice'
        context['default_res_id'] = self.id
        context['default_use_template'] = bool(template)
        context['default_template_id'] = template.id
        context['default_composition_mode'] = 'comment'
        context['make_invoice_as_sent'] = True
        invoice = self.env['account.invoice'].browse(context['default_res_id'])
        invoice = invoice.with_context(mail_post_autofollow=True)
        invoice.write({'sent': True})
        attachments_ids = []
        attachments = self.pool.get('ir.attachment').search_read(self._cr, 1, [('res_model','=',context['default_model']),('res_id','=',context['default_res_id'])], ['id'])
        pj_ids = []
        for pj in attachments:
            pj_ids.append(pj['id'])
        pj_ids = sorted(pj_ids)
        if pj_ids:
            attachments_ids.append(pj_ids[0])
            if invoice.op_id:
                attachments_ids.append(pj_ids[1])
            if attachments_ids:
                context['attachment_ids'] = attachments_ids
        self.pool.get('email.template').send_mail(self._cr, self._uid, template.id, context['default_res_id'],True, context=context)


    def line_get_convert(self, cr, uid, x, part, date, context=None):
          res = super(account_invoice, self).line_get_convert(
            cr, uid, x, part, date, context=context)
          res['start_date'] = x.get('start_date', False)
          res['end_date'] = x.get('end_date', False)
          res['date_treasury'] = x.get('date_treasury', False)
          res['budget_line_id'] = x.get('budget_line_id', False)
          res['budget_item_id'] = x.get('budget_line_id', False)
          return res

    @api.multi
    def action_move_create(self):
      '''Check that products with must_have_dates=True have
      Start and End Dates'''
      for invoice in self.browse(self.ids):
          for invline in invoice.invoice_line:
              if invline.product_id and invline.product_id.must_have_dates:
                 if not invline.start_date or not invline.end_date:
                    raise orm.except_orm(
                        _('Error:'),
                        _("Missing Start Date and End Date for invoice "
                            "line with Product '%s' which has the "
                            "property 'Must Have Start and End Dates'.")
                        % (invline.product_id.name))

      """ Creates invoice related analytics and financial move lines """
      account_invoice_tax = self.env['account.invoice.tax']
      account_move = self.env['account.move']

      for inv in self:
          if not inv.journal_id.sequence_id:
            raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
          if not inv.invoice_line:
             raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
          # TEST IF THE TOTAL AMOUNT IS + 10% HIGHER THAN THE ORIGINAL PURCHASE
          if inv.type == 'in_invoice':
              if inv.invoice_line[0].purchase_line_id:
                  invoice_amount = inv.amount_untaxed
                  purchase_amount = inv.invoice_line[0].purchase_line_id.order_id.amount_untaxed
                  purchase_amount_plus_10_percent = purchase_amount + (purchase_amount*0.1)
                  if invoice_amount > purchase_amount_plus_10_percent:
                      raise except_orm(_("Contrôle montant"), _("Le montant de la facture dépasse de plus que 10% le montant de de l'achat"))
          # TEST IF THE TOTAL AMOUNT IS + 10% HIGHER THAN THE ORIGINAL PURCHASE
          if inv.move_id:
             continue

          ctx = dict(self._context, lang=inv.partner_id.lang)

          if not inv.date_invoice:
             inv.with_context(ctx).write({'date_invoice': fields.date.today()})
          date_invoice = inv.date_invoice

          company_currency = inv.company_id.currency_id
          # create the analytical lines, one move line per invoice line
          iml = inv._get_analytic_lines()
          # check if taxes are all computed
          compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
          inv.check_tax_lines(compute_taxes)

          # I disabled the check_total feature
          if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
             if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
                raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

          if inv.payment_term:
             total_fixed = total_percent = 0
             for line in inv.payment_term.line_ids:
                 if line.value == 'fixed':
                    total_fixed += line.value_amount
                 if line.value == 'procent':
                    total_percent += line.value_amount
             total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
             if (total_fixed + total_percent) > 100:
                raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

          # one move line per tax line
          iml += account_invoice_tax.move_line_get(inv.id)

          if inv.type in ('in_invoice', 'in_refund'):
             ref = inv.reference
          else:
             ref = inv.number

          diff_currency = inv.currency_id != company_currency
          # create one move line for the total and possibly adjust the other lines amount
          total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)

          name = inv.supplier_invoice_number or inv.name or '/'
          totlines = []
          if inv.payment_term:
             totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
          if totlines:
             res_amount_currency = total_currency
             ctx['date'] = date_invoice
             for i, t in enumerate(totlines):
                 if inv.currency_id != company_currency:
                    amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                 else:
                    amount_currency = False

                 # last line: add the diff
                 res_amount_currency -= amount_currency or 0
                 if i + 1 == len(totlines):
                    amount_currency += res_amount_currency

                 iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': t[1],
                    'account_id': inv.account_id.id,
                    'date_maturity': t[0],
                    'date_treasury':inv.prevision_date,
                    'amount_currency': diff_currency and amount_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'ref': ref,
                 })
          else:
            iml.append({
                'type': 'dest',
                'name': name,
                'price': total,
                'account_id': inv.account_id.id,
                'date_maturity': inv.date_due,
                'date_treasury':inv.prevision_date,
                'amount_currency': diff_currency and total_currency,
                'currency_id': diff_currency and inv.currency_id.id,
                'ref': ref
            })
          date = date_invoice

          part = self.env['res.partner']._find_accounting_partner(inv.partner_id)

          line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
          line = inv.group_lines(iml, line)

          journal = inv.journal_id.with_context(ctx)
          if journal.centralisation:
             raise except_orm(_('User Error!'),
                    _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

          line = inv.finalize_invoice_move_lines(line)

          move_vals = {
            'ref': inv.reference or inv.name,
            'line_id': line,
            'journal_id': journal.id,
            'date': inv.date_invoice,
            'narration': inv.comment,
            'date_treasury':inv.prevision_date,
            'company_id': inv.company_id.id,
          }
          ctx['company_id'] = inv.company_id.id
          period = inv.period_id
          if not period:
             period = period.with_context(ctx).find(date_invoice)[:1]
          if period:
             move_vals['period_id'] = period.id
             for i in line:
                 i[2]['period_id'] = period.id

          ctx['invoice'] = inv
          ctx_nolang = ctx.copy()
          ctx_nolang.pop('lang', None)
          move = account_move.with_context(ctx_nolang).create(move_vals)
          #invoice ref to account move
          move.write({'invoice_id':inv.id})
          #invoice ref to account move


          # make the invoice point to that move
          vals = {
            'move_id': move.id,
            'period_id': period.id,
            'move_name': move.name,
          }
          inv.with_context(ctx).write(vals)
          # Pass invoice in context in method post: used if you want to get the same
          # account move reference when creating the same invoice after a cancelled one:
          move.post()
      self._log_event()
      return True
      # return super(account_invoice, self).action_move_create(
      #   cr, uid, ids, context=context)

    @api.multi
    def _calculate_diff_days(self,date_start,date_end):
        print "qsdqsdazeazaeffffffff"
        delay_days_count = rrule.rrule(rrule.DAILY, dtstart=parser.parse(date_start), until=parser.parse(date_end)).count()-1
        print "delay_days_count =",delay_days_count
        if delay_days_count > 0:
            return delay_days_count
        else:
            return 0

    @api.multi
    def action_supplier_penalty_fees(self):
        vals={
            'invoice_id':self.id,
            'base_amount':self.amount_untaxed
              }
        penalty_fees_product = self.env['product.product'].search([('supplier_penalty_fees','=',True)])
        if not penalty_fees_product:
            raise exceptions.ValidationError("Veuillez configurer un produit pour les pénalités de retard")
        if len(penalty_fees_product) <= 1:
            vals['penalty_fees_product_id'] = penalty_fees_product[0].id
        wizard_id = self.pool.get("supplier.penalty.fees.wizard").create(self._cr, self._uid, vals, context=self._context)
        vals={}
        for l in self.invoice_line:
            vals= {
                'penalty_fees_wizard_id':wizard_id,
                'invoice_qty':l.quantity,
            }
            if l.move_id:
                vals['move_id'] = l.move_id.id
                vals['product_name'] = l.move_id.product_id.name
                vals['received_qty']= l.move_id.product_uos_qty
                vals['picking_name']= l.move_id.picking_id.name
                vals['planned_date'] = l.move_id.date
                vals['reception_date'] = l.move_id.picking_id.date_done or self.date_invoice
                line = self.env['penalty.move.line'].create(vals)
                line.write({'diff':self._calculate_diff_days(vals['planned_date'],vals['reception_date'])})
            elif l.purchase_line_id:
                vals['purchase_line_id'] = l.purchase_line_id.id
                vals['purchased_qty']= l.purchase_line_id.product_qty
                vals['purchase_order_name']= l.purchase_line_id.order_id.name
                vals['planned_date'] = l.purchase_line_id.date_planned
                vals['reception_date'] = self.date_invoice
                line = self.env['penalty.purchase.line'].create(vals)
                line.write({'diff':self._calculate_diff_days(vals['planned_date'],vals['reception_date'])})
            else:
                if not l.product_id.penalty_fees:
                    vals['invoice_line_id'] = l.id
                    vals['planned_date'] = self.date_invoice
                    vals['reception_date'] = self.date_invoice
                    line = self.env['penalty.invoice.line'].create(vals)
                    line.write({'diff':self._calculate_diff_days(vals['planned_date'],vals['reception_date'])})

        return {
            'name':_("Pénalités de retard"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'supplier.penalty.fees.wizard',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            }

    @api.multi
    def action_customer_penalty_fees(self):
        penalty_fees_product = self.env['product.product'].search([('penalty_fees','=',True)])
        if not penalty_fees_product:
            raise exceptions.ValidationError("Veuillez configurer un produit pour les pénalités de retard")
        vals={
            'invoice_id':self.id,
            'planned_date': self.date_due or fields.date.today(),
            'base_amount':self.amount_untaxed,
            'total_days':self._calculate_diff_days(self.date_due or str(fields.date.today()), str(fields.date.today()))
              }
        if len(penalty_fees_product) <= 1:
            vals['penalty_fees_product_id'] = penalty_fees_product[0].id
        wizard_id = self.pool.get("customer.penalty.fees.wizard").create(self._cr, self._uid, vals, context=self._context)
        return {
            'name':_("Pénalités de retard"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'customer.penalty.fees.wizard',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            }

    @api.v8
    def invoice_print_auto(self,operation=False):
        html = self.env['report'].with_context({'active_ids':[self.id]}).get_html(self,'account.report_invoice')
        context = self._context.copy()
        context['active_ids'] = self.ids
        pdf = self.pool.get('report').get_pdf(self._cr, self._uid, self.ids,'account.report_invoice',html,context=context)
        if operation :
            html = self.env['report'].with_context({'active_ids':[self.id]}).get_html(self,'portnet_reports.invoice_details_template')
            context = self._context.copy()
            context['active_ids'] = self.ids
            pdf = self.pool.get('report').get_pdf(self._cr, self._uid, self.ids,'portnet_reports.invoice_details_template',html,context=context)
        return True

    @api.multi
    def action_date_assign(self):
        print "in date assign invoice portnet"
        for inv in self:
            res = inv.onchange_payment_term_date_invoice(inv.payment_term.id, inv.date_invoice)
            if res and res.get('value'):
                inv.write(res['value'])
            for l in inv.invoice_line:
                l.write({'date_treasury':inv.prevision_date})
                if l.product_id.is_subscription:
                    print "subscription product"

                    if inv.date_invoice:
                        date_invoice = parser.parse(inv.date_invoice)
                    else:
                        ctx = dict(self._context, lang=inv.partner_id.lang)
                        date_invoice = parser.parse(fields.Date.context_today(self))
                        inv.with_context(ctx).write({'date_invoice':date_invoice })
                    if not l.start_date and not l.end_date:
                        # Adjusting dates to the contract for PCA calculation for subscriptions
                        if inv.contract_id:
                            start_date = parser.parse(inv.contract_id.next_invoice_date) - relativedelta(months=inv.contract_id.periodicity_id.nb_months)
                            l.write({'start_date':start_date,'end_date':(start_date + relativedelta(months=inv.contract_id.periodicity_id.nb_months))-relativedelta(days=1)})
                        else:
                            l.write({'start_date':date_invoice,'end_date':(date_invoice + relativedelta(months=l.product_id.periodicity_id.nb_months))-relativedelta(days=1)})
                        # Adjusting dates to the contract for PCA calculation for subscriptions
                    elif l.start_date and not l.end_date:
                        l.write({'end_date':(parser.parse(l.start_date) + relativedelta(months=l.product_id.periodicity_id.nb_months))-relativedelta(days=1)})

        return True


    @api.multi
    def confirm_paid(self):
        """
        Une fois la facture est payé totalement cette fonction est automatiquement executée.
        :return: un ficheir xml de retour
        """
        self.write({'state': 'paid'})
        self._gen_xml_file(2)
        return True

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.payment_ids:
                for move_line in inv.payment_ids:
                    if move_line.reconcile_partial_id.line_partial_ids:
                        raise except_orm(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        invoice_number = inv.number
        self.write({'state': 'cancel', 'move_id': False, 'invoice_number': invoice_number})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        self._log_event(-1.0, 'Cancel Invoice')
        #self._gen_xml_file(3,invoice_number)
        return True

    ###################

    @api.one
    def _gen_xml_file(self,function,invoice_numb=False):
        print "in gen xml file"

        dirpath=self.env["folder.path.setting"].get_invoices_folder()
        if not dirpath:
            raise exceptions.ValidationError("Erreur d'accès au répértoire de dépôt des factures, veuillez contacter votre administrateur")
        os.chdir(dirpath)

        #La facture doit être crée avant (pièce jointe)
        invoice_attachment = False
        details_attachment = False
        attachments = self.env['ir.attachment'].search([('res_model','=','account.invoice'),('res_id','=',self.id)],order='id desc')
        print "attachments =",attachments
        if attachments:
            for a in attachments:
                if a.name.startswith('INV') and not a.name.endswith('_OP.pdf'):
                    print "invoice a found"
                    invoice_attachment = a
                    break
            for a in attachments:
                if self.op_id and a.name.startswith('INV') and a.name.endswith('_OP.pdf'):
                    print "invoice details a found"
                    details_attachment = a
                    break
                    # TODO : enregistrer le message dans une table plutot que de generer une exception ?
        if not invoice_attachment:
            raise exceptions.ValidationError("Pas de document PDF trouvé pour la facture "+str(self.number))
        # if self.op_id and not details_attachment:
        #     raise exceptions.ValidationError("Pas de document PDF trouvé pour le détail de la facture "+str(self.number))
        # #création document
        newdoc = minidom.Document()
        #création racine xml
        newroot1 = newdoc.createElement('pn:TransmissionFacture')
        newroot1.setAttribute("xmlns:pn", "http://portnet.ma/TransmissionFacture")
        newroot = newdoc.createElement('TransmissionFactureMessage')
        newroot1.appendChild(newroot)
        newdoc.appendChild(newroot1)
            ##création Entête
        header = newdoc.createElement('Entete')
        newroot.appendChild(header)
                ### Numéro d'interchange
        exchange_seq = newdoc.createElement("NumeroMessage")
        message_ref=self.env['ir.sequence'].get('xml.exchange.seq')
        text = newdoc.createTextNode(message_ref)
        exchange_seq.appendChild(text)
        header.appendChild(exchange_seq)
                ### Emetteur
        Emetteur = newdoc.createElement('Emetteur')
        text = newdoc.createTextNode('611ODOO116')
        Emetteur.appendChild(text)
        header.appendChild(Emetteur)
                ### Destinataire
        Destinataire = newdoc.createElement('Destinataire')
        text = newdoc.createTextNode('611PNET00100')
        Destinataire.appendChild(text)
        header.appendChild(Destinataire)
                ### DateMessage
        DateMessage = newdoc.createElement('DateMessage')
        text = newdoc.createTextNode(str(time.strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        DateMessage.appendChild(text)
        header.appendChild(DateMessage)
                ### TypeMessage
        TypeMessage = newdoc.createElement('TypeMessage')
        text = newdoc.createTextNode('INV')
        TypeMessage.appendChild(text)
        header.appendChild(TypeMessage)
                ### Fonction message
        Fonction = newdoc.createElement('Fonction')
        text = newdoc.createTextNode(str(function))
        Fonction.appendChild(text)
        header.appendChild(Fonction)
            ##création balise Opérateur
        operateur = newdoc.createElement('Operateur')
        newroot.appendChild(operateur)
                ### Nom ou raison sociale
        name_rs = newdoc.createElement('Nom')
        text = newdoc.createTextNode(self.partner_id.name)
        name_rs.appendChild(text)
        operateur.appendChild(name_rs)
                ### Operateur
        code = newdoc.createElement('IdentifiantDouane')
        text = newdoc.createTextNode(self.partner_id.code)
        code.appendChild(text)
        operateur.appendChild(code)
                ### Type d'Identification
        type_id = newdoc.createElement("TypeIdentification")
        text = newdoc.createTextNode("IFU")
        type_id.appendChild(text)
        operateur.appendChild(type_id)
                ### Num Identification
        num_identif = newdoc.createElement("NumIdentification")
        text = newdoc.createTextNode('')
        num_identif.appendChild(text)
        operateur.appendChild(num_identif)
                ### Centre
        centre = newdoc.createElement("Centre")
        text = newdoc.createTextNode('')
        centre.appendChild(text)
        operateur.appendChild(centre)
                ### Identifiant fiscal unique
        ifu = newdoc.createElement("IdFiscalUnique")
        text = newdoc.createTextNode(self.partner_id.ifu or "None")
        ifu.appendChild(text)
        operateur.appendChild(ifu)
            ##création balise Facture
        facture = newdoc.createElement('Facture')
        newroot.appendChild(facture)
                ### Numéro de la facture
        invoice_number = newdoc.createElement('NumeroFacture')
        text = newdoc.createTextNode(function == 3 and str(invoice_numb) or self.number)
        invoice_number.appendChild(text)
        facture.appendChild(invoice_number)
                ### Type de facture
        invoice_type = newdoc.createElement('TypeFacture')
        text = newdoc.createTextNode(self.majoration and '2' or '1')
        invoice_type.appendChild(text)
        facture.appendChild(invoice_type)
                ### Description de la facture
        invoice_type = newdoc.createElement('DescriptionFacture')
        desc = ' / '.join(line.name for line in self.invoice_line)
        text = newdoc.createTextNode(desc)
        invoice_type.appendChild(text)
        facture.appendChild(invoice_type)
                ### Référence de la facture principale
        principal_invoice_number = newdoc.createElement('ReferenceFacturePrincipale')
        text = newdoc.createTextNode(self.majoration and self.original_invoice_id.number or '')
        principal_invoice_number.appendChild(text)
        facture.appendChild(principal_invoice_number)
                ### Date de la facture
        invoice_date = newdoc.createElement('DateFacture')
        text = newdoc.createTextNode(str(parser.parse(self.date_invoice).strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        invoice_date.appendChild(text)
        facture.appendChild(invoice_date)
                ### Date d'échéance de règlement
        invoice_due_date = newdoc.createElement("DateReglement")
        text = newdoc.createTextNode(str(parser.parse(self.date_due).strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        invoice_due_date.appendChild(text)
        facture.appendChild(invoice_due_date)
                ### Statut facture
        invoice_status = newdoc.createElement('StatutFacture')
        status_str = {'open':'2','paid': '1','cancel':'3'}
        text = newdoc.createTextNode(status_str[self.state])
        invoice_status.appendChild(text)
        facture.appendChild(invoice_status)
                ### Devise
        invoice_currency = newdoc.createElement('Devise')
        text = newdoc.createTextNode(self.currency_id.symbol)
        invoice_currency.appendChild(text)
        facture.appendChild(invoice_currency)
                ### Montant HT
        amount_untaxed = newdoc.createElement('MontantHT')
        text = newdoc.createTextNode(str(self.amount_untaxed))
        amount_untaxed.appendChild(text)
        facture.appendChild(amount_untaxed)
                ### Montant TTC
        amount_total = newdoc.createElement('MontantTTC')
        text = newdoc.createTextNode(str(self.amount_total))
        amount_total.appendChild(text)
        facture.appendChild(amount_total)
                ### Date Annulation
        if function == 3:
            cancel_date = newdoc.createElement('DateAnnulation')
            text = newdoc.createTextNode(str(time.strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
            cancel_date.appendChild(text)
            facture.appendChild(cancel_date)
            ##création balise Fichier
        file1 = newdoc.createElement('pn:FichierInfo')
        file = newdoc.createElement('Fichier')
        file1.appendChild(file)
        facture.appendChild(file1)
                ### Nom du fichier
        filename = newdoc.createElement('Nom')
        text = newdoc.createTextNode(invoice_attachment.name)
        filename.appendChild(text)
        file.appendChild(filename)
                ### Description
        content_desc = newdoc.createElement('Description')
        # if self.op_id:
        #     text = newdoc.createTextNode("Facture / Détails des opérations")
        # else:
        text = newdoc.createTextNode("Facture")
        content_desc.appendChild(text)
        file.appendChild(content_desc)
                ### Contenu
        content = newdoc.createElement('Contenu')
        # if self.op_id:
        #     text = newdoc.createTextNode(invoice_attachment.datas+details_attachment.datas)
        # else:
        #text = newdoc.createTextNode(base64.encodestring(invoice_attachment.datas))
        text = newdoc.createTextNode(invoice_attachment.datas)
        content.appendChild(text)
        file.appendChild(content)
            ##création balise Prestation
        prestation = newdoc.createElement('pn:Prestation')
        newroot.appendChild(prestation)
                ### Prestation
        prest = newdoc.createElement("PrestationInfo")
        prestation.appendChild(prest)
                ### Type de prestation
        type_doc_op = newdoc.createElement("TypePrestation")
        text = newdoc.createTextNode(self.op_id and 'ES' or 'AB')
        type_doc_op.appendChild(text)
        prest.appendChild(type_doc_op)
                ### Type de document/opération
        type_prest = newdoc.createElement("TypeDocument")
        text = newdoc.createTextNode(self.op_id and 'DN' or 'AB')
        type_prest.appendChild(text)
        prest.appendChild(type_prest)
                ### Référence
        ref = newdoc.createElement("Reference")
        text = newdoc.createTextNode(str(self.invoice_line[0].product_id.code or self.invoice_line[0].product_id.name))
        ref.appendChild(text)
        prest.appendChild(ref)
                ### Date fin
        end_date = newdoc.createElement("DateFin")
        if self.op_id:
            text = newdoc.createTextNode(str(parser.parse(self.period_id.date_stop).strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        elif self.contract_id:
            text = newdoc.createTextNode(str(parser.parse(self.contract_id.date).strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        else:
            text = newdoc.createTextNode(str(parser.parse(self.date_due).strftime("%Y-%m-%d %H:%M:%S")).replace(' ','T'))
        end_date.appendChild(text)
        prest.appendChild(end_date)


        #FILE DEPOSIT
        xml_invoice = newdoc.toprettyxml(encoding="UTF-8")
        date_now_str = str(time.strftime("%Y-%m-%d %H:%M:%S"))
        date_now_str = date_now_str.replace('-','')
        date_now_str = date_now_str.replace(':','')
        date_now_str = date_now_str.replace(' ','T')
        code_edi_odoo = "99999999"
        message_type = 'INV'
        filename_txt = code_edi_odoo+message_type+date_now_str+self.env['ir.sequence'].get('xml.filename.seq')
        text = newdoc.createTextNode(filename_txt)
        f =  open(filename_txt+".xml", "ab+")
        f.write(xml_invoice)
        f.close()

        #HISTORY
        self.env['xml.history'].sudo().create({'invoice_id':self.id,'date':datetime.now(),
                                        'invoice_number':self.number,'invoice_state':self.state,
                                        'customer_code':self.partner_id.code,'customer_name':self.partner_id.name,
                                        'type':'invoice_deposit','filename':filename_txt,'messageref':message_ref})

        return True


    @api.model
    def _generate_all_invoices(self):
        # run cron only on weekdays (no weekends)
        weekno = datetime.today().weekday()
        if weekno>=5:
            return True
        # run cron only on weekdays (no weekends)
        monthly_cron=True
        databse_id=self.env['op.store.db.settings'].search([('state','=','confirmed')])
        if not databse_id :
            code="DBSTORE_ERROR_"
            output="Aucune base de stockage confirmée trouvée"
            self.env['report.exception'].set_exception(code,output)
        dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
        partner_ids=self.env["res.partner"].search([('customer','=',True),('is_company','=',True),('categ_id.op_type_ids','!=',[])])
        period_id=databse_id.period_id
        #Création de l'entité de facturation des opérations
        invoicing_op_id = False
        if period_id:
            existing_period = self.env['invoicing.operation'].search([('period_id','=',period_id.id)])
            if not existing_period:
                invoicing_op_id = self.env['invoicing.operation'].create({'period_id':period_id.id})
            else:
                invoicing_op_id = existing_period[0]
        #Création de l'entité de facturation des opérations
        for partner in partner_ids :
            self.env["customer.invoicing.wizard"]._cron_action_confirm(dbcr,partner,period_id,invoicing_op_id.id)
        next_period=self.env['account.period'].next_period(period_id,1)
        databse_id.write({'period_id':next_period.id})
        dbcr.execute("COMMIT")


    @api.multi
    def apply_pricelist(self, pricelist, product_id, qty, amount, date):
        product = self.env['product.product'].browse(product_id)
        if not pricelist:
            return amount
        else:
            ctx = dict(
                uom=product.uom_id.id,
                date=date,
            )
            #taxes
            account = product.property_account_income or product.categ_id.property_account_income_categ
            taxes = product.taxes_id or account.tax_ids
            fpos = self.env['account.fiscal.position'].browse(False)
            fp_taxes = fpos.map_tax(taxes)
            #taxes
            price = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                    product.id, qty or 1.0, self.partner_id.id, ctx)[pricelist]
            if price is False:
                return amount
            else:
                price = self.pool['account.tax']._fix_tax_included_price(self._cr, self._uid, price, taxes, fp_taxes.ids)
                amount = price
                #print "price unit 3 =",price_unit
                return amount


    @api.multi
    def action_create_invoice(self,date_invoice,partner_id,operation_id,product_id,qty,line_store_ids):
        """
        :param date_invoice: égale à la date invoice à partir de la facturation à la demande ou bien date fin période ,
                             égale à la date fin période pour la facturation par cron mensuel
        :param partner_id: l'objet client
        :param operation_id: l'objet operation
        :param product_id: le produit à facturer
        :param qty: la quantié ==> nombre des lignes des opérations à facturer pour la période.
        :param line_store_ids: les ids des opérations dans le reférentiel de stockage
        :return: l'id de la facture crée
        """
        invoice_obj = self.env['account.invoice']
        if partner_id.property_payment_term:
            payment_term_id = partner_id.property_payment_term.id
        elif partner_id.categ_id and partner_id.categ_id.payment_term_id:
            payment_term_id = partner_id.categ_id.payment_term_id.id
        else:
            payment_term_id = False

        if partner_id.property_account_position:
            fiscal_position_id = partner_id.property_account_position.id
        elif partner_id.categ_id and partner_id.categ_id.fiscal_position_id:
            fiscal_position_id = partner_id.categ_id.fiscal_position_id.id
        else:
            fiscal_position_id = False

        if partner_id.property_product_pricelist:
            pricelist_id = partner_id.property_product_pricelist
        elif partner_id.categ_id.pricelist_id :
             pricelist_id = partner_id.categ_id.pricelist_id
        else :
             raise exceptions.ValidationError("Merci de definir une liste de prix pour le client %s"%partner_id.name)

        vals = {
            'origin': "OP STORE",
            'date_invoice': date_invoice,
            'user_id': self._uid,
            'partner_id': partner_id.id,
            'op_id':operation_id,
            'account_id': partner_id.property_account_receivable.id,
            'type': 'out_invoice',
            'company_id': self.env.user.company_id.id,
            'currency_id': pricelist_id and pricelist_id.currency_id.id or self.env.user.company_id.currency_id.id,
            'pricelist_id':pricelist_id.id,
            'payment_term':payment_term_id,
            'fiscal_position':fiscal_position_id,
            'op_qty':qty,
        }
        if  len(line_store_ids) > 1 :
            vals['line_store_ids']=tuple(line_store_ids)
        else :
            vals['line_store_ids']="("+str(line_store_ids[0])+")"

        invoice = invoice_obj.create(vals)
        account_id = product_id.property_account_income.id
        if not account_id:
            account_id = product_id.categ_id.property_account_income_categ.id
        if not account_id:
            raise exceptions.ValidationError("Merci de définir un compte de revenues pour le produit")
        #taxes
        account = product_id.property_account_income or product_id.categ_id.property_account_income_categ
        taxes = product_id.taxes_id or account.tax_ids
        fpos = self.env['account.fiscal.position'].browse(False)
        fp_taxes = fpos.map_tax(taxes)
        #taxes

        final_amount = self.apply_pricelist(pricelist_id.id, product_id.id, qty, product_id.list_price, date_invoice)
        line_vals = {   'name': product_id.name,
                        'account_id': account_id,
                        'product_id': product_id.id,
                        'product_category_id':product_id.categ_id.id,
                        'quantity': qty,
                        'price_unit': final_amount,
                        'uos_id': product_id.uom_id.id,
                        'account_analytic_id': False,
                        'budget_line_id':False,
                        'invoice_id': invoice.id,
                        'invoice_line_tax_id':[(6, 0, fp_taxes.ids)],

                        }



        #Update account_id on line depending on fiscal position
        fpos = self.env['account.fiscal.position'].browse(fiscal_position_id)
        account = fpos.map_account(account)
        if account:
            line_vals['account_id'] = account.id
            account_id = account.id
        #Update account_id on line depending on fiscal position


        #Ligne budgétaire et compte analytique pour le calcul du budget
        fiscalyear_id = self.env['account.fiscalyear'].search([('date_start','<=',date_invoice),('date_stop','>=',date_invoice)])
        if fiscalyear_id:
            settings = self.env['budget.setting'].search([('product_id','=',product_id.id),('account_id','=',account_id),('fiscalyear_id','=',fiscalyear_id[0].id)])
            if settings:
                line_vals['budget_item_id'] = settings[0].budget_line_id.id
                line_vals['account_analytic_id'] = settings[0].account_analytic_id.id
            else:
                raise exceptions.ValidationError("Veuillez configurer un paramètrage budget pour l'article "+product_id.name)
        #Ligne budgétaire et compte analytique pour le calcul du budget


        #Changement de la quantité à 1 si le prix est forfaitaire
        operation = self.env["operation.type"].browse(operation_id)
        if operation and operation.fixed_price:
            line_vals['quantity'] = 1
        #Changement de la quantité à 1 si le prix est forfaitaire
        line = invoice_obj.invoice_line.create(line_vals)
        invoice.button_reset_taxes()
        # workflow.trg_validate(self._uid, 'account.invoice', invoice.id, 'invoice_open', self._cr)
        # #MAJ de la quantité si le prix est forfaitaire
        # operation = self.env["operation.type"].browse(operation_id)
        # if operation and operation.fixed_price:
        #     line.quantity = qty
        #     line.price_subtotal = line.price_unit
        #     line.invoice_id.amount_untaxed = line.price_unit
        #     line.invoice_id.amount_total = line.price_unit + line.invoice_id.amount_tax
        # #MAJ de la quantité si le prix est forfaitaire
        return invoice.id

    @api.multi
    def validate_operation_invoice(self):
        databse_id=self.env['op.store.db.settings'].search([('state','=','confirmed')])
        if not databse_id :
            raise except_orm (_("Configuration Base Stockage "),
                                      _("Pas de base confirmée trouvée"))
        dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
        dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
        #Validating the invoice
        self.button_reset_taxes()
        workflow.trg_validate(self._uid, 'account.invoice', self.id, 'invoice_open', self._cr)
        #MAJ de la quantité si le prix est forfaitaire
        if self.op_id and self.op_id.fixed_price:
            for line in self.invoice_line:
                line.quantity = self.op_qty
                line.price_subtotal = line.price_unit
                line.invoice_id.amount_untaxed = line.price_unit
                line.invoice_id.amount_total = line.price_unit + line.invoice_id.amount_tax
        #MAJ du statut des lignes d'opérations dans la base de stockage
        if self.line_store_ids:
            line_store_ids = []
            str_ids = self.line_store_ids.replace('(','')
            str_ids = str_ids.replace(')','')
            str_ids = str_ids.split(',')
            for id in str_ids:
                line_store_ids.append(int(id))
            self.write({'date_invoice':datetime.now().date()})
            self.move_id.action_update_maturity_dates()
            self.invoice_print_auto(operation=True)
            self.action_send_mail_auto()
			# TODO : check function==9 behaviour
            self._gen_xml_file(9)
            if len (line_store_ids) >1 :
                req="update invoice_line_store set state='done', in_progress=false, invoice_id='%s' where id in %s"%(self.id,tuple(line_store_ids))
            else :
                req="update invoice_line_store set state='done', in_progress=false, invoice_id='%s' where id = %s"%(self.id,line_store_ids[0])
            print req
            dbcr.execute(req)
            dbcr.execute("COMMIT")


    @api.multi
    def _get_op_structure(self):
        if self.op_id:
            header=[]
            for l in self.op_id.line_ids:
                vals ={'name':l.name,
                       'field':l.field,
                       'data_type':l.data_type,
                       'required':l.required,
                       'report':l.report,
                       'filter':l.filter
                }
                header.append(vals)
            if header:
                return header
            else:
                return False
        else:
            return False

    @api.multi
    def _get_op_lines(self):
        op_struct = self._get_op_structure()
        if op_struct:
            databse_id=self.env['op.store.db.settings'].search([('is_db_store','=',True)])
            dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
            if self.line_store_ids:
                req = "SELECT "
                for op in op_struct:
                    if op['report'] == True:
                        req+=str(op['field'])+","
                req = req[:-1]
                #req+=" FROM invoice_line_store limit 50"
                c=self.line_store_ids
                l=len(c)
                if c[l-2:]==',)' :
                    c=c[:l-2]+')'
                req+=" FROM invoice_line_store WHERE id in "+c
                dbcr.execute(req)
                res = dbcr.fetchall()
                if res:
                    return res
                else:
                    return False
            else:
                return False
                raise exceptions.ValidationError("Pas de détails pour cette facture")
        else:
            return False

    @api.one
    @api.depends('partner_id')
    def _get_categ_pricelist(self):
        if self.partner_id:
            self.categ_pricelist_id = self.partner_id.categ_id.pricelist_id

    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id,date_invoice):
        print 'lllllll',payment_term_id,'---',date_invoice
        value={}
        term={}
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        if not payment_term_id:
            # To make sure the invoice due date should contain due date which is
            # entered by user when there is no payment term defined
            value['date_due']=self.date_due or date_invoice
        else:
            pterm = self.env['account.payment.term'].browse(payment_term_id)
            pterm_list = pterm.compute(value=1, date_ref=date_invoice)[0]
            if pterm_list:
               value['date_due']=max(line[0] for line in pterm_list)
            else:
               raise except_orm(_('Insufficient Data!'),
                _('The payment term of supplier does not have a payment term line.'))
        if not self.partner_id or (self.partner_id and not self.partner_id.treasury_term_id):
            value['prevision_date']=value['date_due']
        elif self.partner_id and self.partner_id.treasury_term_id:
            trterm = self.env['account.payment.term'].browse(self.partner_id.treasury_term_id.id)
            trterm_list = trterm.compute(value=1, date_ref=date_invoice)[0]
            if trterm_list:
               value['prevision_date']=max(line[0] for line in trterm_list)
        term['value']=value
        print 'eeeee',term
        return term

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False,treasury_term_id=False, partner_bank_id=False, company_id=False, context=None):
        account_id = False
        payment_term_id = False
        treasury_term=False
        fiscal_position = False
        bank_id = False
        pricelist_id = False

        if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            rec_account = p.property_account_receivable
            pay_account = p.property_account_payable
            treasury_term=p.treasury_term_id.id
            if company_id:
               if p.property_account_receivable.company_id and \
                        p.property_account_receivable.company_id.id != company_id and \
                        p.property_account_payable.company_id and \
                        p.property_account_payable.company_id.id != company_id:
                    prop = self.env['ir.property']
                    rec_dom = [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)]
                    pay_dom = [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)]
                    res_dom = [('res_id', '=', 'res.partner,%s' % partner_id)]
                    print "rec_dom =",rec_dom
                    print "res_dom =",res_dom
                    rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom)
                    pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom)
                    rec_account = rec_prop.get_by_record(rec_prop)
                    pay_account = pay_prop.get_by_record(pay_prop)
                    if not rec_account and not pay_account:
                        action = self.env.ref('account.action_account_config')
                        msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                        raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund'):
                account_id = rec_account.id
                if not p.property_payment_term and p.categ_id and p.categ_id.payment_term_id:
                    payment_term_id = p.categ_id.payment_term_id.id
                else:
                    payment_term_id = p.property_payment_term.id
            else:
                account_id = pay_account.id
                if not p.property_supplier_payment_term and p.categ_id and p.categ_id.payment_term_id:
                    payment_term_id = p.categ_id.payment_term_id.id
                else:
                    payment_term_id = p.property_supplier_payment_term.id
            fiscal_position = p.property_account_position.id
            if p.property_account_position:
                fiscal_position = p.property_account_position.id
            elif p.categ_id and p.categ_id.fiscal_position_id:
                fiscal_position = p.categ_id.fiscal_position_id.id
            else:
                fiscal_position = False
            bank_id = p.bank_ids and p.bank_ids[0].id or False

            # pricelist
            if p.categ_id: pricelist_id = p.categ_id.pricelist_id.id
            if not p.categ_id and not p.categ_id.pricelist_id and p.property_product_pricelist:
                pricelist_id = p.property_product_pricelist.id
            # pricelist
        print 'rrrr',treasury_term
        print 'tttt',payment_term_id
        result = {'value': {
            'account_id': account_id,
            'payment_term': payment_term_id,
            'treasury_term_id':treasury_term,
            'fiscal_position': fiscal_position,
            'pricelist_id': pricelist_id,
        }}

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id
        if payment_term != payment_term_id or treasury_term_id !=treasury_term :
            if payment_term_id  :
                to_update = self.onchange_payment_term_date_invoice(payment_term_id,date_invoice)
                print 'mmmm',to_update
                result['value'].update(to_update.get('value', {}))
            else:
                result['value']['date_due'] = False
        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(bank_id)
            result['value'].update(to_update.get('value', {}))
        print 'ddd',result
        return result

    @api.multi
    def unlink(self):
        current_user = self.env['res.users'].browse(self._uid)
        invoice_list = ''
        for invoice in self:
            if invoice.state == 'cancel':
                if self.env['res.users'].has_group('portnet_invoicing.group_cancelled_invoice_removal'):
                    invoice_list = invoice_list + invoice.invoice_number + ','
                    pass
                else:
                    raise Warning(_('Vous ne pouvez pas supprimer une facture annulée ou brouillon déjà validée (qui possède un numéro)'))
            elif invoice.state == 'draft' and invoice.invoice_number:
                if self.env['res.users'].has_group('portnet_invoicing.group_cancelled_invoice_removal'):
                    invoice_list = invoice_list + invoice.invoice_number + ','
                    pass
                else:
                    raise Warning(_('Vous ne pouvez pas supprimer une facture annulée ou brouillon déjà validée (qui possède un numéro)'))
            elif invoice.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
            elif invoice.internal_number:
                raise Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))

        deleted = models.Model.unlink(self)
        if invoice_list != '' and deleted:
            deleted_invoices_obj = self.pool.get('deleted.invoices')
            deleted_invoices_obj.create(self._cr,1,{'user':current_user.partner_id.name,
                                                            'invoice_delete_date':datetime.today(),
                                                            'invoice_numbers': invoice_list
                                                        })
        return deleted

account_invoice()


class account_invoice_line(models.Model):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    move_id = fields.Many2one(comodel_name="stock.move", string="Mouvement", required=False)
    budget_item_id=fields.Many2one('crossovered.budget.lines',string='Ligne Budgétaire')
    budget_line_id=fields.Many2one('crossovered.budget.lines',string='Ligne Budgétaire',required=False,domain=[('crossovered_budget_id.actif','=',True)])
    is_subscription = fields.Boolean(string="Abonnement", related="product_id.is_subscription")

    def move_line_get_item(self, cr, uid, line, context=None):
          res = super(account_invoice_line, self).move_line_get_item(
            cr, uid, line, context=context)
          res['start_date'] = line.start_date
          res['end_date'] = line.end_date
          res['date_treasury'] = line.invoice_id.prevision_date
          res['budget_line_id'] = line.budget_item_id and line.budget_item_id.id or False
          res['budget_item_id'] = res['budget_line_id']
          return res

    @api.multi
    def product_id_change2(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None,pricelist=False, date_invoice=False):
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        self = self.with_context(company_id=company_id, force_company=company_id)

        if not partner_id:
            raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain': {'uos_id': []}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain': {'uos_id': []}}


        values = {}

        part = self.env['res.partner'].browse(partner_id)
        fpos = self.env['account.fiscal.position'].browse(fposition_id)

        if part.lang:
            self = self.with_context(lang=part.lang)
        product = self.env['product.product'].browse(product)
        if product.is_subscription:
            raise except_orm(_('Abonnement'), _("Les factures d'abonnement sont générées automatiquement!"))

        values['name'] = product.partner_ref
        if type in ('out_invoice', 'out_refund'):
            account = product.property_account_income or product.categ_id.property_account_income_categ
        else:
            account = product.property_account_expense or product.categ_id.property_account_expense_categ
        account = fpos.map_account(account)
        if account:
            values['account_id'] = account.id

        if type in ('out_invoice', 'out_refund'):
            taxes = product.taxes_id or account.tax_ids
            if product.description_sale:
                values['name'] += '\n' + product.description_sale
        else:
            taxes = product.supplier_taxes_id or account.tax_ids
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase

        fp_taxes = fpos.map_tax(taxes)
        values['invoice_line_tax_id'] = fp_taxes.ids

        if type in ('in_invoice', 'in_refund'):
            if price_unit and price_unit != product.standard_price:
                values['price_unit'] = price_unit
            else:
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.standard_price, taxes, fp_taxes.ids)
        else:
            values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.lst_price, taxes, fp_taxes.ids)

        values['uos_id'] = product.uom_id.id
        if uom_id:
            uom = self.env['product.uom'].browse(uom_id)
            if product.uom_id.category_id.id == uom.category_id.id:
                values['uos_id'] = uom_id

        domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}

        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)

        if company and currency:
            if company.currency_id != currency:
                values['price_unit'] = values['price_unit'] * currency.rate

            if values['uos_id'] and values['uos_id'] != product.uom_id.id:
                values['price_unit'] = self.env['product.uom']._compute_price(
                    product.uom_id.id, values['price_unit'], values['uos_id'])


        # get unit price with pricelist

        warning={}
        warning_msgs = ''
        if type== 'out_invoice':
            if not pricelist:
                warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                        'Please set one before choosing a product.')
                warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
            else:
                ctx = dict(
                    context,
                    uom=uom_id or values.get('product_uom'),
                    date=date_invoice,
                )
                price = self.pool.get('product.pricelist').price_get(self._cr, self._uid, [pricelist],
                        product.id, qty or 1.0, partner_id, ctx)[pricelist]
                if price is False:
                    warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist.")

                    warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
                else:
                    price = self.pool['account.tax']._fix_tax_included_price(self._cr, self._uid, price, taxes, values['invoice_line_tax_id'])
                    values.update({'price_unit': price})
                    if context.get('uom_qty_change', False):
                        values = {'price_unit': price}
                        if values.get('product_uos_qty'):
                            values['product_uos_qty'] = values['product_uos_qty']
                        return {'value': values, 'domain': {}, 'warning': False}
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }

        return {'value': values, 'domain': domain, 'warning': warning}


    @api.multi
    def uos_id_change2(self, product, uom, qty=0, name='', type='out_invoice', partner_id=False,
            fposition_id=False, price_unit=False, currency_id=False, company_id=None,pricelist=False, date_invoice=False):
        context = self._context
        company_id = company_id if company_id != None else context.get('company_id', False)
        self = self.with_context(company_id=company_id)

        result = self.product_id_change2(
            product, uom, qty, name, type, partner_id, fposition_id, price_unit,
            currency_id, company_id=company_id,pricelist=pricelist,date_invoice=date_invoice
        )
        warning = {}
        if not uom:
            result['value']['price_unit'] = 0.0
        if product and uom:
            prod = self.env['product.product'].browse(product)
            prod_uom = self.env['product.uom'].browse(uom)
            if prod.uom_id.category_id != prod_uom.category_id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure is not compatible with the unit of measure of the product.'),
                }
                result['value']['uos_id'] = prod.uom_id.id
        if warning:
            result['warning'] = warning
        return result

    @api.multi
    def onchange_account_id2(self, product_id, partner_id, inv_type, fposition_id, account_id,pricelist=False, date_invoice=False):
        value = {'budget_item_id': False}
        domain = {'budget_item_id': [('crossovered_budget_id.actif','=',True)]}
        res = {'value':value,'domain':domain}
        if not account_id:
            return res
        unique_tax_ids = []
        account = self.env['account.account'].browse(account_id)
        if not product_id:
            fpos = self.env['account.fiscal.position'].browse(fposition_id)
            unique_tax_ids = fpos.map_tax(account.tax_ids).ids
        else:
            product_change_result = self.product_id_change2(product_id, False, type=inv_type,
                partner_id=partner_id, fposition_id=fposition_id, company_id=account.company_id.id,pricelist=pricelist,date_invoice=date_invoice)
            if 'invoice_line_tax_id' in product_change_result.get('value', {}):
                unique_tax_ids = product_change_result['value']['invoice_line_tax_id']
        res['value'].update({'invoice_line_tax_id': unique_tax_ids})

        if date_invoice:
            domaindate = date_invoice
            res['domain']['budget_item_id'].append(('date_from', '<', domaindate))
            res['domain']['budget_item_id'].append(('date_to', '>', domaindate))
        if account.budget_post_ids:
            budget_lines = account.budget_post_ids[0].crossovered_budget_line
            budget_line_ids = [budget_line.id for budget_line in budget_lines]
            res['domain']['budget_item_id'].append(('id', 'in', budget_line_ids))
        return res




account_invoice_line()

class deleted_invoices(models.Model):
    _name = 'deleted.invoices'

    user = fields.Char('Utilisateur')
    invoice_delete_date = fields.Datetime('Date de suppression')
    invoice_numbers = fields.Char('Liste des numéros de factures')

deleted_invoices()