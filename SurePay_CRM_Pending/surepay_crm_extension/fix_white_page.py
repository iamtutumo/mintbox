#!/usr/bin/env python
# -*- coding: utf-8 -*-

def fix_white_page_issue(env):
    """Fix white page issue by ensuring all leads have valid stage references."""
    print("=== FIXING WHITE PAGE ISSUE ===")
    
    try:
        # Step 1: Check current state
        print("\n1. Checking current state...")
        
        # Count total leads
        env.cr.execute("SELECT COUNT(*) FROM crm_lead")
        total_leads = env.cr.fetchone()[0]
        print(f"   Total leads: {total_leads}")
        
        # Count leads with NULL stage_id
        env.cr.execute("SELECT COUNT(*) FROM crm_lead WHERE stage_id IS NULL")
        null_stage_leads = env.cr.fetchone()[0]
        print(f"   Leads with NULL stage_id: {null_stage_leads}")
        
        # Count leads with invalid stage references
        env.cr.execute("""
            SELECT COUNT(*) 
            FROM crm_lead l 
            LEFT JOIN crm_stage s ON l.stage_id = s.id 
            WHERE s.id IS NULL AND l.stage_id IS NOT NULL
        """)
        invalid_stage_leads = env.cr.fetchone()[0]
        print(f"   Leads with invalid stage_id: {invalid_stage_leads}")
        
        # Count visible stages
        env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
        visible_stages = env.cr.fetchone()[0]
        print(f"   Visible stages: {visible_stages}")
        
        # Step 2: Ensure we have at least one visible stage
        print("\n2. Ensuring visible stages exist...")
        if visible_stages == 0:
            print("   ❌ No visible stages found! Creating default SurePay stages...")
            
            # Create SurePay stages if they don't exist
            surepay_stages = [
                ('Cold Lead', 1, False, False),
                ('Prospecting', 10, False, False),
                ('Preparation', 20, False, False),
                ('Closing', 30, False, False),
                ('Won', 40, False, True),
                ('Lost', 50, False, False),
            ]
            
            for stage_name, sequence, fold, is_won in surepay_stages:
                import json
                name_json = json.dumps({'en_US': stage_name})
                
                env.cr.execute("""
                    INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                    VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE SET
                        sequence = EXCLUDED.sequence,
                        fold = EXCLUDED.fold,
                        is_won = EXCLUDED.is_won,
                        write_date = NOW()
                """, (name_json, sequence, fold, is_won))
                print(f"   ✓ Created/updated stage: {stage_name}")
            
            print("   ✅ SurePay stages created/updated")
        
        # Step 3: Get the Cold Lead stage ID (default stage)
        print("\n3. Getting default stage...")
        env.cr.execute("SELECT id FROM crm_stage WHERE name->>'en_US' = 'Cold Lead' LIMIT 1")
        cold_lead_stage = env.cr.fetchone()
        
        if cold_lead_stage:
            cold_lead_stage_id = cold_lead_stage[0]
            print(f"   ✓ Cold Lead stage ID: {cold_lead_stage_id}")
        else:
            print("   ❌ Cold Lead stage not found! Creating it...")
            import json
            name_json = json.dumps({'en_US': 'Cold Lead'})
            
            env.cr.execute("""
                INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
                RETURNING id
            """, (name_json, 1, False, False))
            
            cold_lead_stage_id = env.cr.fetchone()[0]
            print(f"   ✓ Created Cold Lead stage with ID: {cold_lead_stage_id}")
        
        # Step 4: Fix leads with NULL stage_id
        print("\n4. Fixing leads with NULL stage_id...")
        if null_stage_leads > 0:
            env.cr.execute("UPDATE crm_lead SET stage_id = %s WHERE stage_id IS NULL", (cold_lead_stage_id,))
            fixed_null_leads = env.cr.rowcount
            print(f"   ✓ Fixed {fixed_null_leads} leads with NULL stage_id")
        else:
            print("   ✓ No leads with NULL stage_id found")
        
        # Step 5: Fix leads with invalid stage references
        print("\n5. Fixing leads with invalid stage references...")
        if invalid_stage_leads > 0:
            env.cr.execute("""
                UPDATE crm_lead 
                SET stage_id = %s 
                WHERE stage_id IS NOT NULL 
                AND NOT EXISTS (SELECT 1 FROM crm_stage WHERE id = crm_lead.stage_id)
            """, (cold_lead_stage_id,))
            fixed_invalid_leads = env.cr.rowcount
            print(f"   ✓ Fixed {fixed_invalid_leads} leads with invalid stage references")
        else:
            print("   ✓ No leads with invalid stage references found")
        
        # Step 6: Ensure all SurePay stages are visible
        print("\n6. Ensuring SurePay stages are visible...")
        surepay_stage_names = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
        for stage_name in surepay_stage_names:
            env.cr.execute("UPDATE crm_stage SET fold = false WHERE name->>'en_US' = %s", (stage_name,))
            print(f"   ✓ Made '{stage_name}' visible")
        
        # Step 7: Archive non-SurePay stages
        print("\n7. Archiving non-SurePay stages...")
        env.cr.execute("""
            UPDATE crm_stage SET fold = true 
            WHERE name->>'en_US' NOT IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')
        """)
        archived_stages = env.cr.rowcount
        print(f"   ✓ Archived {archived_stages} non-SurePay stages")
        
        # Step 8: Final verification
        print("\n8. Final verification...")
        env.cr.execute("SELECT COUNT(*) FROM crm_lead WHERE stage_id IS NULL")
        final_null_leads = env.cr.fetchone()[0]
        
        env.cr.execute("""
            SELECT COUNT(*) 
            FROM crm_lead l 
            LEFT JOIN crm_stage s ON l.stage_id = s.id 
            WHERE s.id IS NULL AND l.stage_id IS NOT NULL
        """)
        final_invalid_leads = env.cr.fetchone()[0]
        
        env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
        final_visible_stages = env.cr.fetchone()[0]
        
        print(f"   Final leads with NULL stage_id: {final_null_leads}")
        print(f"   Final leads with invalid stage_id: {final_invalid_leads}")
        print(f"   Final visible stages: {final_visible_stages}")
        
        if final_null_leads == 0 and final_invalid_leads == 0 and final_visible_stages > 0:
            print(f"\n✅ SUCCESS: White page issue fixed!")
            print(f"✅ All leads now have valid stage references")
            print(f"✅ Visible stages are available")
            print(f"✅ Refresh your CRM page to see the leads")
        else:
            print(f"\n❌ WARNING: Some issues may remain")
            print(f"   Leads with NULL stage_id: {final_null_leads}")
            print(f"   Leads with invalid stage_id: {final_invalid_leads}")
            print(f"   Visible stages: {final_visible_stages}")
        
        print(f"\n=== FIX COMPLETE ===")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during fix: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("This script should be run from within Odoo:")
    print("env['surepay_crm_extension.fix_white_page'].fix_white_page_issue(env)")
