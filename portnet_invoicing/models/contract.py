# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time
from openerp import workflow

class advanced_contract(models.Model):
    _name = "res.contract"
    _inherit = 'mail.thread'

    name = fields.Char(string="Nom", required=False, )
    partner_categ_id = fields.Many2one(comodel_name="res.partner.category", string="Catégorie client", required=True,)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Client",required=False)
    product_category_id = fields.Many2one(comodel_name="product.category", string="Catégorie du produit",required=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Produit",required=True)
    amount = fields.Float(string="Montant du contrat", digits=(6,2))
    date_start = fields.Date(string="Date de début", default=fields.Date().today())
    date = fields.Date(string="Date de fin")
    first_invoice_date = fields.Date(string="Date début facturation")
    next_invoice_date = fields.Date(string="Date prochaine facturation")
    anticipated_invoice_date = fields.Date(string="Date de facture anticipée")
    periodicity_id = fields.Many2one(comodel_name="res.periodicity", string="Périodicité",required=True)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Devise",default=lambda self: self.env.user.company_id.currency_id.id)
    diff_months = fields.Integer(string="Nombre de mois")
    state = fields.Selection(string="Statut", selection=[('draft', 'Brouillon'), ('pending', 'En cours'), ('closed', 'Clôturé') ], default='draft')
    tacite = fields.Boolean(string="Tacite de reconduction")
    is_template = fields.Boolean(string="Modèle de contrat ?")
    template_id = fields.Many2one(comodel_name="res.contract", string="Modèle de contrat",domain=[('is_template','=',True)],required=False)
    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Liste de prix", required=False, domain=[('active','=',True),('type','=','sale')])
    message_ids =  fields.One2many('mail.message', 'res_id',
                                   domain=lambda self: [('model', '=', self._name)],
                                   auto_join=True,
                                   string='Messages',
                                   help="Messages and communication history")

    # Notification Clients of Payment Before Next Invoice Date of Contract : Created by Mouad Ghandi

    @api.model
    def _cron_email_two_months_before_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff == 60 and ctr.partner_id.categ_id != False and ctr.partner_id.categ_id.be_notified:
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                print "", ctr.partner_id.name
                if not open_invoices:
                    print "I am in Two Months"
                    ctr.action_send_mail_auto_notif(
                        'portnet_invoicing.email_template_notif_email_two_months_before_next_invoice_date')
                    self._cr.commit()
                    print "", ctr.partner_id.name

    @api.model
    def _cron_email_one_month_before_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff == 30 and ctr.partner_id.categ_id != False and ctr.partner_id.categ_id.be_notified:
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                if not open_invoices:
                    ctr.action_send_mail_auto_notif(
                        'portnet_invoicing.email_template_notif_email_one_months_before_next_invoice_date')
                    self._cr.commit()
                    print "", ctr.partner_id.name

    @api.model
    def _cron_email_at_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff == 0 and ctr.partner_id.categ_id != False and ctr.partner_id.categ_id.be_notified:
                print "", ctr.partner_id.name
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                if not open_invoices:
                    ctr.action_send_mail_auto_notif(
                        'portnet_invoicing.email_template_notif_email_at_contract_next_invoice_date')
                    self._cr.commit()
                    print "", ctr.partner_id.name

    @api.model
    def _cron_email_four_months_after_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d1 - d2).days
            if daysDiff == 120 and ctr.partner_id.categ_id != False and ctr.partner_id.categ_id.be_notified:
                #print "", ctr.partner_id.name
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                new_paid_invoices = self.env['account.invoice'].search(
                    [('date_invoice', '>', ctr.next_invoice_date), ('state', '=', 'paid'),
                     ('contract_id', '=', ctr.id)])
                if not open_invoices:
                    #print "2_ There is Open Invoices ....."
                    if not new_paid_invoices:
                        print "3_ There is Open Invoices ....."
                        ctr.action_send_mail_auto_notif(
                            'portnet_invoicing.email_template_notif_email_four_months_after_next_invoice_date')
                        self._cr.commit()
                        print "", ctr.partner_id.name

    @api.model
    def _cron_email_six_months_after_contract_next_invoice_date(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d1 - d2).days
            if daysDiff == 180 and ctr.partner_id.categ_id != False and ctr.partner_id.categ_id.be_notified:
                print "", ctr.partner_id.name
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                new_paid_invoices = self.env['account.invoice'].search(
                    [('date_invoice', '>', ctr.next_invoice_date), ('state', '=', 'paid'),
                     ('contract_id', '=', ctr.id)])
                if not open_invoices:
                    if not new_paid_invoices:
                        ctr.action_send_mail_auto_notif(
                         'portnet_invoicing.email_template_notif_email_six_months_after_next_invoice_date')
                        self._cr.commit()
                        print "", ctr.partner_id.name

    # End of Notifs

    @api.model
    def _cron_tacite_reconduction(self):
        # run cron only on weekdays (no weekends)
        weekno = datetime.today().weekday()
        if weekno>=5:
            return True
        today = datetime.now().date()
        # First we have to Calculate the anticipated invoice dates for all contracts depending
        # on the number of months configured in customer categories
        contracts = self.search([('is_template','=',False),('state','=','pending')])
        for ctr in contracts:
            print ctr.id
            months_in_advance = ctr.partner_id.categ_id.invoicing_advance_in_months
            if months_in_advance > 0:
                anticipated_invoice_date = parser.parse(ctr.next_invoice_date).date() - relativedelta(months=months_in_advance)
                if anticipated_invoice_date != ctr.anticipated_invoice_date:
                    print "dates  =",ctr.name,anticipated_invoice_date
                    ctr.anticipated_invoice_date = anticipated_invoice_date
            else:
                ctr.anticipated_invoice_date = ctr.next_invoice_date
        self._cr.commit()
        #Generating invoices
        contracts = self.search([('anticipated_invoice_date','<=',str(today)),('is_template','=',False),('state','=','pending'),('tacite','=',True)])
        print "len ==",len(contracts)
        for c in contracts:
            c.write({'next_invoice_date':parser.parse(c.next_invoice_date) + relativedelta(months=c.periodicity_id.nb_months),
                     'anticipated_invoice_date':parser.parse(c.anticipated_invoice_date) + relativedelta(months=c.periodicity_id.nb_months)})
            c.action_create_invoice(str(today),renewal=True)
            self._cr.commit()

        return True

    @api.model
    def _cron_anticipated_dates_calculation(self):
        today = datetime.now().date()
        # First we have to Calculate the anticipated invoice dates for all contracts depending on the number of months configured in customer categories
        contracts = self.search([('is_template','=',False),('state','=','pending')])
        for ctr in contracts:
            print ctr.id
            months_in_advance = ctr.partner_id.categ_id.invoicing_advance_in_months
            if months_in_advance > 0:
                anticipated_invoice_date = parser.parse(ctr.next_invoice_date).date() - relativedelta(months=months_in_advance)
                if anticipated_invoice_date != ctr.anticipated_invoice_date:
                    ctr.anticipated_invoice_date = anticipated_invoice_date
            else:
                ctr.anticipated_invoice_date = ctr.next_invoice_date
        return True

    @api.model
    def _cron_email_two_months_before_contract_next_invoice_date_paid(self):
        date_format = '%Y-%m-%d'
        today = (datetime.today()).strftime(date_format)
        d1 = datetime.strptime(today, date_format)
        contracts = self.search([('tacite', '=', True), ('state', '=', 'pending')])
        for ctr in contracts:
            next_invoice_date = str(ctr.next_invoice_date)
            d2 = datetime.strptime(next_invoice_date, date_format)
            daysDiff = (d2 - d1).days
            if daysDiff == 61:
                open_invoices = None
                open_invoices = self.env['account.invoice'].search(
                    [('state', '=', 'open'), ('contract_id', '=', ctr.id)])
                if not open_invoices:
                    ctr.action_send_mail_auto_notif(
                        'portnet_invoicing.email_template_edi_invoice_portnet_two_month_before_anniversary')
                    self._cr.commit()

    @api.multi
    def action_send_mail_auto_notif(self, template_id):
        """ Sends a notification mail
        """
        # template = self.env.ref('portnet_invoicing.email_template_edi_invoice_portnet_two_month_before_anniversary', False)
        template = self.env.ref(template_id, False)
        context = self._context.copy()
        context['default_model'] = 'res.contract'
        context['default_res_id'] = self.id
        context['default_use_template'] = bool(template)
        context['default_template_id'] = template.id
        context['default_composition_mode'] = 'comment'
        self.pool.get('email.template').send_mail(self._cr, self._uid, template.id, context['default_res_id'], True,
                                                  context=context)

    @api.one
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

    @api.one
    def action_create_invoice(self, date_invoice, renewal=False):
        #invoice gen

        if self.partner_id.property_payment_term:
            payment_term_id = self.partner_id.property_payment_term.id
        elif self.partner_id.categ_id and self.partner_id.categ_id.payment_term_id:
            payment_term_id = self.partner_id.categ_id.payment_term_id.id
        else:
            payment_term_id = False

        if self.partner_id.property_account_position:
            fiscal_position_id = self.partner_id.property_account_position.id
        elif self.partner_id.categ_id and self.partner_id.categ_id.fiscal_position_id:
            fiscal_position_id = self.partner_id.categ_id.fiscal_position_id.id
        else:
            fiscal_position_id = False

        vals = {
            'origin': self.name,
            'date_invoice': date_invoice,
            'user_id': self._uid,
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.property_account_receivable.id,
            'type': 'out_invoice',
            'company_id': self.env.user.company_id.id,
            'currency_id': self.currency_id.id,
            'contract_id':self.id,
            'pricelist_id':self.pricelist_id and self.pricelist_id.id or False,
            'payment_term':payment_term_id,
            'fiscal_position':fiscal_position_id,
            'renewal':renewal,
            #'partner_bank_id':partner_bank and partner_bank[0].id or False,
            #'journal_id':journal and journal[0].id or False,
        }
        invoice_obj = self.env['account.invoice']
        invoice = invoice_obj.create(vals)
        account_id = self.product_id.property_account_income.id
        if not account_id:
            account_id = self.product_id.categ_id.property_account_income_categ.id
        if not account_id:
            raise exceptions.ValidationError("Merci de définir un compte de revenues sur ce produit")
        #taxes
        account = self.product_id.property_account_income or self.product_id.categ_id.property_account_income_categ
        taxes = self.product_id.taxes_id or account.tax_ids
        fpos = self.env['account.fiscal.position'].browse(False)
        fp_taxes = fpos.map_tax(taxes)
        #taxes
        final_amount = self.apply_pricelist(self.pricelist_id.id, self.product_id.id, 1, self.amount, date_invoice)
        line_vals = {   'name': renewal and ("[REN]"+self.product_id.name) or self.product_id.name,
                        'account_id': account_id,
                        'product_id': self.product_id.id,
                        #'product_category_id':self.product_category_id.id,
                        'quantity': 1,
                        'price_unit': final_amount[0],
                        'uos_id': self.product_id.uom_id.id,
                        'account_analytic_id': False,
                        'invoice_id': invoice.id,
                        'invoice_line_tax_id':[(6, 0, fp_taxes.ids)],

                        }

        #Update account_id on line depending on fiscal position
        fpos = self.env['account.fiscal.position'].browse(fiscal_position_id)
        account = fpos.map_account(account)
        if account:
            account_id = account.id
            line_vals['account_id'] = account.id
        #Update account_id on line depending on fiscal position

        #Ligne budgétaire et compte analytique pour le calcul du budget
        fiscalyear_id = self.env['account.fiscalyear'].search([('date_start','<=',date_invoice),('date_stop','>=',date_invoice)])
        if fiscalyear_id:
            domain=[('product_id','=',self.product_id.id),('account_id','=',account_id),('fiscalyear_id','=',fiscalyear_id[0].id)]
            print "domain",domain,fiscal_position_id,account.code
            settings = self.env['budget.setting'].search(domain)

            if settings:
                line_vals['budget_item_id'] = settings[0].budget_line_id.id
                line_vals['account_analytic_id'] = settings[0].account_analytic_id.id
            else:
                raise exceptions.ValidationError("Veuillez configurer un paramètrage budget pour l'article "+self.product_id.name)
        #Ligne budgétaire et compte analytique pour le calcul du budget


        invoice_obj.invoice_line.create(line_vals)
        invoice.button_reset_taxes()
        workflow.trg_validate(self._uid, 'account.invoice', invoice.id, 'invoice_open', self._cr)

        invoice.invoice_print_auto()
        invoice.action_send_mail_auto()
        invoice._gen_xml_file(9)

        #invoice gen

    @api.one
    def action_validate_from_subscription(self,create_invoice=False):
        self.name = self.env['ir.sequence'].get('res.contract.seq')
        if create_invoice:
            self.action_create_invoice(self.first_invoice_date)
        self.state = 'pending'

    @api.multi
    def action_validate(self,create_invoice=False):
        wizard_id = self.pool.get("contract.validation.wizard").create(self._cr, self._uid, {'contract_id':self.id}, context=self._context)
        return {
            'name':_("Validation contrat"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'contract.validation.wizard',
            'res_id':wizard_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            }

    @api.one
    def set_closed(self):
        self.state = 'closed'

    @api.one
    def set_draft(self):
        self.state = 'draft'

    @api.onchange('date_start','date')
    def _how_many_months(self):
        if self.date_start and self.date:
            date_start = parser.parse(self.date_start).date()
            date_end = parser.parse(self.date).date()
            if date_end > date_start:
                r = relativedelta(date_end,date_start)
                print "diff ===",r.years*12 + r.months+1
                self.diff_months = (r.years*12 + r.months+1)-1


    @api.onchange('date_start')
    def _set_first_invoice_date(self):
        self.first_invoice_date = self.date_start


    @api.onchange('periodicity_id','date_start')
    def _set_end_date(self):
        if self.periodicity_id and self.date_start:
            self.date = (parser.parse(self.date_start) + relativedelta(months=self.periodicity_id.nb_months))- relativedelta(days=1)

    @api.onchange('template_id')
    def _onchange_template(self):
        if self.template_id:
            self.partner_id = False
            self.periodicity_id = self.template_id.periodicity_id
            self.currency_id = self.template_id.currency_id
            self.tacite = self.template_id.tacite
            self.product_category_id = self.template_id.product_category_id
            self.product_id = self.template_id.product_id
            self.amount = self.template_id.amount
            self.partner_categ_id = self.template_id.partner_categ_id

    @api.onchange('partner_categ_id')
    def _onchange_categ(self):
        self.partner_id = False
        domain_partner = [('categ_id','=',self.partner_categ_id and self.partner_categ_id.id or False)]
        domain_pricelist = [('id','=',self.partner_categ_id.pricelist_id and self.partner_categ_id.pricelist_id.id or False)]
        self.pricelist_id = self.partner_categ_id.pricelist_id or False
        return {'domain':{'partner_id':domain_partner,'pricelist_id':domain_pricelist}}

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id and self.partner_id.property_product_pricelist:
            domain_partner = [('categ_id','=',self.partner_categ_id and self.partner_categ_id.id or False)]
            domain_pricelist = [('id','=',self.partner_id.property_product_pricelist.id)]
            self.pricelist_id = self.partner_id.property_product_pricelist
            return {'domain':{'partner_id':domain_partner,'pricelist_id':domain_pricelist}}

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.amount = self.product_id.list_price


    @api.one
    @api.constrains('date_start','date')
    def _check_dates(self):
       if not self.is_template and (self.date_start > self.date):
            raise exceptions.ValidationError("La date de fin du contrat ne peut être antérieure à la date de début")

    @api.model
    def create(self, vals):
        if 'is_template' in self._context and self._context['is_template'] == True:
                vals['is_template'] = True
        return super(advanced_contract, self).create(vals)


advanced_contract()


