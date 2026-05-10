# -*- coding: utf-8 -*-

def post_init_hook(cr, registry):
    """
    Post-init hook to clean up existing stages and ensure only our stages exist.
    This runs after the module is installed or updated.
    """
    # First, unlink all existing stages
    cr.execute("""
        -- First, unset any default stages in jobs
        UPDATE hr_job 
        SET default_stage_id = NULL 
        WHERE default_stage_id IS NOT NULL;
        
        -- Then delete all stages that don't belong to our module
        DELETE FROM ir_model_data 
        WHERE model = 'hr.recruitment.stage' 
        AND module != 'hr_recruitment_stages_surepay';
        
        -- Delete all stages that don't have an entry in ir_model_data
        DELETE FROM hr_recruitment_stage 
        WHERE id NOT IN (
            SELECT res_id FROM ir_model_data 
            WHERE model = 'hr.recruitment.stage'
        );
        
        -- Make sure our stages are properly sequenced
        UPDATE hr_recruitment_stage stage
        SET sequence = subquery.sequence
        FROM (
            SELECT id, row_number() OVER (ORDER BY sequence) * 10 as sequence 
            FROM hr_recruitment_stage
        ) as subquery
        WHERE stage.id = subquery.id;
    """)
