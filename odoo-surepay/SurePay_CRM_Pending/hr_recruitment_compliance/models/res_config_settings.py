# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # GDPR Data Retention Settings
    default_retention_period_days = fields.Integer(
        string='Default Data Retention Period (Days)',
        default=730,
        config_parameter='hr_recruitment_compliance.default_retention_period_days',
        help='Default number of days to retain applicant data (GDPR compliance). Default is 730 days (2 years).'
    )
    
    # GDPR Auto-Consent Settings
    auto_consent_web_form = fields.Boolean(
        string='Auto-Consent for Web Forms',
        default=True,
        config_parameter='hr_recruitment_compliance.auto_consent_web_form',
        help='Automatically grant GDPR consent for applicants submitting via web forms.'
    )
    
    # GDPR Auto-Anonymization Settings
    enable_auto_anonymization = fields.Boolean(
        string='Enable Automatic Anonymization',
        default=False,
        config_parameter='hr_recruitment_compliance.enable_auto_anonymization',
        help='Automatically anonymize applicant data after retention period expires.'
    )
    
    # Audit Log Settings
    enable_audit_logging = fields.Boolean(
        string='Enable Audit Logging',
        default=True,
        config_parameter='hr_recruitment_compliance.enable_audit_logging',
        help='Track all actions performed on applicant records for GDPR compliance.'
    )
    
    log_ip_addresses = fields.Boolean(
        string='Log IP Addresses',
        default=True,
        config_parameter='hr_recruitment_compliance.log_ip_addresses',
        help='Record IP addresses in audit logs.'
    )
    
    # GDPR Export Settings
    export_format = fields.Selection([
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('pdf', 'PDF'),
    ], string='Default Export Format',
        default='json',
        config_parameter='hr_recruitment_compliance.export_format',
        help='Default format for GDPR data export requests.'
    )
    
    # Notification Settings
    notify_before_anonymization = fields.Boolean(
        string='Notify Before Anonymization',
        default=True,
        config_parameter='hr_recruitment_compliance.notify_before_anonymization',
        help='Send notification to recruitment managers before auto-anonymization.'
    )
    
    anonymization_notice_days = fields.Integer(
        string='Notice Period (Days)',
        default=30,
        config_parameter='hr_recruitment_compliance.anonymization_notice_days',
        help='Number of days before anonymization to send notification.'
    )
