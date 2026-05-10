#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify CRM stage configuration and detect duplicates.
This script can be run to check if the duplicate stages issue has been resolved.
"""

def test_crm_stages(env):
    """Test CRM stage configuration and report any issues."""
    print("=== CRM Stage Configuration Test ===\n")
    
    # Get all stages
    env.cr.execute("SELECT id, name, sequence, fold, is_won FROM crm_stage ORDER BY sequence")
    all_stages = env.cr.fetchall()
    print(f"Total stages in database: {len(all_stages)}")
    
    # Get visible stages (fold = false)
    env.cr.execute("SELECT id, name, sequence, fold, is_won FROM crm_stage WHERE fold = false ORDER BY sequence")
    visible_stages = env.cr.fetchall()
    print(f"Visible stages (fold = false): {len(visible_stages)}")
    
    # Get hidden stages (fold = true)
    env.cr.execute("SELECT id, name, sequence, fold, is_won FROM crm_stage WHERE fold = true ORDER BY sequence")
    hidden_stages = env.cr.fetchall()
    print(f"Hidden stages (fold = true): {len(hidden_stages)}")
    
    print("\n=== Visible Stages ===")
    for stage in visible_stages:
        stage_id, name, sequence, fold, is_won = stage
        print(f"ID: {stage_id}, Name: {name}, Sequence: {sequence}, Won: {is_won}")
    
    print("\n=== Hidden Stages ===")
    for stage in hidden_stages:
        stage_id, name, sequence, fold, is_won = stage
        print(f"ID: {stage_id}, Name: {name}, Sequence: {sequence}, Won: {is_won}")
    
    # Check for duplicates
    print("\n=== Duplicate Detection ===")
    env.cr.execute("""
        SELECT name->>'en_US', COUNT(*) as count 
        FROM crm_stage 
        GROUP BY name->>'en_US' 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)
    duplicates = env.cr.fetchall()
    
    if duplicates:
        print("❌ DUPLICATE STAGES FOUND:")
        for name, count in duplicates:
            print(f"  - '{name}' appears {count} times")
    else:
        print("✅ No duplicate stages found")
    
    # Check for expected SurePay stages
    expected_stages = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
    print(f"\n=== Expected SurePay Stages Check ===")
    
    env.cr.execute("SELECT name->>'en_US' FROM crm_stage WHERE fold = false")
    visible_stage_names = [row[0] for row in env.cr.fetchall()]
    
    missing_stages = []
    extra_stages = []
    
    for stage in expected_stages:
        if stage not in visible_stage_names:
            missing_stages.append(stage)
    
    for stage in visible_stage_names:
        if stage not in expected_stages:
            extra_stages.append(stage)
    
    if missing_stages:
        print(f"❌ Missing expected stages: {missing_stages}")
    else:
        print("✅ All expected SurePay stages are present")
    
    if extra_stages:
        print(f"❌ Unexpected stages found: {extra_stages}")
    else:
        print("✅ No unexpected stages found")
    
    # Check stage sequences
    print(f"\n=== Stage Sequence Check ===")
    expected_sequences = {
        'Cold Lead': 1,
        'Prospecting': 10,
        'Preparation': 20,
        'Closing': 30,
        'Won': 40,
        'Lost': 50
    }
    
    sequence_issues = []
    for stage in visible_stages:
        stage_id, name, sequence, fold, is_won = stage
        stage_name = name.split('"en_US": "')[1].split('"')[0] if '"en_US": "' in name else name
        
        if stage_name in expected_sequences:
            expected_seq = expected_sequences[stage_name]
            if sequence != expected_seq:
                sequence_issues.append(f"{stage_name}: expected {expected_seq}, got {sequence}")
    
    if sequence_issues:
        print("❌ Sequence issues found:")
        for issue in sequence_issues:
            print(f"  - {issue}")
    else:
        print("✅ All stages have correct sequences")
    
    # Overall result
    print(f"\n=== OVERALL RESULT ===")
    if (len(visible_stages) == 6 and 
        not duplicates and 
        not missing_stages and 
        not extra_stages and 
        not sequence_issues):
        print("✅ CRM STAGE CONFIGURATION IS CORRECT")
        return True
    else:
        print("❌ CRM STAGE CONFIGURATION HAS ISSUES")
        return False

if __name__ == "__main__":
    # This script is designed to be run within Odoo environment
    # Use: env['surepay.crm.extension'].test_crm_stages(env)
    print("This script should be called from within Odoo environment.")
    print("Usage: env['surepay.crm.extension'].test_crm_stages(env)")
