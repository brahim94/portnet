# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, UserError, ValidationError


class MarketExecution(models.Model):
    _name = 'market.execution'
    _description = 'Market Execution'

    name = fields.Char(string='Name', copy=False, default=lambda self: _('New'), readonly=True)
    purchase_requisition = fields.Many2one('purchase.requisition', string="Purchase Requisition")
    purchase_order = fields.Many2one('purchase.order', string="Purchase Order")
    partner_id = fields.Many2one('res.partner', string="Attributaire")
    date = fields.Date(string="Order Date")
    engagement_ids = fields.One2many('market.engagement', 'market_id', string="Actions")
    engagement_number = fields.Char(string="Engagement Number", default=lambda self: _('New'), copy=False, readonly=True)
    enagagement_date = fields.Datetime(string="Engagement Date")
    # budget_id = fields.Many2one('account.analytic.line', string="Budget Line")
    final_deposit = fields.Float(string="Final Deposit")
    engagement_amount = fields.Float(string="Engagement Amount")
    notification_number = fields.Char(string="Notification Number", default=lambda self: _('New'), copy=False, readonly=True)
    caution_recue = fields.Boolean(string='Caution recue ?')
    caution_date = fields.Date(string='Date Caution ?')
    notification_date = fields.Datetime(string="Notification Date")
    documents_ids = fields.Many2many('market.document', 'rel_market_document', 'market_id', 'document_id', string="Documents Required")
    contract_attachment_id = fields.Binary(type="binary", string="Market Contract")
    contract_filename = fields.Char(string="Contract Filename")
    presentation_attachment_id = fields.Binary(type="binary", string="Rapport de présentation")
    presentation_filename = fields.Char(string="Presentation Filename")
    sheet_attachment_id = fields.Binary(type="binary", string="Signed engagement sheets")
    sheet_filename = fields.Char(string="Contract Filename")
    follow_up_assured = fields.Selection([('service_stock', 'Service Stock'), ('service_patrimoine', 'Service Patrimoine'), ('service_achat', 'Service Achat'), ('service_uilisateur', 'Service Uilisateur')], string="Follow-Up Assured")
    responsible = fields.Many2one('hr.employee', string="Responsible")
    order_service_number = fields.Char(String="Order Service Number", default=lambda self: _('New'), copy=False, readonly=True)
    execution_days = fields.Integer(string="Execution Days")
    order_date = fields.Date(string="Order Date")
    commencement_date = fields.Date(String="Commencement Date")
    service_ids = fields.One2many('market.service', 'market_id', string="Service")
    monitoring_execution_ids = fields.One2many('market.monitoring.execution', 'market_id', string="Monitoring Execution")
    reclamation_ids = fields.One2many('market.execution.reclamation', 'market_id', string="Réclamations")
    penalite_ids = fields.One2many('market.penalite', 'market_id', string="Panalites")
    
    # Mise en demeure
    motif = fields.Char(string='Motif')
    mise_reclamation_id = fields.Many2one('market.execution.reclamation', string='Réclamation')
    date_mise = fields.Date(string='Date de mise en demeure')
    days_mise = fields.Integer(string='Délai de mise en demeure')
    date_auto_effect = fields.Date(string='Date d’effet')
    attachment_mise_id = fields.Binary(type="binary", string="Lettre")
    filename_mise = fields.Char(string="Lettre Filename")
    
    # Résillation
    type_resillation = fields.Selection([('par_le_prestataire', 'Par le prestataire'), ('par_institution', 'Par Institution')], string='Type')
    motif_resillation = fields.Char(string='Motif')
    resillation_reclamation_id = fields.Many2one('market.execution.reclamation', string='Réclamation')
    is_caution_resillation = fields.Boolean(string='Confiscation de caution')
    date_decision_resillation = fields.Date(string='Date décision')
    days_decision_resillation = fields.Integer(string='Délai de préavis')
    date_effective_resillation = fields.Date(string="Date d'effect")
    attachment_resillation_id = fields.Binary(type="binary", string="Décision de résillation")
    filename_resillation = fields.Char(string='Résillation Filename')

    # paiement
    total_engage_amount = fields.Float(compute='_compute_total_paiement', string='Total engagé', store=True)
    total_transmis_amount = fields.Float(compute='_compute_total_paiement', string='Total transmis', store=True)
    total_facture_amount = fields.Float(compute='_compute_total_paiement', string='Total facturé', store=True)
    paiment_line_ids = fields.One2many('paiement.paiement', 'market_id', string='Paiement Line')

    # Closed
    date_reception_provision = fields.Date(string="Date reception provisone")
    days_reception_provision = fields.Integer(string='Délai (mois)')
    date_reception_definitive = fields.Date(string="Date reception definitive prévue")
    attachment_decompte_definit = fields.Binary(type="binary", string="Décompte definitif")
    filename_decompte_definit = fields.Char(string='Décompte definitif Filename')
    attachment_repport_achievement = fields.Binary(type="binary", string="Rapport d'achievement")
    filename_repport_achievement = fields.Char(string="Rapport d'achievement Filename")
    date_reception_definitive_reelle = fields.Date(string="Date reception definitive réelle")

    total_penalite = fields.Float(compute='_compute_penalite', string="Total Pénalité", store=True)
    taux_penalite = fields.Float(compute='_compute_penalite', string="Taux Pénalité (%)", store=True)
    state = fields.Selection([('pre_engagement', 'Pre Engagement'), ('engagement', 'Engagement'), ('paiement', 'Paiement'), ('done', 'Closed'), ('cancel', 'Cancel')], string="Status", default='pre_engagement')

    # BC Execution
    is_bc_execution = fields.Boolean(string='BC Execution')
    is_execution_convention = fields.Boolean(string='Execution Convention')
    is_regie_execution = fields.Boolean(string='Execution Régie')
    purchase_requisition_bc = fields.Many2one('purchase.requisition', string="N° Opération")
    contrat_convention_id = fields.Many2one('purchase.requisition', string="N° Opération")
    contrat_regie_id = fields.Many2one('purchase.requisition', string="N° Opération")
    # 
    consultation_name = fields.Char(related='purchase_requisition_bc.consultation_name')
    convention_name = fields.Char(related='contrat_convention_id.consultation_name')
    purchase_order_id_bc = fields.Many2one('purchase.order', string="Concurrents Séléctionné")
    date_notification_bc = fields.Datetime(related='purchase_order_id_bc.date_approve', readonly=False)
    
    purchase_order_id_convention = fields.Many2one('purchase.order', string="Concurrents Séléctionné")
    date_notification_convention = fields.Datetime(related='purchase_order_id_convention.date_approve', readonly=False)

    purchase_order_id_rigie = fields.Many2one('purchase.order', string="Concurrents Séléctionné")
    date_notification_rigie = fields.Datetime(related='purchase_order_id_rigie.date_approve', readonly=False)

    # budget_type = fields.Selection([('chb', 'CHB'), ('investment', 'Investissment'), ('functionment', 'Fonctionnement')], string='Type de budget')
    # programme_chb = fields.Many2one("purchase.financement", string="Programme")
    # programme_prestation = fields.Many2one("purchase.previsionnel", string="Prestation")
    # nature_bc = fields.Many2one('nature.bc', string='Nature')
    attachment_commande_signe = fields.Binary(type="binary", string="Bon de commande signé")
    filename_commande_signe = fields.Char(string="Bon de commande signé Filename")
    attachment_engagement_signe = fields.Binary(type="binary", string="Fiche d'engagement signée")
    filename_engagement_signe = fields.Char(string="Fiche d'engagement signée Filename")
    attachment_commission = fields.Binary(type="binary", string="PV de la commission")
    filename_commission = fields.Char(string="PV de la commission Filename")

    term = fields.Integer('Terme')
    date_debut = fields.Date(string="Début terme")   
    date_fin = fields.Date('Fin terme')

    
    @api.constrains('contrat_convention_id', 'term', 'is_execution_convention')
    def _check_dup_market_execution(self):
        if self.is_execution_convention:
            executions_to_check = self.search([('contrat_convention_id', '=', self.contrat_convention_id.id), ('term', '=', self.term), ('id', '!=', self.id), ('is_execution_convention', '=', True)])
            if executions_to_check:
                raise ValidationError(_('You already have execution with same contract convention and term, you can not create one more.'))
       
    @api.depends('engagement_amount', 'paiment_line_ids')
    def _compute_total_paiement(self):
        for record in self:
            record.total_engage_amount = record.engagement_amount
            record.total_transmis_amount = sum(record.paiment_line_ids.filtered(lambda a: a.state == 'comptabilisee').mapped('montant'))
            record.total_facture_amount = sum(record.paiment_line_ids.filtered(lambda a: a.state == 'en_course').mapped('montant'))

    @api.constrains('total_engage_amount', 'total_transmis_amount', 'total_facture_amount' )
    def _check_my_balance(self):
            balance = self.total_transmis_amount + self.total_facture_amount
            if  balance > self.total_engage_amount:
                    raise ValidationError('le montant Total transmis additionné au montant Total facturé ne doit pas dépassé le montant Total engagé')

    @api.onchange('paiment_line_ids')
    def onchange_paiment_line_ids(self):
        if self.paiment_line_ids:
            self.date_reception_provision = max(dt for dt in self.paiment_line_ids.mapped('date_reception')) 

    @api.onchange('date_mise', 'days_mise')
    def onchange_mise_date(self):
        if self.date_mise:
            actual_days = self.env['resource.calendar']._check_holiday_status(self.days_mise, self.date_mise)
            self.days_mise = actual_days
            self.date_decision_resillation = self.date_mise + timedelta(days=self.days_mise)
            self.date_auto_effect = self.date_mise + timedelta(days=self.days_mise)

    @api.onchange('date_decision_resillation', 'days_decision_resillation')
    def onchange_decision_date_resillation(self):
        if self.date_decision_resillation:
            actual_days = self.env['resource.calendar']._check_holiday_status(self.days_decision_resillation, self.date_decision_resillation)
            self.days_decision_resillation = actual_days
            self.date_effective_resillation = self.date_decision_resillation + timedelta(days=self.days_decision_resillation)

    def action_update_term_dates(self):
        if self.contrat_convention_id:
            active_term = self.contrat_convention_id.requisition_terms_ids.filtered(lambda l: l.etat == 'active')
            if active_term and self.enagagement_date:
               date_debut = self.enagagement_date
               unit = self.contrat_convention_id.unit
               nbr = self.contrat_convention_id.nbr
               if unit == 'week':
                date_fin = self.enagagement_date + relativedelta(weeks=+nbr)
               if unit == 'day':
                date_fin = self.enagagement_date + relativedelta(days=+nbr)
               if unit == 'month':
                date_fin = self.enagagement_date + relativedelta(months=+nbr)
               if unit == 'year':
                date_fin = self.enagagement_date + relativedelta(years=+nbr)
               active_term.write({
                'date_debut': date_debut,
                'date_fin': date_fin,
               }) 
               self.write({
                'date_debut': date_debut,
                'date_fin': date_fin,
                'term': active_term.term,
                })
    def action_engager(self):
        if self.contrat_convention_id and self.is_execution_convention:
            self.action_update_term_dates()
        lines = []
        for planification in self.purchase_requisition.planification_ids:
            lines.append((0, 0, {
                    'jalon_id': planification.jalon_id.id,
                    'scheduled_start_date': planification.start_date,
                    'scheduled_end_date': planification.end_date,
                    }))
        self.write({'state': 'engagement', 'monitoring_execution_ids': lines})
        for line in self.monitoring_execution_ids:
            line.onchange_estimated_time()

    @api.onchange('date_reception_provision', 'days_reception_provision')
    def onchange_date_reception_provision(self):
        if self.date_reception_provision:
            date = self.date_reception_provision + relativedelta(months=self.days_reception_provision)
            actual_days = self.env['resource.calendar']._check_holiday_status(0, date)
            self.date_reception_definitive = date + timedelta(days=actual_days)

    @api.onchange('date_reception_definitive')
    def onchange_date_reception_definitive(self):
        if self.date_reception_definitive:
            self.date_reception_definitive_reelle = self.date_reception_definitive

    def generate_miss_model(self):
        return True

    def generate_resillation_model(self):
        return True

    def action_payer(self):
        return self.write({'state': 'paiement'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        return self.write({'state': 'done'})

    # def print_engagement(self):
    #     if self.engagement_number == _('New') or self.engagement_number == 'New':
    #         self.write({'engagement_number': self.env['ir.sequence'].next_by_code('market.engagement')})
    #     return True
    #     return self.env.ref('tech_reports_extention.action_report_engagement').report_action(self)


    def print_notification(self):
        if self.notification_number == _('New') or self.notification_number == 'New':
            self.write({'notification_number': self.env['ir.sequence'].next_by_code('market.notification')})
        return True

    def print_commencement_order(self):
        if self.order_service_number == _('New') or self.order_service_number == 'New':
            self.write({'order_service_number': self.env['ir.sequence'].next_by_code('market.order.service')})
        return True

    def print_decompte_definitif(self):
        return True

    def print_rapport_achievement(self):
        return True

    def action_view_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq").read()[0]
        action["domain"] = [("id", "in", self.purchase_order.ids)]
        action["res_id"] = self.purchase_order.id
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals.get('is_bc_execution') == True:
                vals['name'] = self.env['ir.sequence'].next_by_code('bc.execution')
            elif vals.get('is_execution_convention') == True:
                vals['name'] = self.env['ir.sequence'].next_by_code('execution.convention')
            elif vals.get('is_regie_execution') == True:
                vals['name'] = self.env['ir.sequence'].next_by_code('regie.execution')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('market.execution')
        return super(MarketExecution, self).create(vals)

    @api.onchange('execution_days', 'order_date')
    def onchange_order_date_service(self):
        if self.order_date:
            actual_days = self.env['resource.calendar']._check_holiday_status(self.execution_days, self.order_date)
            self.execution_days = actual_days
            self.commencement_date = self.order_date + timedelta(days=self.execution_days)

    @api.depends('penalite_ids', 'engagement_amount')
    def _compute_penalite(self):
        for record in self:
            record.total_penalite = sum(record.penalite_ids.mapped('amount'))
            if record.total_penalite > 0.00 and record.engagement_amount > 0.00:
                record.taux_penalite = (record.total_penalite / record.engagement_amount) * 100

    @api.onchange('engagement_amount')
    def onchange_engagement_amount(self):
        if self.engagement_amount:
            self.final_deposit = ((self.engagement_amount * 3.0) / 100)

    @api.onchange('purchase_order')
    def onchange_purchase_order(self):
        if self.purchase_order:
            self.date = self.purchase_order.tender_decision_line_id.date
            self.partner_id = self.purchase_order.tender_decision_line_id.bidder_id.id
            self.engagement_amount = self.purchase_order.amount_total
            return {'domain': {'partner_id': [('id', 'in', self.purchase_order.tender_decision_line_id.bidder_id.ids)]}}
        else:
            self.partner_id = False
            self.date = False
            return {'domain': {'partner_id': [('id', 'in', [])]}}

    @api.onchange('purchase_order_id_bc', 'purchase_order_id_convention', 'purchase_order_id_rigie')
    def onchange_purchase_order_id_bc(self):
        if self.purchase_order_id_bc:
            self.engagement_amount = self.purchase_order_id_bc.amount_total
        if self.purchase_order_id_convention:
            self.engagement_amount = self.purchase_order_id_convention.amount_total
        if self.purchase_order_id_rigie:
            self.engagement_amount = self.purchase_order_id_rigie.amount_total

    @api.onchange('contrat_regie_id')
    def onchange_contrat_regie_id(self):
        if self.contrat_regie_id:
            order = self.env['purchase.order'].search([('requisition_id', '!=', False), ('requisition_id', '=', self.contrat_regie_id.id)], limit=1)
            self.purchase_order_id_rigie = order.id

class NatureBC(models.Model):
    _name = 'nature.bc'
    _description = 'Nature BC'

    name = fields.Char(string='Name', required=True)


class PaiementPaiement(models.Model):
    _name = 'paiement.paiement'
    _description = 'Paiement'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    name = fields.Char(string='N° Facture', required=True)
    date_invoice = fields.Date(string='Date de facture')
    montant = fields.Float(string='Montant')
    date_paiement = fields.Date(string='Date de paiement prévu')
    state = fields.Selection([('comptabilisee', 'Comptabilisée'), ('en_course', 'En cours'), ('annulee', 'Annulée')], string='Etat', default='comptabilisee')
    date_reception = fields.Date(string='Date reception', default=fields.Date.context_today)
    reception_attachment_id = fields.Binary(type="binary", string='Bon de reception / exécution')
    reception_filename = fields.Char(string='Reception Filename')
    bc_exec_check = fields.Boolean(string='BCEx', related='market_id.is_bc_execution')
    cv_exec_check = fields.Boolean(string='CVEx', related='market_id.is_execution_convention')
    rj_exec_check = fields.Boolean(string='REEx', related='market_id.is_regie_execution')

    def generate_decompte_paiement(self):
        return True


class MarketEngagement(models.Model):
    _name = 'market.engagement'
    _description = 'Market Engagement'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    object_id = fields.Many2one('market.object', string="Object", required=True)
    action_id = fields.Many2one('market.action', string="Action", required=True)
    days = fields.Integer(string="Days")
    date = fields.Date(string="Date")
    quality_id = fields.Many2one('market.quality', string="Quality")
    engagement_type = fields.Selection([('Partner', 'Partner'), ('Employee', 'Employee')], string="Type")
    hr_responsible = fields.Many2one('hr.employee', string="HR Responsible")
    partner_responsible = fields.Many2one('res.partner', string="Partner Responsible")
    department_id = fields.Many2one('hr.department',related='hr_responsible.department_id', string="Service")

    @api.onchange('days')
    def onchange_days(self):
        if self.days:
            date = self._context.get('default_date')
            if date:
                actual_days = self.env['resource.calendar']._check_holiday_status(self.days, date)
                self.days = actual_days
                self.date = fields.Date.from_string(date) + timedelta(days=self.days)

    @api.onchange('date')
    def onchange_date(self):
        if self.date and self.market_id.date:
            if not fields.Date.to_string(self.date) >= fields.Date.to_string(self.market_id.date + timedelta(days=self.days)):
                raise UserError(_("Date should be grater than or equal to order date+ days."))


class MarketService(models.Model):
    _name = 'market.service'
    _description = 'Market Service'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    service_type = fields.Selection([('Arret', 'Arret'), ('Reprise', 'Reprise')], string="Type", required=True)
    order_number = fields.Char(String="Order Number", default=lambda self: _('New'), copy=False, readonly=True)
    order_date = fields.Date(string="Order Date", default=fields.Date.context_today)
    days = fields.Integer(string="Days")
    effect_date = fields.Date(string="Effect Date")
    description = fields.Text(string="Description")

    @api.onchange('order_date', 'days')
    def onchange_order_date(self):
        if self.order_date:
            actual_days = self.env['resource.calendar']._check_holiday_status(self.days, self.order_date)
            self.days = actual_days
            self.effect_date = self.order_date + timedelta(days=self.days)

    @api.model
    def create(self, vals):
        if vals.get('order_number', _('New')) == _('New'):
            vals['order_number'] = self.env['ir.sequence'].next_by_code('market.service')
        return super(MarketService, self).create(vals)

    @api.model
    def default_get(self, default_fields):
        service_type = False
        if 'service_ids' in self._context:
            if self._context.get('service_ids'):
                counter_arret = counter_reprise = 0
                last_type = False
                for service_line in self._context.get('service_ids'):
                    if service_line[2].get('service_type') == 'Arret':
                        counter_arret += 1
                    if service_line[2].get('service_type') == 'Reprise':
                        counter_reprise += 1
                    last_type = service_line[2].get('service_type')
                if counter_arret > counter_reprise:
                    service_type = 'Reprise'
                elif counter_arret == counter_reprise:
                    service_type = 'Arret' if last_type == 'Reprise' else 'Reprise'
                else:
                    service_type = 'Arret'
        result = super(MarketService, self).default_get(default_fields)
        if service_type:
            result.update({'service_type': service_type})
        return result


class MarketMonitoringExecution(models.Model):
    _name = 'market.monitoring.execution'
    _description = 'Market Monitoring Execution'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    jalon_id = fields.Many2one('purchase.requisition.jalon', string="Jalons", required=True)
    scheduled_start_date = fields.Date(string="Scheduled Start Date")
    scheduled_end_date = fields.Date(string="Scheduled End Date")
    estimated_time = fields.Integer(string="Estimated Duration")
    actual_start_date = fields.Date(string="Actual Start Date")
    actual_end_date = fields.Date(string="Actual End Date")
    actual_time = fields.Integer(string="Actual Duration")
    ecart = fields.Float(string="Ecart (%)")
    state = fields.Selection([('en_course', 'En cours'), ('termine', 'Terminé'), ('en_arret', 'En arreét')], string="State")
    
    @api.onchange('scheduled_start_date', 'scheduled_end_date')
    def onchange_estimated_time(self):
        for record in self:
            if record.scheduled_start_date and record.scheduled_end_date:
                record.estimated_time = (record.scheduled_end_date - record.scheduled_start_date).days

    @api.onchange('actual_start_date', 'actual_end_date')
    def onchange_actual_time(self):
        for record in self:
            if record.actual_start_date and record.actual_end_date:
                record.actual_time = (record.actual_end_date - record.actual_start_date).days

    @api.onchange('estimated_time', 'actual_time')
    def onchange_estimate_and_actual_time(self):
        for record in self:
            if record.estimated_time and record.actual_time:
                record.ecart = ((record.actual_time - record.estimated_time) / record.estimated_time) * 100
            else:
                record.ecart = 0.00


class MarketExecutionReclamation(models.Model):
    _name = 'market.execution.reclamation'
    _description = 'Market Execution Reclamation'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    date = fields.Date(string='Date', default=fields.Date.context_today)
    type_reclamation = fields.Selection([('service_utisaleur', 'Service Utisaleur'), ('partenaire', 'Partenaire')], string='Type', default='service_utisaleur')
    name = fields.Char(string='Référence', default=lambda self: _('New'), copy=False, readonly=True)
    object_reclamation = fields.Char(string='Object')
    description = fields.Char(string='Description')
    department_id = fields.Many2one('hr.department', string='Service Utisaleur')
    partner_id = fields.Many2one('res.partner', string='Partenaire')
    attachment_id = fields.Binary(type="binary", string="Attachment")
    filename = fields.Char(String="Filename")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('market.execution.reclamation')
        return super(MarketExecutionReclamation, self).create(vals)


class MarketPanalite(models.Model):
    _name = 'market.penalite'
    _description = 'Market Penalite'

    market_id = fields.Many2one('market.execution', string="Market Execution")
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    penalite_type = fields.Many2one('penalite.type', string="Type", required=True)
    description = fields.Text(string="Description")
    reclamation_id = fields.Many2one('market.execution.reclamation', string='Réclamation', ondelete='cascade')
    amount = fields.Float(String="Amount")
    pv_attachment_id = fields.Binary(type="binary", string="PV")
    pv_filename = fields.Char(String="PV Filename")


class MarketObject(models.Model):
    _name = 'market.object'
    _description = 'Market Object'

    name = fields.Char(String="Name", required=True)


class MarketAction(models.Model):
    _name = 'market.action'
    _description = 'Market Action'

    name = fields.Char(string="Name", required=True)


class MarketQuality(models.Model):
    _name = 'market.quality'
    _description = 'Market Quality'

    name = fields.Char(string="Name", required=True)


class MarketDocument(models.Model):
    _name = 'market.document'
    _description = 'Market Document'

    name = fields.Char(string="Name", required=True)


class PenaliteType(models.Model):
    _name = 'penalite.type'
    _description = 'Penalite Type'

    name = fields.Char(string="Name", required=True)
