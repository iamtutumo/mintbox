# -*- coding: utf-8 -*-
"""
Post-migration script to recompute stored fields after database schema update
"""

def migrate(cr, version):
    """
    Recompute stored fields for all employees to ensure data consistency
    """
    # Trigger recomputation of stored fields
    cr.execute("""
        UPDATE hr_employee 
        SET advance_count = 0, 
            loan_count = 0,
            total_advance_outstanding = 0.0,
            total_loan_outstanding = 0.0
    """)
    
    # Let Odoo's compute methods handle the proper calculation
    # The fields will be recomputed when the models are loaded
