#!/usr/bin/env python
# -*- coding: utf-8 -*-

def diagnose_white_page(env):
    """Diagnose white page issue in CRM."""
    print("=== DIAGNOSING WHITE PAGE ISSUE ===")
    
    try:
        # Check 1: Verify CRM stages exist and are visible
        print("\n1. Checking CRM stages...")
        env.cr.execute("""
            SELECT id, name->>'en_US' as stage_name, sequence, fold, is_won 
            FROM crm_stage 
            ORDER BY sequence
        """)
        stages = env.cr.fetchall()
        print(f"   Total stages: {len(stages)}")
        visible_stages = []
        for stage in stages:
            stage_id, stage_name, sequence, fold, is_won = stage
            print(f"   ID {stage_id}: '{stage_name}' (Seq: {sequence}, Fold: {fold}, Won: {is_won})")
            if not fold:
                visible_stages.append(stage_name)
        
        print(f"   Visible stages: {visible_stages}")
        
        # Check 2: Verify leads exist and have valid stages
        print("\n2. Checking CRM leads...")
        env.cr.execute("SELECT COUNT(*) FROM crm_lead")
        total_leads = env.cr.fetchone()[0]
        print(f"   Total leads: {total_leads}")
        
        if total_leads > 0:
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
        
        # Check 3: Check leads with NULL or invalid stages
        env.cr.execute("SELECT COUNT(*) FROM crm_lead WHERE stage_id IS NULL")
        null_stage_leads = env.cr.fetchone()[0]
        print(f"   Leads with NULL stage_id: {null_stage_leads}")
        
        env.cr.execute("""
            SELECT COUNT(*) 
            FROM crm_lead l 
            LEFT JOIN crm_stage s ON l.stage_id = s.id 
            WHERE s.id IS NULL AND l.stage_id IS NOT NULL
        """)
        invalid_stage_leads = env.cr.fetchone()[0]
        print(f"   Leads with invalid stage_id: {invalid_stage_leads}")
        
        # Check 4: Check if kanban view will show any leads
        print("\n3. Checking kanban view visibility...")
        env.cr.execute("""
            SELECT COUNT(*) 
            FROM crm_lead l 
            JOIN crm_stage s ON l.stage_id = s.id 
            WHERE s.fold = false
        """)
        visible_leads = env.cr.fetchone()[0]
        print(f"   Leads that should appear in kanban view: {visible_leads}")
        
        # Check 5: Check for SurePay stages specifically
        surepay_stages = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
        print("\n4. Checking SurePay stages...")
        for stage_name in surepay_stages:
            env.cr.execute("SELECT id, fold FROM crm_stage WHERE name->>'en_US' = %s", (stage_name,))
            result = env.cr.fetchone()
            if result:
                stage_id, fold = result
                print(f"   '{stage_name}': ID {stage_id}, Fold: {fold}")
            else:
                print(f"   '{stage_name}': NOT FOUND")
        
        # Check 6: Analyze potential issues
        print("\n5. Issue Analysis:")
        issues = []
        
        if len(visible_stages) == 0:
            issues.append("❌ No visible stages found - this will cause white page")
        
        if visible_leads == 0 and total_leads > 0:
            issues.append("❌ No leads will appear in kanban view - check stage visibility")
        
        if null_stage_leads > 0:
            issues.append(f"❌ {null_stage_leads} leads have NULL stage_id")
        
        if invalid_stage_leads > 0:
            issues.append(f"❌ {invalid_stage_leads} leads have invalid stage_id")
        
        missing_surepay = []
        for stage_name in surepay_stages:
            env.cr.execute("SELECT id FROM crm_stage WHERE name->>'en_US' = %s", (stage_name,))
            if not env.cr.fetchone():
                missing_surepay.append(stage_name)
        
        if missing_surepay:
            issues.append(f"❌ Missing SurePay stages: {missing_surepay}")
        
        if issues:
            print("   Issues found:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   ✅ No obvious issues found")
        
        # Check 7: Provide recommendations
        print("\n6. Recommendations:")
        if len(visible_stages) == 0:
            print("   - Make at least one stage visible (fold = false)")
        
        if visible_leads == 0 and total_leads > 0:
            print("   - Ensure leads have valid stage references")
            print("   - Make sure stages are not folded")
        
        if missing_surepay:
            print("   - Create missing SurePay stages")
        
        if null_stage_leads > 0 or invalid_stage_leads > 0:
            print("   - Fix leads with invalid stage references")
        
        print(f"\n=== DIAGNOSIS COMPLETE ===")
        return {
            'total_stages': len(stages),
            'visible_stages': visible_stages,
            'total_leads': total_leads,
            'visible_leads': visible_leads,
            'null_stage_leads': null_stage_leads,
            'invalid_stage_leads': invalid_stage_leads,
            'issues': issues
        }
        
    except Exception as e:
        print(f"❌ ERROR during diagnosis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print("This script should be run from within Odoo:")
    print("env['surepay_crm_extension.diagnose_white_page'].diagnose_white_page(env)")
