#!/usr/bin/env python
# -*- coding: utf-8 -*-

def fix_crm_stages(env):
    """Manually fix CRM stages to show only SurePay stages."""
    print("=== FIXING CRM STAGES ===")
    
    try:
        # Get the CRM stage model
        crm_stage = env['crm.stage']
        
        # Call the cleanup method
        result = crm_stage.cleanup_duplicate_stages()
        
        if result:
            print("✅ SUCCESS: CRM stages fixed successfully!")
            print("✅ Refresh your CRM page to see only SurePay stages.")
        else:
            print("❌ ERROR: Failed to fix CRM stages.")
            
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    # This script should be run from within Odoo
    print("This script should be run from within Odoo using the following command:")
    print("env['crm.stage'].cleanup_duplicate_stages()")
