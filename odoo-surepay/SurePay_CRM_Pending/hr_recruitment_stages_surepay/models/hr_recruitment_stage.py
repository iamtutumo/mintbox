# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID

class HrRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    hired_stage = fields.Boolean(
        string='Hired Stage',
        default=False,
        help='Check this if this stage represents a hired/successful candidate'
    )

    @api.model
    def _cleanup_existing_stages(self):
        """Remove all existing stages except the ones defined in this module"""
        # Get the Application Received stage (our first stage)
        app_received_stage = self.env.ref('hr_recruitment_stages_surepay.stage_application_received', False)
        if not app_received_stage:
            return  # Our stages aren't created yet
            
        # Update all job applicants to use our Application Received stage
        self.env.cr.execute("""
            UPDATE hr_applicant 
            SET stage_id = %s
            WHERE stage_id NOT IN (
                SELECT res_id 
                FROM ir_model_data 
                WHERE model = 'hr.recruitment.stage' 
                AND module = 'hr_recruitment_stages_surepay'
            )
        """, (app_received_stage.id,))
        
        # Now it's safe to delete other stages
        self.env.cr.execute("""
            DELETE FROM ir_model_data 
            WHERE model = 'hr.recruitment.stage' 
            AND module != 'hr_recruitment_stages_surepay'
            AND res_id NOT IN (
                SELECT res_id 
                FROM ir_model_data 
                WHERE model = 'hr.recruitment.stage' 
                AND module = 'hr_recruitment_stages_surepay'
            )
        """)
        
        # Also clean up any stages without ir.model.data
        self.env.cr.execute("""
            DELETE FROM hr_recruitment_stage 
            WHERE id NOT IN (
                SELECT res_id 
                FROM ir_model_data 
                WHERE model = 'hr.recruitment.stage'
            )
        """)

    def init(self):
        # Call parent's init first
        super().init()
        # Then clean up existing stages
        self._cleanup_existing_stages()
