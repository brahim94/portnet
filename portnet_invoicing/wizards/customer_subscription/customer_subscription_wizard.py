# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser

class customer_subscription_wizard(models.TransientModel):
    _name = 'customer.subscription.wizard'

    def _default_nb_customers(self):
        if 'active_ids' in self._context:
            return len(self._context.get('active_ids'))
        else:
            return 0

    def _default_etl(self):
        if 'action_etl' in self._context and self._context['action_etl'] == True:
            return True
        else:
            return False

    def _default_date(self):
        if len(self._context.get('active_ids')) == 1:
            customer = self.env['res.partner'].browse(self._context.get('active_ids')[0])
            if customer and customer.customer_request_id:
                return customer.customer_request_id.create_date
            else:
                return datetime.now().date()
        else:
            return datetime.now().date()

    partner_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False, )
    contract_tmpl_id = fields.Many2one(comodel_name="res.contract", string="Modèle de contrat", required=False, )
    date = fields.Date(string="Date début du contrat", default=_default_date)
    nb_customers = fields.Integer(string="Nombre de clients", required=False, default=_default_nb_customers)
    etl = fields.Boolean(string="Reprise ?", default=_default_etl)


    @api.multi
    def action_subscribe(self):
        #Recherche date réelle de la demande de création client
        #self.env['customer.request'].search([('code','=',self.partner_id.code),('ifu','=',''),('','','')])

        #Création du contrat à partir du modèle
        i = 0
        for id in self._context['active_ids']:
            self.partner_id = self.env['res.partner'].browse(id)
            if not self.partner_id.subscribed:
                i+=1
                print i
                #Check si date de facture > date de création de la demande
                date_check = self.partner_id.customer_request_id and parser.parse(self.partner_id.customer_request_id.create_date).date() or False
                if not self.partner_id.etl and date_check and self.date and self.date < str(date_check):
                    raise exceptions.ValidationError("La date du début du contrat ne peut être supérieure à la date de création du client : "+str(self.partner_id.display_name))
                # vérifier si le modèle de contrat pour cette catégorie de client est défini
                contract_templates = self.env['res.contract'].search([('is_template','=',True),('partner_categ_id','=',self.partner_id.categ_id.id)])
                if not contract_templates:
                    raise exceptions.ValidationError("Aucun modèle de contrat défini pour la catégorie ("+str(self.partner_id.categ_id.name)+") de ce client : "+str(self.partner_id.display_name))
                self.contract_tmpl_id = self.env['res.contract'].browse(contract_templates[0].id)
                #pricelist
                if self.partner_id.property_product_pricelist:
                    pricelist_id = self.partner_id.property_product_pricelist.id
                elif self.partner_id.categ_id.pricelist_id:
                     pricelist_id = self.partner_id.categ_id.pricelist_id.id
                else:
                    pricelist_id = False

                vals={
                    'template_id':self.contract_tmpl_id.id,
                    'partner_categ_id':self.contract_tmpl_id.partner_categ_id.id,
                    'partner_id':self.partner_id.id,
                    'product_category_id':self.contract_tmpl_id.product_category_id.id,
                    'product_id':self.contract_tmpl_id.product_id.id,
                    'pricelist_id':pricelist_id,
                    'currency_id':self.contract_tmpl_id.currency_id.id,
                    'amount':self.contract_tmpl_id.amount,
                    'tacite':self.contract_tmpl_id.tacite,
                    'periodicity_id':self.contract_tmpl_id.periodicity_id.id,
                    'date_start':parser.parse(self.date),
                    'date':(parser.parse(self.date) + relativedelta(months=self.contract_tmpl_id.periodicity_id.nb_months))-relativedelta(days=1),
                    'first_invoice_date':parser.parse(self.date)
                }

                # Date de début contrat/facture
                if self.partner_id.etl:
                    if self.partner_id.first_invoice_date:
                        vals['first_invoice_date'] = parser.parse(self.partner_id.first_invoice_date)
                        vals['date_start'] = vals['first_invoice_date']
                        vals['date'] = (parser.parse(self.partner_id.first_invoice_date) + relativedelta(months=self.contract_tmpl_id.periodicity_id.nb_months))-relativedelta(days=1)
                        today = datetime.now().date()
                        years_diff = today.year - parser.parse(self.partner_id.first_invoice_date).year
                        #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa modifier
                        if years_diff > 0:
                            if parser.parse(self.partner_id.first_invoice_date).replace(year=today.year).date() < today:
                                vals['next_invoice_date'] = parser.parse(self.partner_id.first_invoice_date).replace(year=today.year) + relativedelta(months=self.contract_tmpl_id.periodicity_id.nb_months)
                            else:
                                vals['next_invoice_date'] = parser.parse(self.partner_id.first_invoice_date).replace(year=today.year)
                        else:
                            vals['next_invoice_date'] = parser.parse(self.partner_id.first_invoice_date) + relativedelta(months=self.contract_tmpl_id.periodicity_id.nb_months)
                    else:
                        raise exceptions.ValidationError("Date de première facture manquante pour ce client : "+str(self.partner_id.display_name))
                else:
                    vals['first_invoice_date'] = datetime.now().date()
                    vals['next_invoice_date'] = parser.parse(self.date) + relativedelta(months=self.contract_tmpl_id.periodicity_id.nb_months)
                    #Anticipation de la prochaine facturation
                    if self.partner_id.categ_id.invoicing_advance_in_months > 0:
                        print vals['next_invoice_date']
                        vals['anticipated_invoice_date'] = vals['next_invoice_date'].date() - relativedelta(months=self.partner_id.categ_id.invoicing_advance_in_months)
                    else:
                        vals['anticipated_invoice_date'] = vals['next_invoice_date'].date()

                # Cas des clients autres que les importateurs et les transitaires (facturation toujours en début d'année):
                if self.partner_id.categ_id.annual_invoicing:
                    first_day_of_next_year = date(datetime.now().date().year, 12, 31) + relativedelta(days=1)
                    if first_day_of_next_year != datetime.now().date():
                        vals['next_invoice_date'] =  first_day_of_next_year
                    else:
                        vals['next_invoice_date'] = first_day_of_next_year+relativedelta(years=1)
                    #Anticipation de la prochaine facturation
                    if self.partner_id.categ_id.invoicing_advance_in_months > 0:
                        vals['anticipated_invoice_date'] = vals['next_invoice_date'] - relativedelta(months=self.partner_id.categ_id.invoicing_advance_in_months)
                    else:
                        vals['anticipated_invoice_date'] = vals['next_invoice_date']


                new_contract= self.env['res.contract'].create(vals)
                if self.partner_id.etl:
                    new_contract.action_validate_from_subscription()
                else:
                    new_contract.action_validate_from_subscription(create_invoice=True)
                    self.partner_id.first_invoice_date = vals['first_invoice_date']
                self.partner_id.set_confirmed()
                self.partner_id.subscribed = True


customer_subscription_wizard()