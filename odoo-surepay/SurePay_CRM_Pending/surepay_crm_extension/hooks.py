# -*- coding: utf-8 -*-

def post_init_hook(env):
    """Clean up default Odoo CRM stages and only show SurePay stages - runs automatically on module install/reinstall."""
    print("=== SUREPAY CRM STAGE CLEANUP ===")
    print("This will remove all default Odoo stages and keep only SurePay stages.")
    
    try:
        # Step 1: Check current state first
        env.cr.execute("SELECT COUNT(*) FROM crm_stage")
        total_stages = env.cr.fetchone()[0]
        print(f"Current total stages: {total_stages}")
        
        # Step 2: Show current stages before cleanup
        env.cr.execute("SELECT id, name->>'en_US', sequence, fold FROM crm_stage ORDER BY sequence")
        current_stages = env.cr.fetchall()
        print("\nCurrent stages:")
        for stage_id, name, sequence, fold in current_stages:
            print(f"  ID {stage_id}: '{name}' (Seq: {sequence}, Folded: {fold})")
        
        # Step 3: Create a temporary stage to hold leads during cleanup
        env.cr.execute("""
            INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
            VALUES ('{"en_US": "TEMPORARY_CLEANUP"}', 999, true, false, NULL, 1, 1, NOW(), NOW())
            RETURNING id
        """)
        temp_stage_id = env.cr.fetchone()[0]
        print(f"\nStep 1: Created temporary stage with ID {temp_stage_id}")
        
        # Step 4: Move all leads to the temporary stage
        env.cr.execute("UPDATE crm_lead SET stage_id = %s", (temp_stage_id,))
        moved_leads_count = env.cr.rowcount
        print(f"Step 2: Moved {moved_leads_count} leads to temporary stage")
        
        # Step 5: Archive ALL existing stages (both default Odoo and any existing SurePay stages)
        env.cr.execute("UPDATE crm_stage SET fold = true")
        archived_count = env.cr.rowcount
        print(f"Step 3: Archived {archived_count} existing stages")
        
        # Step 6: Delete ALL existing stages to start fresh (except temporary stage)
        env.cr.execute("DELETE FROM crm_stage WHERE id != %s", (temp_stage_id,))
        deleted_count = env.cr.rowcount
        print(f"Step 4: Deleted {deleted_count} stages (keeping only temporary stage)")
        
        # Step 7: Create exactly 6 new SurePay stages with proper JSON formatting
        surepay_stages = [
            ('Cold Lead', 1, False, False),
            ('Prospecting', 10, False, False),
            ('Preparation', 20, False, False),
            ('Closing', 30, False, False),
            ('Won', 40, False, True),
            ('Lost', 50, False, False),
        ]
        
        created_stages = []
        for stage_name, sequence, fold, is_won in surepay_stages:
            # Use proper JSON formatting for the name field
            import json
            name_json = json.dumps({'en_US': stage_name})
            
            env.cr.execute("""
                INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name_json, sequence, fold, is_won))
            
            new_stage_id = env.cr.fetchone()[0]
            created_stages.append((new_stage_id, stage_name, sequence))
            print(f"Step 5: Created new SurePay stage '{stage_name}' with ID {new_stage_id}")
        
        # Step 8: Move all leads from temporary stage to Cold Lead
        cold_lead_id = next((stage_id for stage_id, name, seq in created_stages if name == 'Cold Lead'), None)
        if cold_lead_id:
            env.cr.execute("UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s", (cold_lead_id, temp_stage_id))
            updated_leads_count = env.cr.rowcount
            print(f"Step 6: Moved {updated_leads_count} leads from temporary stage to Cold Lead")
        
        # Step 9: Delete the temporary stage
        env.cr.execute("DELETE FROM crm_stage WHERE id = %s", (temp_stage_id,))
        print(f"Step 7: Deleted temporary stage")
        
        # Step 10: Verify the final state
        print(f"\n=== VERIFICATION ===")
        env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
        final_visible_count = env.cr.fetchone()[0]
        
        env.cr.execute("SELECT name->>'en_US', sequence, fold, is_won FROM crm_stage WHERE fold = false ORDER BY sequence")
        final_stages = env.cr.fetchall()
        
        print(f"Total visible stages: {final_visible_count}")
        print("Final SurePay stages:")
        for stage in final_stages:
            name, sequence, fold, is_won = stage
            print(f"  - {name} (Seq: {sequence}, Won: {is_won})")
        
        # Step 11: Check for any remaining issues
        env.cr.execute("SELECT COUNT(*) FROM crm_stage")
        total_final_stages = env.cr.fetchone()[0]
        
        if final_visible_count == 6 and total_final_stages == 6:
            print(f"\n✅ SUCCESS: Cleanup completed successfully!")
            print(f"✅ SUCCESS: Exactly {final_visible_count} visible SurePay stages")
            print(f"✅ SUCCESS: No default Odoo stages remaining")
            print(f"✅ SUCCESS: All leads moved to Cold Lead stage")
            print(f"✅ SUCCESS: SurePay stages: Cold Lead, Prospecting, Preparation, Closing, Won, Lost")
            print(f"\n🎉 CLEANUP COMPLETE! Refresh your CRM page to see only SurePay stages.")
        else:
            print(f"\n❌ WARNING: Unexpected stage count")
            print(f"   Visible stages: {final_visible_count} (expected: 6)")
            print(f"   Total stages: {total_final_stages} (expected: 6)")
    
    except Exception as e:
        print(f"❌ ERROR during stage cleanup: {str(e)}")
        raise

def uninstall_hook(env):
    """Restore default Odoo CRM stages when module is uninstalled."""
    print("=== RESTORING DEFAULT ODOO CRM STAGES ===")
    
    try:
        # Archive all current SurePay stages
        env.cr.execute("UPDATE crm_stage SET fold = true")
        archived_count = env.cr.rowcount
        print(f"Archived {archived_count} SurePay stages")
        
        # Create default Odoo CRM stages
        default_stages = [
            ('New', 1, False, False),
            ('Qualified', 2, False, False),
            ('Proposition', 3, False, False),
            ('Won', 4, False, True),
            ('Lost', 5, False, False),
        ]
        
        created_count = 0
        for stage_name, sequence, fold, is_won in default_stages:
            import json
            name_json = json.dumps({'en_US': stage_name})
            
            env.cr.execute("""
                INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
            """, (name_json, sequence, fold, is_won))
            created_count += 1
            print(f"Created default stage '{stage_name}'")
        
        print(f"✅ SUCCESS: Restored {created_count} default Odoo CRM stages")
        print(f"✅ SUCCESS: Module uninstallation cleanup completed")
        
    except Exception as e:
        print(f"❌ ERROR during stage restoration: {str(e)}")
        # Don't raise here to avoid blocking uninstallation
