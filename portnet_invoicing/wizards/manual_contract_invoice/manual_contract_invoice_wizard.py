# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp import workflow

class manual_contract_invoice_wizard(models.TransientModel):
    _name = 'manual.contract.invoice.wizard'

    def _current_period(self):
        period_obj = self.env['account.period']
        current_period = period_obj.find()[0]
        return current_period

    date_facture = fields.Date('Date de facture')
    date_debut = fields.Date('Date début')
    date_fin = fields.Date('Date fin')
    period = fields.Many2one('account.period', 'Période de comptabilisation', domain=[('state','=','draft'),
                                                                                      ('special','=',False)],default=_current_period)

    @api.multi
    def action_create(self):
        invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']

        if len(self._context['active_ids'])>1:
            raise exceptions.ValidationError("Veuillez sélectionner un seul contrat.")

        invoice_lines = invoice_line_obj.search([('invoice_id.contract_id','in',self._context['active_ids']),
                                                 ('start_date','=',self.date_debut),
                                                 ('end_date','=',self.date_fin)])
        if invoice_lines:
            raise exceptions.ValidationError("Une facture existe déjà pour cet interval (Date début - Date fin).")

        contracts = self.env['res.contract'].browse(self._context['active_ids'])

        for contract in contracts:
            if contract.partner_id.property_payment_term:
                payment_term_id = contract.partner_id.property_payment_term.id
            elif contract.partner_id.categ_id and contract.partner_id.categ_id.payment_term_id:
                payment_term_id = contract.partner_id.categ_id.payment_term_id.id
            else:
                payment_term_id = False

            if contract.partner_id.property_account_position:
                fiscal_position_id = contract.partner_id.property_account_position.id
            elif contract.partner_id.categ_id and contract.partner_id.categ_id.fiscal_position_id:
                fiscal_position_id = contract.partner_id.categ_id.fiscal_position_id.id
            else:
                fiscal_position_id = False

            vals = {
                'origin': contract.name,
                'date_invoice': self.date_facture,
                'user_id': self._uid,
                'partner_id': contract.partner_id.id,
                'account_id': contract.partner_id.property_account_receivable.id,
                'type': 'out_invoice',
                'company_id': self.env.user.company_id.id,
                'currency_id': contract.currency_id.id,
                'contract_id': contract.id,
                'pricelist_id': contract.pricelist_id and contract.pricelist_id.id or False,
                'payment_term': payment_term_id,
                'fiscal_position': fiscal_position_id,
                'renewal': True,
                'period_id': self.period.id,
            }

            invoice = invoice_obj.create(vals)

            account_id = contract.product_id.property_account_income.id
            if not account_id:
                account_id = contract.product_id.categ_id.property_account_income_categ.id
            if not account_id:
                raise exceptions.ValidationError("Merci de définir un compte de revenues sur ce produit")
            # taxes
            account = contract.product_id.property_account_income or contract.product_id.categ_id.property_account_income_categ
            taxes = contract.product_id.taxes_id or account.tax_ids
            fpos = self.env['account.fiscal.position'].browse(False)
            fp_taxes = fpos.map_tax(taxes)
            # taxes
            final_amount = contract.apply_pricelist(contract.pricelist_id.id, contract.product_id.id, 1, contract.amount, self.date_facture)

            line_vals = {'name': "[REN]" + contract.product_id.name,
                         'account_id': account_id,
                         'product_id': contract.product_id.id,
                         'quantity': 1,
                         'price_unit': final_amount[0],
                         'uos_id': contract.product_id.uom_id.id,
                         'account_analytic_id': False,
                         'invoice_id': invoice.id,
                         'invoice_line_tax_id': [(6, 0, fp_taxes.ids)],
                         'start_date': self.date_debut,
                         'end_date': self.date_fin,
                         }

            # Update account_id on line depending on fiscal position
            fpos = self.env['account.fiscal.position'].browse(fiscal_position_id)
            account = fpos.map_account(account)
            if account:
                account_id = account.id
                line_vals['account_id'] = account.id
            # Update account_id on line depending on fiscal position

            #Ligne budgétaire et compte analytique pour le calcul du budget
            fiscalyear_id = self.env['account.fiscalyear'].search([('date_start','<=',self.date_facture),('date_stop','>=',self.date_facture)])
            if fiscalyear_id:
                domain=[('product_id','=',contract.product_id.id),('account_id','=',account_id),('fiscalyear_id','=',fiscalyear_id[0].id)]
                settings = self.env['budget.setting'].search(domain)

                if settings:
                    line_vals['budget_item_id'] = settings[0].budget_line_id.id
                    line_vals['account_analytic_id'] = settings[0].account_analytic_id.id
                else:
                    raise exceptions.ValidationError("Veuillez configurer un paramètrage budget pour l'article " + contract.product_id.name)
            #Ligne budgétaire et compte analytique pour le calcul du budget

            invoice_obj.invoice_line.create(line_vals)
            invoice.button_reset_taxes()
            workflow.trg_validate(self._uid, 'account.invoice', invoice.id, 'invoice_open', self._cr)
            invoice.invoice_print_auto()
            invoice.action_send_mail_auto()
            invoice._gen_xml_file(9)

        return True

