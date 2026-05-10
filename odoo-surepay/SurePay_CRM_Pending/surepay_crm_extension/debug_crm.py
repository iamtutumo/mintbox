#!/usr/bin/env python
# -*- coding: utf-8 -*-

def debug_crm_issues(env):
    """Debug CRM issues including white page problems."""
    print("=== CRM DEBUG ===")
    
    try:
        # Check CRM stages
        print("\n1. CRM STAGES:")
        env.cr.execute("SELECT id, name->>'en_US', sequence, fold, is_won FROM crm_stage ORDER BY sequence")
        stages = env.cr.fetchall()
        for stage in stages:
            stage_id, name, sequence, fold, is_won = stage
            print(f"   ID {stage_id}: '{name}' (Seq: {sequence}, Fold: {fold}, Won: {is_won})")
        
        # Check visible stages
        env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
        visible_count = env.cr.fetchone()[0]
        print(f"\n   Visible stages count: {visible_count}")
        
        # Check CRM leads
        print("\n2. CRM LEADS:")
        env.cr.execute("SELECT COUNT(*) FROM crm_lead")
        total_leads = env.cr.fetchone()[0]
        print(f"   Total leads: {total_leads}")
        
        # Check leads by stage
        env.cr.execute("""
            SELECT s.name->>'en_US', COUNT(l.id) as lead_count
            FROM crm_lead l
            JOIN crm_stage s ON l.stage_id = s.id
            GROUP BY s.name->>'en_US'
            ORDER BY lead_count DESC
        """)
        leads_by_stage = env.cr.fetchall()
        print("   Leads by stage:")
        for stage_name, count in leads_by_stage:
            print(f"      '{stage_name}': {count} leads")
        
        # Check leads with invalid stage references
        env.cr.execute("SELECT COUNT(*) FROM crm_lead WHERE stage_id IS NULL")
        null_stage_leads = env.cr.fetchone()[0]
        if null_stage_leads > 0:
            print(f"   ❌ Leads with NULL stage_id: {null_stage_leads}")
        
        # Check for leads pointing to non-existent stages
        env.cr.execute("""
            SELECT COUNT(*) 
            FROM crm_lead l 
            LEFT JOIN crm_stage s ON l.stage_id = s.id 
            WHERE s.id IS NULL AND l.stage_id IS NOT NULL
        """)
        invalid_stage_leads = env.cr.fetchone()[0]
        if invalid_stage_leads > 0:
            print(f"   ❌ Leads with invalid stage_id: {invalid_stage_leads}")
        
        # Check if we have at least one visible stage
        if visible_count == 0:
            print(f"\n   ❌ CRITICAL: No visible stages found!")
            print(f"   This will cause white page issues in CRM views.")
            print(f"   Fix: Create at least one visible stage.")
        
        # Check if all leads have valid stages
        if null_stage_leads > 0 or invalid_stage_leads > 0:
            print(f"\n   ❌ CRITICAL: Some leads have invalid stage references!")
            print(f"   This will cause white page issues in CRM views.")
            print(f"   Fix: Assign valid stages to all leads.")
        
        print(f"\n=== DEBUG COMPLETE ===")
        
        return {
            'visible_stages': visible_count,
            'total_leads': total_leads,
            'null_stage_leads': null_stage_leads,
            'invalid_stage_leads': invalid_stage_leads,
            'leads_by_stage': leads_by_stage
        }
        
    except Exception as e:
        print(f"❌ ERROR during debug: {str(e)}")
        return None

if __name__ == '__main__':
    print("This script should be run from within Odoo:")
    print("env['ir.logging']._log('debug', 'surepay_crm_extension', 'Starting CRM debug')")
    print("result = env['surepay_crm_extension.debug_crm'].debug_crm_issues(env)")
