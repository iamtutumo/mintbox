#!/usr/bin/env python
# -*- coding: utf-8 -*-

def diagnose_stages(env):
    """Diagnose CRM stage issues including '1111' display problems."""
    print("=== CRM STAGE DIAGNOSIS ===")
    
    # Check all stages in the database
    env.cr.execute("SELECT id, name, sequence, fold, is_won FROM crm_stage ORDER BY sequence")
    all_stages = env.cr.fetchall()
    
    print(f"\n1. ALL STAGES IN DATABASE ({len(all_stages)} total):")
    for stage in all_stages:
        stage_id, name, sequence, fold, is_won = stage
        print(f"   ID: {stage_id}, Name: {name}, Seq: {sequence}, Fold: {fold}, Won: {is_won}")
    
    # Check visible stages (fold = false)
    env.cr.execute("SELECT id, name, sequence, fold, is_won FROM crm_stage WHERE fold = false ORDER BY sequence")
    visible_stages = env.cr.fetchall()
    
    print(f"\n2. VISIBLE STAGES ({len(visible_stages)} total):")
    for stage in visible_stages:
        stage_id, name, sequence, fold, is_won = stage
        print(f"   ID: {stage_id}, Name: {name}, Seq: {sequence}, Fold: {fold}, Won: {is_won}")
    
    # Check for duplicate names
    env.cr.execute("""
        SELECT name->>'en_US', COUNT(*) as count, array_agg(id) as ids
        FROM crm_stage 
        GROUP BY name->>'en_US' 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    duplicates = env.cr.fetchall()
    
    print(f"\n3. DUPLICATE STAGE NAMES:")
    if duplicates:
        for name, count, ids in duplicates:
            print(f"   '{name}' appears {count} times with IDs: {ids}")
    else:
        print("   No duplicate names found")
    
    # Check leads and their stages
    env.cr.execute("SELECT COUNT(*) FROM crm_lead")
    total_leads = env.cr.fetchone()[0]
    
    env.cr.execute("""
        SELECT s.name->>'en_US', COUNT(l.id) as lead_count
        FROM crm_lead l
        JOIN crm_stage s ON l.stage_id = s.id
        GROUP BY s.name->>'en_US'
        ORDER BY lead_count DESC
    """)
    leads_by_stage = env.cr.fetchall()
    
    print(f"\n4. LEADS BY STAGE (Total leads: {total_leads}):")
    for stage_name, count in leads_by_stage:
        print(f"   '{stage_name}': {count} leads")
    
    # Check leads without stages
    env.cr.execute("SELECT COUNT(*) FROM crm_lead WHERE stage_id IS NULL")
    leads_no_stage = env.cr.fetchone()[0]
    if leads_no_stage > 0:
        print(f"   Leads without stage: {leads_no_stage}")
    
    # Check JSON name format specifically
    print(f"\n5. NAME FORMAT ANALYSIS:")
    env.cr.execute("SELECT id, name FROM crm_stage")
    for stage_id, name in env.cr.fetchall():
        try:
            # Try to parse as JSON
            import json
            parsed = json.loads(name)
            en_name = parsed.get('en_US', 'NOT_FOUND')
            print(f"   ID {stage_id}: JSON format, en_US = '{en_name}'")
        except:
            print(f"   ID {stage_id}: NOT JSON format, raw = '{name}'")
    
    # Check if we have the expected 6 SurePay stages
    expected_stages = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
    env.cr.execute("SELECT name->>'en_US' FROM crm_stage WHERE fold = false")
    actual_stages = [row[0] for row in env.cr.fetchall()]
    
    print(f"\n6. STAGE COMPLETENESS CHECK:")
    print(f"   Expected stages: {expected_stages}")
    print(f"   Actual visible stages: {actual_stages}")
    
    missing = set(expected_stages) - set(actual_stages)
    extra = set(actual_stages) - set(expected_stages)
    
    if missing:
        print(f"   ❌ Missing stages: {missing}")
    if extra:
        print(f"   ❌ Extra stages: {extra}")
    if not missing and not extra:
        print(f"   ✅ All expected stages present!")
    
    print(f"\n=== DIAGNOSIS COMPLETE ===")
