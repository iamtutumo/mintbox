#!/usr/bin/env python3
"""
Script to clean up activities that reference missing models.
This resolves the KeyError: 'hr.applicant' error.
"""

from odoo import api, SUPERUSER_ID

def cleanup_activities(registry):
    """Clean up activities that reference missing models"""
    env = api.Environment(registry.cursor(), SUPERUSER_ID, {})
    
    print("Starting cleanup activities...")
    
    # List of models that might be missing
    missing_models = ['hr.applicant']
    
    # Clean up configuration fields that might be missing
    try:
        # Check if providers_state field exists in res.config.settings
        config_settings = env['res.config.settings']
        if not hasattr(config_settings._fields, 'providers_state'):
            print("Field 'providers_state' not found in res.config.settings - this is expected if auth_oauth module is not installed")
    except Exception as e:
        print(f"Error checking providers_state field: {e}")
    
    for model_name in missing_models:
        try:
            # Check if model exists
            env['ir.model'].sudo().search([('model', '=', model_name)])
            print(f"Model {model_name} exists - no cleanup needed")
        except Exception:
            print(f"Model {model_name} not found - cleaning up activities...")
            
            # Remove activities that reference the missing model
            activities = env['mail.activity'].sudo().search([
                ('res_model', '=', model_name)
            ])
            
            if activities:
                print(f"Found {len(activities)} activities for {model_name} - removing...")
                activities.unlink()
                print(f"Removed {len(activities)} activities")
            else:
                print(f"No activities found for {model_name}")
    
    # Also try to clean up any activities that might cause issues
    try:
        # Clean up activities for any model that might not exist
        all_activities = env['mail.activity'].sudo().search([])
        models_to_check = set(all_activities.mapped('res_model'))
        
        for model in models_to_check:
            try:
                env[model].sudo().search([('id', '=', 1)], limit=1)
            except Exception:
                print(f"Model {model} is not accessible - cleaning up activities...")
                bad_activities = env['mail.activity'].sudo().search([('res_model', '=', model)])
                if bad_activities:
                    print(f"Removing {len(bad_activities)} activities for {model}")
                    bad_activities.unlink()
    except Exception as e:
        print(f"Error in general cleanup: {e}")
    
    print("Cleanup completed.")
