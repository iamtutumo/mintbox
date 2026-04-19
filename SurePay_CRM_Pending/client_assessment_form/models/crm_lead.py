import base64
import os
from datetime import datetime
from io import BytesIO

from docxtpl import DocxTemplate
from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from docx import Document
    from docx.shared import Inches
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _get_template_path(self):
        """Get the path to the template file."""
        module_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(module_path, 'client_assessment_form', 'static', 'src', 'template', 'CLIENT ASSESSMENT FORM.docx')

    def _prepare_template_context(self):
        """Prepare the context for the template with all available CRM fields."""
        self.ensure_one()
        
        # Get the current date in a readable format
        current_date = fields.Date.context_today(self)
        
        # Safely get field values with defaults
        def safe_get(record, field, default=''):
            try:
                value = getattr(record, field, default)
                if field.endswith('_ids') and hasattr(value, 'mapped'):
                    return ', '.join(value.mapped('name'))
                elif hasattr(value, 'name') and hasattr(value, 'id'):
                    return value.name
                return value or default
            except Exception:
                return default
        
        def safe_get_currency(record, field, default='0.00'):
            """Safely get monetary fields with currency."""
            try:
                value = getattr(record, field, 0)
                if value:
                    currency = safe_get(record, 'company_currency.symbol', '$')
                    return f"{currency} {value:,.2f}"
                return default
            except Exception:
                return default
        
        def safe_get_date(record, field, default=''):
            """Safely get date fields in readable format."""
            try:
                value = getattr(record, field, None)
                if value:
                    return value.strftime('%B %d, %Y')
                return default
            except Exception:
                return default
        
        def safe_get_datetime(record, field, default=''):
            """Safely get datetime fields in readable format."""
            try:
                value = getattr(record, field, None)
                if value:
                    return value.strftime('%B %d, %Y at %I:%M %p')
                return default
            except Exception:
                return default
        
        # Prepare the comprehensive context dictionary
        context = {
            # Document metadata
            'date': current_date.strftime('%B %d, %Y'),
            'datetime': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            'lead_name': safe_get(self, 'name'),
            'lead_id': self.id,
            
            # Basic CRM fields
            'client_name': self.partner_id.name if hasattr(self, 'partner_id') and self.partner_id else safe_get(self, 'contact_name'),
            'email': safe_get(self, 'email_from'),
            'phone': safe_get(self, 'phone'),
            'mobile': safe_get(self, 'mobile'),
            'street': safe_get(self, 'street'),
            'street2': safe_get(self, 'street2'),
            'city': safe_get(self, 'city'),
            'state': safe_get(self, 'state_id.name'),
            'zip': safe_get(self, 'zip'),
            'country': safe_get(self, 'country_id.name'),
            'website': safe_get(self, 'website'),
            'company_name': safe_get(self, 'company_id.name'),
            
            # Lead information
            'lead_type': safe_get(self, 'type'),
            'priority': safe_get(self, 'priority'),
            'stage_name': safe_get(self, 'stage_id.name'),
            'source_name': safe_get(self, 'source_id.name'),
            'medium_name': safe_get(self, 'medium_id.name'),
            'campaign_name': safe_get(self, 'campaign_id.name'),
            'tag_names': safe_get(self, 'tag_ids'),
            'description': safe_get(self, 'description'),
            
            # Dates
            'create_date': safe_get_datetime(self, 'create_date'),
            'write_date': safe_get_datetime(self, 'write_date'),
            'date_deadline': safe_get_date(self, 'date_deadline'),
            'date_conversion': safe_get_date(self, 'date_conversion'),
            'date_closed': safe_get_date(self, 'date_closed'),
            
            # Monetary fields
            'planned_revenue': safe_get_currency(self, 'planned_revenue'),
            'expected_revenue': safe_get_currency(self, 'expected_revenue'),
            'probability': f"{safe_get(self, 'probability', 0)}%",
            
            # User assignments
            'user_name': safe_get(self, 'user_id.name'),
            'user_email': safe_get(self, 'user_id.email'),
            'user_phone': safe_get(self, 'user_id.phone'),
            'team_name': safe_get(self, 'team_id.name'),
            
            # Custom fields from crm_client_assessment module
            'organization_name': safe_get(self, 'organization_name'),
            'years_in_business': safe_get(self, 'years_in_business', '0'),
            'sector_industry': safe_get(self, 'sector_industry'),
            'services_requested': safe_get(self, 'services_requested'),
            'current_transactions': safe_get(self, 'current_transactions'),
            'projected_transactions': safe_get(self, 'projected_transactions'),
            'expected_monthly_turnover': safe_get_currency(self, 'expected_monthly_turnover'),
            'target_customers': safe_get(self, 'target_customers'),
            'customer_distribution': safe_get(self, 'customer_distribution'),
            'onboarding_responsible': safe_get(self, 'onboarding_responsible_id.name'),
            'marketing_budget': safe_get_currency(self, 'marketing_budget'),
            'declaration_date': safe_get_date(self, 'declaration_date'),
            'declaration_signed_by': safe_get(self, 'declaration_signed_by'),
            
            # Custom fields from surepay_crm_extension module
            'school_code': safe_get(self, 'school_code'),
            'is_cold_lead': 'Yes' if safe_get(self, 'is_cold_lead', False) else 'No',
            
            # Client visit information from surepay_client_visits module
            'visit_count': safe_get(self, 'visit_count', '0'),
            'last_visit_date': '',  # Will be populated below
            'last_visit_location': '',  # Will be populated below
            'last_visit_purpose': '',  # Will be populated below
            'last_visit_notes': '',  # Will be populated below
        }
        
        # Get visit information if available
        if hasattr(self, 'visit_ids') and self.visit_ids:
            last_visit = self.visit_ids.sorted('visit_date', reverse=True)[:1]
            if last_visit:
                visit = last_visit[0]
                context.update({
                    'last_visit_date': safe_get_date(visit, 'visit_date'),
                    'last_visit_location': f"{safe_get(visit, 'latitude')}, {safe_get(visit, 'longitude')}",
                    'last_visit_purpose': safe_get(visit, 'purpose'),
                    'last_visit_notes': safe_get(visit, 'notes'),
                })
        
        return context

    def generate_client_assessment_form(self):
        """Generate the client assessment form and return it as a download action."""
        return self._generate_assessment_form('docx')
    
    def generate_client_assessment_form_pdf(self):
        """Generate the client assessment form in PDF format and return it as a download action."""
        if not PDF_AVAILABLE:
            raise UserError(_("PDF generation is not available. Please install the required dependencies: python-docx and reportlab."))
        return self._generate_assessment_form('pdf')
    
    def _generate_assessment_form(self, format_type='docx'):
        """Generate the client assessment form in the specified format."""
        self.ensure_one()
        
        if format_type == 'docx':
            return self._generate_docx_form()
        elif format_type == 'pdf':
            return self._generate_assessment_form_pdf()
        else:
            raise UserError(_("Unsupported format: %s") % format_type)
    
    def _generate_docx_form(self):
        """Generate the client assessment form in DOCX format."""
        # Check if template exists
        template_path = self._get_template_path()
        if not os.path.exists(template_path):
            raise UserError(_("Template file not found. Please contact your system administrator."))
        
        try:
            # Load the template
            doc = DocxTemplate(template_path)
            
            # Render the template with the context
            context = self._prepare_template_context()
            doc.render(context)
            
            # Save the document to a BytesIO object
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            
            # Create the attachment
            file_name = f"Client_Assessment_{self.name.replace(' ', '_')}_{fields.Date.context_today(self)}.docx"
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': base64.b64encode(output.getvalue()),
                'res_model': 'crm.lead',
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            })
            
            # Return the download action
            return {
                'type': 'ir.actions.act_url',
                'url': f"/web/content/{attachment.id}?download=true",
                'target': 'self',
            }
            
        except Exception as e:
            raise UserError(_(f"Error generating DOCX document: {str(e)}"))
    
    def _get_docx_content(self):
        """Generate DOCX content and return as bytes without creating attachment."""
        # Check if template exists
        template_path = self._get_template_path()
        if not os.path.exists(template_path):
            raise UserError(_("Template file not found. Please contact your system administrator."))
        
        try:
            # Load the template
            doc = DocxTemplate(template_path)
            
            # Render the template with the context
            context = self._prepare_template_context()
            doc.render(context)
            
            # Save the document to a BytesIO object
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            
            # Return the content as bytes
            return output.getvalue()
            
        except Exception as e:
            raise UserError(_(f"Error generating DOCX content: {str(e)}"))
    
    def _generate_assessment_form_pdf(self):
        """Generate PDF assessment form using reportlab with professional formatting"""
        try:
            if not PDF_AVAILABLE:
                raise UserError(_("PDF generation is not available. Please install the required dependencies: python-docx and reportlab."))
            
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
            from io import BytesIO
            
            # Get the template context
            context = self._prepare_template_context()
            
            # Create PDF document
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            
            # Build document content
            story = []
            
            # Title
            story.append(Paragraph("CLIENT ASSESSMENT FORM", title_style))
            story.append(Spacer(1, 20))
            
            # Document Info
            story.append(Paragraph("Document Information", heading_style))
            doc_info_data = [
                ['Date:', context.get('date', '')],
                ['Time:', context.get('datetime', '')],
                ['Lead Name:', context.get('lead_name', '')],
                ['Lead ID:', context.get('lead_id', '')]
            ]
            doc_info_table = Table(doc_info_data, colWidths=[2*inch, 4*inch])
            doc_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ]))
            story.append(doc_info_table)
            story.append(Spacer(1, 20))
            
            # Client Information
            story.append(Paragraph("Client Information", heading_style))
            client_data = [
                ['Client Name:', context.get('partner_name', '')],
                ['Email:', context.get('email_from', '')],
                ['Phone:', context.get('phone', '')],
                ['Mobile:', context.get('mobile', '')],
                ['Street:', context.get('street', '')],
                ['City:', context.get('city', '')],
                ['State:', context.get('state_name', '')],
                ['Country:', context.get('country_name', '')],
                ['ZIP:', context.get('zip', '')]
            ]
            
            # Remove empty rows
            client_data = [row for row in client_data if row[1]]
            
            if client_data:
                client_table = Table(client_data, colWidths=[2*inch, 4*inch])
                client_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ]))
                story.append(client_table)
            story.append(Spacer(1, 20))
            
            # Lead Information
            story.append(Paragraph("Lead Information", heading_style))
            lead_data = [
                ['Lead Type:', context.get('type_name', '')],
                ['Priority:', context.get('priority_name', '')],
                ['Stage:', context.get('stage_name', '')],
                ['Source:', context.get('source_name', '')],
                ['Tags:', context.get('tag_names', '')],
                ['Expected Revenue:', context.get('expected_revenue_formatted', '')],
                ['Probability:', context.get('probability_formatted', '')],
                ['Salesperson:', context.get('user_name', '')],
                ['Sales Team:', context.get('team_name', '')]
            ]
            
            # Remove empty rows
            lead_data = [row for row in lead_data if row[1]]
            
            if lead_data:
                lead_table = Table(lead_data, colWidths=[2*inch, 4*inch])
                lead_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ]))
                story.append(lead_table)
            story.append(Spacer(1, 20))
            
            # Custom Fields from crm_client_assessment
            custom_fields = [
                ('Business Name', context.get('x_studio_business_name', '')),
                ('Business Type', context.get('x_studio_business_type', '')),
                ('Business Address', context.get('x_studio_business_address', '')),
                ('Business Phone', context.get('x_studio_business_phone', '')),
                ('Business Email', context.get('x_studio_business_email', '')),
                ('Industry', context.get('x_studio_industry', '')),
                ('Years in Business', context.get('x_studio_years_in_business', '')),
                ('Number of Employees', context.get('x_studio_number_of_employees', '')),
                ('Annual Revenue', context.get('x_studio_annual_revenue', '')),
                ('Business Description', context.get('x_studio_business_description', ''))
            ]
            
            # Add non-empty custom fields
            non_empty_custom = [(label, value) for label, value in custom_fields if value]
            if non_empty_custom:
                story.append(Paragraph("Business Information", heading_style))
                custom_data = [[f"{label}:", value] for label, value in non_empty_custom]
                custom_table = Table(custom_data, colWidths=[2*inch, 4*inch])
                custom_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ]))
                story.append(custom_table)
                story.append(Spacer(1, 20))
            
            # Visit Information
            if context.get('last_visit_date') or context.get('visit_count', '0') != '0':
                story.append(Paragraph("Visit Information", heading_style))
                visit_data = [
                    ['Total Visits:', context.get('visit_count', '0')],
                    ['Last Visit Date:', context.get('last_visit_date', '')],
                    ['Last Visit Location:', context.get('last_visit_location', '')],
                    ['Visit Purpose:', context.get('last_visit_purpose', '')],
                    ['Visit Notes:', context.get('last_visit_notes', '')]
                ]
                
                # Remove empty rows
                visit_data = [row for row in visit_data if row[1]]
                
                if visit_data:
                    visit_table = Table(visit_data, colWidths=[2*inch, 4*inch])
                    visit_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                    ]))
                    story.append(visit_table)
                story.append(Spacer(1, 20))
            
            # Description
            if context.get('description', ''):
                story.append(Paragraph("Description", heading_style))
                story.append(Paragraph(context.get('description', ''), normal_style))
                story.append(Spacer(1, 20))
            
            # Footer
            footer_text = f"Generated on {fields.Date.context_today(self)} at {datetime.now().strftime('%H:%M:%S')}"
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(footer_text, footer_style))
            
            # Build PDF
            doc.build(story)
            
            # Create the attachment
            file_name = f"Client_Assessment_{self.name.replace(' ', '_')}_{fields.Date.context_today(self)}.pdf"
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': base64.b64encode(output.getvalue()),
                'res_model': 'crm.lead',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # Return the download action
            return {
                'type': 'ir.actions.act_url',
                'url': f"/web/content/{attachment.id}?download=true",
                'target': 'self',
            }
            
        except Exception as e:
            raise UserError(_(f"Error generating PDF document: {str(e)}"))
