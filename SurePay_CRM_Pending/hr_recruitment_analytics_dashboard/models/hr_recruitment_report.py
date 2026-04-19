# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class HrRecruitmentReport(models.Model):
    _name = 'hr.recruitment.report'
    _description = 'Recruitment Analysis'
    _auto = False
    _rec_name = 'job_id'

    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    stage_id = fields.Many2one('hr.recruitment.stage', string='Stage', readonly=True)
    
    # Counts
    applicant_count = fields.Integer(string='Total Applicants', readonly=True)
    hired_count = fields.Integer(string='Hired', readonly=True)
    rejected_count = fields.Integer(string='Rejected', readonly=True)
    
    # Time metrics
    avg_time_to_hire = fields.Float(string='Avg Time to Hire (Days)', readonly=True)
    create_date = fields.Date(string='Application Date', readonly=True)
    
    # Rates
    conversion_rate = fields.Float(string='Conversion Rate %', readonly=True)
    
    def init(self):
        """Create the view"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () as id,
                    a.job_id,
                    a.department_id,
                    a.company_id,
                    a.stage_id,
                    DATE(a.create_date) as create_date,
                    COUNT(a.id) as applicant_count,
                    COUNT(CASE WHEN s.hired_stage = true THEN 1 END) as hired_count,
                    COUNT(CASE WHEN s.fold = true THEN 1 END) as rejected_count,
                    AVG(CASE 
                        WHEN s.hired_stage = true 
                        THEN EXTRACT(DAY FROM (a.write_date - a.create_date))
                        ELSE NULL 
                    END) as avg_time_to_hire,
                    CASE 
                        WHEN COUNT(a.id) > 0 
                        THEN (COUNT(CASE WHEN s.hired_stage = true THEN 1 END)::float / COUNT(a.id)::float * 100)
                        ELSE 0 
                    END as conversion_rate
                FROM hr_applicant a
                LEFT JOIN hr_recruitment_stage s ON a.stage_id = s.id
                GROUP BY a.job_id, a.department_id, a.company_id, a.stage_id, DATE(a.create_date)
            )
        """ % self._table)
