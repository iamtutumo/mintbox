#!/usr/bin/env python3
"""
Manual script to clean up activities that reference missing models.
Run this script directly in the Odoo shell to fix KeyError: 'hr.applicant' error.

Usage:
1. Go to Odoo container: docker-compose exec odoo bash
2. Run: python3 /mnt/extra-addons/customs/surepay_crm_extension/manual_cleanup.py
"""

import odoo
from odoo import api, SUPERUSER_ID

def cleanup_hr_applicant_activities():
    """Clean up activities that reference hr.applicant model"""
    registry = odoo.modules.registry.Registry.new(odoo.tools.config['db_name'])
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("Starting cleanup of hr.applicant activities...")
        
        try:
            # Check if hr.applicant model exists
            env['ir.model'].sudo().search([('model', '=', 'hr.applicant')])
            print("Model hr.applicant exists - no cleanup needed")
            return False
        except Exception:
            print("Model hr.applicant not found - cleaning up activities...")
            
            # Remove activities that reference the missing model
            activities = env['mail.activity'].sudo().search([
                ('res_model', '=', 'hr.applicant')
            ])
            
            if activities:
                print(f"Found {len(activities)} activities for hr.applicant - removing...")
                activities.unlink()
                print(f"Removed {len(activities)} activities")
                return True
            else:
                print("No activities found for hr.applicant")
                return False

if __name__ == '__main__':
    cleanup_hr_applicant_activities()
