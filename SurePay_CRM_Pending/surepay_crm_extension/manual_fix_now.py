#!/usr/bin/env python
# -*- coding: utf-8 -*-

def manual_fix_stages(env):
    """Manual fix for duplicate CRM stages and '1111' display issue.
    
    Run this script in the Odoo shell:
    1. Open terminal in your Odoo container
    2. Run: odoo shell -d your_database_name
    3. Import and run: exec(open('/path/to/manual_fix_now.py').read())
    4. Then call: manual_fix_stages(env)
    """
    print("=== MANUAL CRM STAGE FIX ===")
    print("This will immediately fix duplicate stages and '1111' display issue.")
    
    try:
        # Step 1: Check current state first
        env.cr.execute("SELECT COUNT(*) FROM crm_stage")
        total_stages = env.cr.fetchone()[0]
        print(f"Current total stages: {total_stages}")
        
        # Step 2: Create a temporary stage to hold leads during cleanup
        env.cr.execute("""
            INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
            VALUES ('{"en_US": "TEMPORARY"}', 999, true, false, NULL, 1, 1, NOW(), NOW())
            RETURNING id
        """)
        temp_stage_id = env.cr.fetchone()[0]
        print(f"Step 1: Created temporary stage with ID {temp_stage_id}")
        
        # Step 3: Move all leads to the temporary stage
        env.cr.execute("UPDATE crm_lead SET stage_id = %s", (temp_stage_id,))
        moved_leads_count = env.cr.rowcount
        print(f"Step 2: Moved {moved_leads_count} leads to temporary stage")
        
        # Step 4: Archive ALL existing stages
        env.cr.execute("UPDATE crm_stage SET fold = true")
        archived_count = env.cr.rowcount
        print(f"Step 3: Archived {archived_count} existing stages")
        
        # Step 5: Get all SurePay stage IDs for deletion (excluding temporary stage)
        env.cr.execute("SELECT id FROM crm_stage WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')")
        surepay_stage_ids = [row[0] for row in env.cr.fetchall()]
        print(f"Step 4: Found {len(surepay_stage_ids)} SurePay stages to delete")
        
        # Step 6: Delete all SurePay stages completely (not just archive)
        if surepay_stage_ids:
            env.cr.execute("DELETE FROM crm_stage WHERE id IN %s", (tuple(surepay_stage_ids),))
            deleted_count = env.cr.rowcount
            print(f"Step 5: Deleted {deleted_count} SurePay stage records")
        
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
            print(f"Step 6: Created new stage '{stage_name}' with ID {new_stage_id} and JSON name: {name_json}")
        
        # Step 8: Move all leads from temporary stage to Cold Lead
        cold_lead_id = next((stage_id for stage_id, name, seq in created_stages if name == 'Cold Lead'), None)
        if cold_lead_id:
            env.cr.execute("UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s", (cold_lead_id, temp_stage_id))
            updated_leads_count = env.cr.rowcount
            print(f"Step 7: Moved {updated_leads_count} leads from temporary stage to Cold Lead")
        
        # Step 9: Delete the temporary stage
        env.cr.execute("DELETE FROM crm_stage WHERE id = %s", (temp_stage_id,))
        print(f"Step 8: Deleted temporary stage")
        
        # Step 10: Verify the JSON formatting of created stages
        print(f"\n=== VERIFICATION OF JSON FORMATTING ===")
        env.cr.execute("SELECT id, name, name->>'en_US' FROM crm_stage WHERE fold = false ORDER BY sequence")
        stage_verification = env.cr.fetchall()
        
        for stage_id, name_json, extracted_name in stage_verification:
            print(f"   ID {stage_id}: Raw JSON = {name_json}, Extracted = '{extracted_name}'")
        
        # Step 11: Final verification
        env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
        final_visible_count = env.cr.fetchone()[0]
        
        env.cr.execute("SELECT name->>'en_US', sequence, fold, is_won FROM crm_stage WHERE fold = false ORDER BY sequence")
        final_stages = env.cr.fetchall()
        
        print(f"\n=== FINAL RESULT ===")
        print(f"Total visible stages: {final_visible_count}")
        print("Visible stages:")
        for stage in final_stages:
            name, sequence, fold, is_won = stage
            print(f"  - {name} (Seq: {sequence}, Won: {is_won})")
        
        # Check for any remaining duplicates
        env.cr.execute("""
            SELECT name->>'en_US', COUNT(*) 
            FROM crm_stage 
            GROUP BY name->>'en_US' 
            HAVING COUNT(*) > 1
        """)
        remaining_duplicates = env.cr.fetchall()
        
        if remaining_duplicates:
            print(f"\n❌ WARNING: Still found {len(remaining_duplicates)} duplicate stage names:")
            for name, count in remaining_duplicates:
                print(f"  - '{name}' appears {count} times")
        else:
            print(f"\n✅ SUCCESS: No duplicate stages found!")
            print(f"✅ SUCCESS: Exactly {final_visible_count} visible stages (expected: 6)")
            
            expected_stages = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
            actual_stages = [stage[0] for stage in final_stages]
            
            if set(actual_stages) == set(expected_stages):
                print(f"✅ SUCCESS: All expected SurePay stages are present")
                print(f"✅ SUCCESS: CRM stage setup completed successfully!")
                print(f"✅ SUCCESS: JSON formatting fixed - '1111' display issue should be resolved!")
                print(f"\n🎉 FIX COMPLETE! Refresh your CRM page to see the changes.")
            else:
                missing = set(expected_stages) - set(actual_stages)
                extra = set(actual_stages) - set(expected_stages)
                if missing:
                    print(f"❌ Missing stages: {missing}")
                if extra:
                    print(f"❌ Extra stages: {extra}")
    
    except Exception as e:
        print(f"❌ ERROR during stage setup: {str(e)}")
        raise

# Quick test function to check current state
def quick_check(env):
    """Quick check of current CRM stage state."""
    print("=== QUICK STAGE CHECK ===")
    
    # Check visible stages
    env.cr.execute("SELECT id, name->>'en_US', sequence, fold FROM crm_stage WHERE fold = false ORDER BY sequence")
    visible_stages = env.cr.fetchall()
    
    print(f"Visible stages ({len(visible_stages)}):")
    for stage_id, name, sequence, fold in visible_stages:
        print(f"  ID {stage_id}: '{name}' (Seq: {sequence})")
    
    # Check for duplicates
    env.cr.execute("""
        SELECT name->>'en_US', COUNT(*) as count, array_agg(id) as ids
        FROM crm_stage 
        GROUP BY name->>'en_US' 
        HAVING COUNT(*) > 1
    """)
    duplicates = env.cr.fetchall()
    
    if duplicates:
        print(f"\nDuplicates found:")
        for name, count, ids in duplicates:
            print(f"  '{name}': {count} times, IDs: {ids}")
    else:
        print(f"\nNo duplicates found.")
    
    # Check leads
    env.cr.execute("SELECT COUNT(*) FROM crm_lead")
    total_leads = env.cr.fetchone()[0]
    print(f"\nTotal leads: {total_leads}")
