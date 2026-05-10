# -*- coding: utf-8 -*-
def migrate(cr, version):
    """
    Add missing level_progress field to hr_employee_skill table
    """
    cr.execute("""
        ALTER TABLE hr_employee_skill 
        ADD COLUMN IF NOT EXISTS level_progress INTEGER DEFAULT 0;
    """)
    
    cr.execute("""
        COMMENT ON COLUMN hr_employee_skill.level_progress 
        IS 'Progress percentage of the skill level (0-100)';
    """)
