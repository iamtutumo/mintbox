from odoo import http
from odoo.http import request, content_disposition
from odoo.addons.web.controllers.main import ReportController
import base64
import io


class RiskRegisterController(http.Controller):
    
    @http.route('/web/export/risk/excel', type='http', auth='user')
    def export_risk_excel(self, **kwargs):
        """Export risks to Excel format"""
        risk_ids = kwargs.get('ids', '').split(',')
        risks = request.env['risk.register'].browse([int(id) for id in risk_ids if id.isdigit()])
        
        # Apply department restrictions
        if not request.env.user.has_group('risk_register.group_risk_manager') and \
           not request.env.user.has_group('risk_register.group_risk_admin'):
            if request.env.user.employee_id and request.env.user.employee_id.department_id:
                risks = risks.filtered(lambda r: r.department_id.id == request.env.user.employee_id.department_id.id)
            else:
                risks = request.env['risk.register'].browse([])
        
        # Generate Excel report
        report = request.env['report.risk_register.report_risk_excel']
        excel_data = report.sudo().generate_excel_report(risks)
        
        # Return as downloadable file
        excel_base64 = base64.b64encode(excel_data)
        response = request.make_response(
            excel_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition('risk_register.xlsx'))
            ]
        )
        return response
    
    @http.route('/web/export/risk/csv', type='http', auth='user')
    def export_risk_csv(self, **kwargs):
        """Export risks to CSV format"""
        risk_ids = kwargs.get('ids', '').split(',')
        risks = request.env['risk.register'].browse([int(id) for id in risk_ids if id.isdigit()])
        
        # Apply department restrictions
        if not request.env.user.has_group('risk_register.group_risk_manager') and \
           not request.env.user.has_group('risk_register.group_risk_admin'):
            if request.env.user.employee_id and request.env.user.employee_id.department_id:
                risks = risks.filtered(lambda r: r.department_id.id == request.env.user.employee_id.department_id.id)
            else:
                risks = request.env['risk.register'].browse([])
        
        # Generate CSV report
        report = request.env['report.risk_register.report_risk_csv']
        csv_data = report.sudo().generate_csv_report(risks)
        
        # Return as downloadable file
        response = request.make_response(
            csv_data,
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', content_disposition('risk_register.csv'))
            ]
        )
        return response
