#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emergency fix script for duplicate CRM stages.
This script provides a comprehensive solution to remove all duplicate stages and ensure only the 6 SurePay stages remain visible.
"""

def fix_duplicate_stages_now(env):
    """
    Comprehensive fix for duplicate CRM stages.
    This is an emergency cleanup that will:
    1. Archive ALL existing stages
    2. Delete all SurePay stage records to start fresh
    3. Create exactly 6 new SurePay stages
    4. Update all leads to use Cold Lead as default
    """
    print("=== EMERGENCY DUPLICATE STAGES FIX ===\n")
    
    try:
        # Step 1: Archive ALL stages first
        env.cr.execute("UPDATE crm_stage SET fold = true")
        archived_count = env.cr.rowcount
        print(f"Step 1: Archived {archived_count} existing stages")
        
        # Step 2: Get all SurePay stage IDs for deletion
        env.cr.execute("SELECT id FROM crm_stage WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')")
        surepay_stage_ids = [row[0] for row in env.cr.fetchall()]
        print(f"Step 2: Found {len(surepay_stage_ids)} SurePay stages to delete")
        
        # Step 3: Delete all SurePay stages completely (not just archive)
        if surepay_stage_ids:
            env.cr.execute("DELETE FROM crm_stage WHERE id IN %s", (tuple(surepay_stage_ids),))
            deleted_count = env.cr.rowcount
            print(f"Step 3: Deleted {deleted_count} SurePay stage records")
        
        # Step 4: Create exactly 6 new SurePay stages
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
            env.cr.execute("""
                INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
                RETURNING id
            """, (f'{{"en_US": "{stage_name}"}}', sequence, fold, is_won))
            
            new_stage_id = env.cr.fetchone()[0]
            created_stages.append((new_stage_id, stage_name, sequence))
            print(f"Step 4: Created new stage '{stage_name}' with ID {new_stage_id}")
        
        # Step 5: Update all leads to use Cold Lead as default
        cold_lead_id = next((stage_id for stage_id, name, seq in created_stages if name == 'Cold Lead'), None)
        if cold_lead_id:
            # Update leads without a stage
            env.cr.execute("UPDATE crm_lead SET stage_id = %s WHERE stage_id IS NULL", (cold_lead_id,))
            updated_leads_no_stage = env.cr.rowcount
            
            # Update leads with archived stages
            env.cr.execute("UPDATE crm_lead SET stage_id = %s WHERE stage_id IN (SELECT id FROM crm_stage WHERE fold = true)", (cold_lead_id,))
            updated_leads_archived = env.cr.rowcount
            
            print(f"Step 5: Updated {updated_leads_no_stage} leads without stage and {updated_leads_archived} leads with archived stages to Cold Lead")
        
        # Step 6: Verify the final result
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
            return False
        else:
            print(f"\n✅ SUCCESS: No duplicate stages found!")
            print(f"✅ SUCCESS: Exactly {final_visible_count} visible stages (expected: 6)")
            
            expected_stages = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
            actual_stages = [stage[0] for stage in final_stages]
            
            if set(actual_stages) == set(expected_stages):
                print(f"✅ SUCCESS: All expected SurePay stages are present")
                return True
            else:
                missing = set(expected_stages) - set(actual_stages)
                extra = set(actual_stages) - set(expected_stages)
                if missing:
                    print(f"❌ Missing stages: {missing}")
                if extra:
                    print(f"❌ Extra stages: {extra}")
                return False
    
    except Exception as e:
        print(f"❌ ERROR during fix: {str(e)}")
        return False

def check_current_stage_status(env):
    """Check current stage status before applying fix."""
    print("=== CURRENT STAGE STATUS ===\n")
    
    # Count all stages
    env.cr.execute("SELECT COUNT(*) FROM crm_stage")
    total_count = env.cr.fetchone()[0]
    print(f"Total stages in database: {total_count}")
    
    # Count visible stages
    env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
    visible_count = env.cr.fetchone()[0]
    print(f"Visible stages (fold = false): {visible_count}")
    
    # Count hidden stages
    env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = true")
    hidden_count = env.cr.fetchone()[0]
    print(f"Hidden stages (fold = true): {hidden_count}")
    
    # Show visible stages
    env.cr.execute("SELECT name->>'en_US', sequence, fold, is_won FROM crm_stage WHERE fold = false ORDER BY sequence")
    visible_stages = env.cr.fetchall()
    print(f"\nVisible stages:")
    for stage in visible_stages:
        name, sequence, fold, is_won = stage
        print(f"  - {name} (Seq: {sequence}, Won: {is_won})")
    
    # Check for duplicates
    env.cr.execute("""
        SELECT name->>'en_US', COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM crm_stage 
        GROUP BY name->>'en_US' 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    duplicates = env.cr.fetchall()
    
    if duplicates:
        print(f"\n❌ DUPLICATE STAGES FOUND:")
        for name, count, ids in duplicates:
            print(f"  - '{name}' appears {count} times (IDs: {ids})")
    else:
        print(f"\n✅ No duplicate stages found")
    
    return {
        'total_count': total_count,
        'visible_count': visible_count,
        'hidden_count': hidden_count,
        'visible_stages': visible_stages,
        'duplicates': duplicates
    }

if __name__ == "__main__":
    print("This script should be called from within Odoo environment.")
    print("Usage:")
    print("1. Check current status: env['surepay.crm.extension'].check_current_stage_status(env)")
    print("2. Fix duplicates: env['surepay.crm.extension'].fix_duplicate_stages_now(env)")
