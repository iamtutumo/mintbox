# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import json
import base64

class GdprExportWizard(models.TransientModel):
    _name = 'gdpr.export.wizard'
    _description = 'GDPR Data Export Wizard'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=True)
    export_format = fields.Selection([
        ('json', 'JSON'),
        ('text', 'Text'),
    ], string='Export Format', default='json', required=True)
    export_file = fields.Binary(string='Export File', readonly=True)
    export_filename = fields.Char(string='Filename', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')
    
    def action_export(self):
        """Generate export file"""
        self.ensure_one()
        applicant = self.applicant_id
        
        # Collect all data
        data = {
            'personal_information': {
                'name': applicant.partner_name,
                'email': applicant.email_from,
                'phone': applicant.partner_phone,
                'mobile': applicant.partner_mobile,
            },
            'application': {
                'job': applicant.job_id.name if applicant.job_id else None,
                'department': applicant.department_id.name if applicant.department_id else None,
                'tracking_id': applicant.tracking_id,
                'application_date': str(applicant.create_date),
                'current_stage': applicant.stage_id.name if applicant.stage_id else None,
            },
            'education': [
                {
                    'degree': edu.degree,
                    'institution': edu.institution,
                    'field': edu.field_of_study,
                    'year': edu.year_completed,
                } for edu in applicant.education_ids
            ] if hasattr(applicant, 'education_ids') else [],
            'experience': [
                {
                    'position': exp.position,
                    'company': exp.company,
                    'start_date': str(exp.start_date),
                    'end_date': str(exp.end_date) if exp.end_date else 'Present',
                } for exp in applicant.experience_ids
            ] if hasattr(applicant, 'experience_ids') else [],
            'gdpr_information': {
                'consent_given': applicant.gdpr_consent,
                'consent_date': str(applicant.gdpr_consent_date) if applicant.gdpr_consent_date else None,
                'data_retention_until': str(applicant.data_retention_date) if applicant.data_retention_date else None,
            },
        }
        
        if self.export_format == 'json':
            content = json.dumps(data, indent=2)
            filename = f'applicant_data_{applicant.tracking_id}.json'
        else:
            content = self._format_as_text(data)
            filename = f'applicant_data_{applicant.tracking_id}.txt'
        
        self.write({
            'export_file': base64.b64encode(content.encode('utf-8')),
            'export_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _format_as_text(self, data):
        """Format data as readable text"""
        text = "APPLICANT DATA EXPORT\n"
        text += "=" * 50 + "\n\n"
        
        text += "PERSONAL INFORMATION:\n"
        for key, value in data['personal_information'].items():
            text += f"  {key.title()}: {value}\n"
        
        text += "\nAPPLICATION:\n"
        for key, value in data['application'].items():
            text += f"  {key.replace('_', ' ').title()}: {value}\n"
        
        if data['education']:
            text += "\nEDUCATION:\n"
            for edu in data['education']:
                text += f"  - {edu['degree']} from {edu['institution']} ({edu['year']})\n"
        
        if data['experience']:
            text += "\nEXPERIENCE:\n"
            for exp in data['experience']:
                text += f"  - {exp['position']} at {exp['company']} ({exp['start_date']} - {exp['end_date']})\n"
        
        text += "\nGDPR INFORMATION:\n"
        for key, value in data['gdpr_information'].items():
            text += f"  {key.replace('_', ' ').title()}: {value}\n"
        
        return text
