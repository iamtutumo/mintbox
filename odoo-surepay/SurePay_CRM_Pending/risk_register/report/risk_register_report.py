from odoo import models, fields, api, _
import base64
import io
import xlsxwriter
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class RiskRegisterReport(models.AbstractModel):
    _name = 'report.risk_register.report_risk_register_pdf'
    _description = 'Risk Register PDF Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['risk.register'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'risk.register',
            'docs': docs,
            'data': data,
        }


class RiskRegisterExcelReport(models.AbstractModel):
    _name = 'report.risk_register.report_risk_excel'
    _description = 'Risk Register Excel Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'risk.register',
            'data': data or {},
        }
    
    def generate_excel_report(self, risks):
        """Generate Excel report for risks"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create worksheet
        worksheet = workbook.add_worksheet('Risk Register')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Set column widths
        worksheet.set_column('A:A', 5)     # ID
        worksheet.set_column('B:B', 40)    # Name
        worksheet.set_column('C:C', 15)    # Risk Level
        worksheet.set_column('D:D', 10)    # Impact
        worksheet.set_column('E:E', 15)    # Likelihood
        worksheet.set_column('F:F', 10)    # Risk Score
        worksheet.set_column('G:G', 20)    # Department
        worksheet.set_column('H:H', 20)    # Owner
        worksheet.set_column('I:I', 12)    # Status
        worksheet.set_column('J:J', 20)    # Created Date
        worksheet.set_column('K:K', 20)    # Created By
        worksheet.set_column('L:L', 50)    # Description
        
        # Write title
        worksheet.merge_range('A1:L1', 'Risk Register Report', title_format)
        worksheet.merge_range('A2:L2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', title_format)
        
        # Write headers
        headers = ['ID', 'Risk Title', 'Risk Level', 'Impact', 'Likelihood', 'Risk Score', 
                  'Department', 'Owner', 'Status', 'Created Date', 'Created By', 'Description']
        
        for col, header in enumerate(headers, 1):
            worksheet.write(3, col - 1, header, header_format)
        
        # Write data
        for row, risk in enumerate(risks, 4):
            worksheet.write(row, 0, risk.id, cell_format)
            worksheet.write(row, 1, risk.name or '', cell_format)
            worksheet.write(row, 2, risk.risk_level or '', cell_format)
            worksheet.write(row, 3, risk.impact or '', cell_format)
            worksheet.write(row, 4, risk.likelihood or '', cell_format)
            worksheet.write(row, 5, risk.risk_score or 0, cell_format)
            worksheet.write(row, 6, risk.department_id.name or '', cell_format)
            worksheet.write(row, 7, risk.owner_id.name or '', cell_format)
            worksheet.write(row, 8, risk.status or '', cell_format)
            worksheet.write(row, 9, risk.create_date.strftime('%Y-%m-%d %H:%M:%S') if risk.create_date else '', cell_format)
            worksheet.write(row, 10, risk.created_by.name or '', cell_format)
            worksheet.write(row, 11, risk.description or '', cell_format)
        
        workbook.close()
        output.seek(0)
        return output.read()


class RiskRegisterCSVReport(models.AbstractModel):
    _name = 'report.risk_register.report_risk_csv'
    _description = 'Risk Register CSV Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'risk.register',
            'data': data or {},
        }
    
    def generate_csv_report(self, risks):
        """Generate CSV report for risks"""
        import csv
        output = io.StringIO()
        
        fieldnames = ['ID', 'Risk Title', 'Risk Level', 'Impact', 'Likelihood', 'Risk Score', 
                     'Department', 'Owner', 'Status', 'Created Date', 'Created By', 'Description']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for risk in risks:
            writer.writerow({
                'ID': risk.id,
                'Risk Title': risk.name or '',
                'Risk Level': risk.risk_level or '',
                'Impact': risk.impact or '',
                'Likelihood': risk.likelihood or '',
                'Risk Score': risk.risk_score or 0,
                'Department': risk.department_id.name or '',
                'Owner': risk.owner_id.name or '',
                'Status': risk.status or '',
                'Created Date': risk.create_date.strftime('%Y-%m-%d %H:%M:%S') if risk.create_date else '',
                'Created By': risk.created_by.name or '',
                'Description': risk.description or '',
            })
        
        return output.getvalue()
