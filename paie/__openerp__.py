# -*- coding: utf-8 -*-
{   'name': "l10n_ma_hr_payroll",
    'version' : '1.4',
    'author' : 'Kazacube',
    'category' : 'Human Resources',
    'website': "http://www.kazacube.com",
    'version': '2.3',
    'description' : """
Generic Moroccan Payroll  Management.
====================================

Morocco payroll module that covers:
--------------------------------------------
    * Employee Details
    * Employee Contracts
    * Passport based Contract
    * Allowances/Deductions
    * Allow to configure Basic/Gross/Net Salary
    * Employee Payslip
    * Monthly Payroll Register
    * Integrated with Holiday Management

Permet d'imprimer les rapports:
--------------------------------------------------
    * Bulletin de paie
    * Livre de paie

Développée exclusivement par Kazacube, la paie sur Odoo a été entièrement revue pour répondre aux exigences réglementaires marocaines.
Le module paie, entièrement intégré, reçoit des données RH (primes, absences etc.) pour les intégrer automatiquement aux bulletins de paie
et prépare la comptabilité et la télédéclaration de l'IR, CNSS et AMO en mode brouillon.

    """,



    'depends': ['hr_expense', 'hr_payroll', 'hr_payroll_account','hr_contract', 'hr_timesheet','hr_holidays_usability'],

    # always loaded
    'data': [
        'security/hr_security.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'hr_event/events.xml',

        'views/employee.xml',
        'views/res_company.xml',
        'views/hr_payroll_view.xml',
        'views/user.xml',
        'views/poste.xml',
        'views/contract.xml',
        'wizard/enfant_wizard.xml',
        'wizard/declaration_issaf.xml',
        'wizard/declaration_sm.xml',
        'wizard/cot_modep.xml',
        'wizard/declaration_caad.xml',
        'wizard/ordre_de_virement.xml',
        'enfant/enfant_view.xml',
        'wizard/prime_wizard.xml',
        'wizard/livre_de_paie_wizard.xml',
        'wizard/etat_resume_wizard.xml',
        'wizard/account_period_wizard.xml',
        'views/report_livre_paie.xml',
        'views/paiereport.xml',
        'views/ordre_virement_wizard.xml',
        'views/etat_resume.xml',
        'views/hr_paie_data.xml',
        'mail/mail.xml',
        'avenant/avenant.xml',
        'views/salary_rule.xml',
        'views/salary_structure.xml',
        'views/payslip.xml',
        'views/payslip_lines.xml',
        'views/salary_rule_category.xml',
        'views/salary_structure.xml',
        'views/payslip.xml',
        'views/hr_employee_categorie.xml',
        'wizard/etat_ir.xml',
        'views/report_etat_ir.xml',
        'primes_indemnites/primes.xml',
        'wizard/payslip_run.xml',
        'views/rubriques.xml',
        'cron/cron.xml',

    ],

    # only loaded in demonstration mode
    'demo': [
       # 'demo.xml',
    ],
}
