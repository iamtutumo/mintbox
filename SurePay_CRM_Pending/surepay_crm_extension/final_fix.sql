-- FINAL COMPREHENSIVE FIX FOR CRM WHITE PAGE ISSUE
-- This addresses all potential causes

-- Step 1: Clear all existing stages completely
DELETE FROM crm_stage;

-- Step 2: Create fresh SurePay stages with proper visibility
INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
VALUES 
    ('{"en_US": "Cold Lead"}', 1, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Prospecting"}', 10, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Preparation"}', 20, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Closing"}', 30, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Won"}', 40, false, true, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Lost"}', 50, false, false, NULL, 1, 1, NOW(), NOW());

-- Step 3: Fix ALL leads - ensure they all have valid stage references
-- First, set all leads with NULL stages to Cold Lead
UPDATE crm_lead 
SET stage_id = (SELECT id FROM crm_stage WHERE name->>'en_US' = 'Cold Lead' LIMIT 1)
WHERE stage_id IS NULL;

-- Then, fix any leads with invalid stage references (stage_id that doesn't exist)
UPDATE crm_lead 
SET stage_id = (SELECT id FROM crm_stage WHERE name->>'en_US' = 'Cold Lead' LIMIT 1)
WHERE stage_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM crm_stage WHERE id = crm_lead.stage_id
);

-- Step 4: Ensure all SurePay stages are visible
UPDATE crm_stage 
SET fold = false 
WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');

-- Step 5: Verification - show results
SELECT '=== FIX RESULTS ===' as status;

SELECT 
    'Total Stages Created: ' || COUNT(*) as info
FROM crm_stage;

SELECT 
    'Visible Stages: ' || COUNT(*) as info
FROM crm_stage WHERE fold = false;

SELECT 
    'Total Leads: ' || COUNT(*) as info
FROM crm_lead;

SELECT 
    'Leads with Valid Stages: ' || COUNT(*) as info
FROM crm_lead l 
JOIN crm_stage s ON l.stage_id = s.id;

SELECT 
    'Leads in Each Stage:' as info
UNION ALL
SELECT 
    s.name->>'en_US' || ': ' || COUNT(l.id) || ' leads'
FROM crm_lead l 
JOIN crm_stage s ON l.stage_id = s.id
GROUP BY s.name->>'en_US'
ORDER BY s.sequence;

SELECT '=== FIX COMPLETE ===' as status;
SELECT 'Refresh your browser and check CRM page' as next_step;
