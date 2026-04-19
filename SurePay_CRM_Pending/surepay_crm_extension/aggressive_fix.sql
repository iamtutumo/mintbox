-- Aggressive Fix for CRM White Page Issue
-- This will completely reset CRM stages and ensure leads are visible

-- Step 1: Delete ALL existing stages (clean slate)
DELETE FROM crm_stage;

-- Step 2: Create fresh SurePay stages
INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
VALUES 
    ('{"en_US": "Cold Lead"}', 1, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Prospecting"}', 10, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Preparation"}', 20, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Closing"}', 30, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Won"}', 40, false, true, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Lost"}', 50, false, false, NULL, 1, 1, NOW(), NOW());

-- Step 3: Get Cold Lead stage ID
WITH cold_lead_stage AS (
    SELECT id FROM crm_stage WHERE name->>'en_US' = 'Cold Lead' LIMIT 1
)

-- Step 4: Update ALL leads to use Cold Lead stage
UPDATE crm_lead 
SET stage_id = (SELECT id FROM cold_lead_stage)
WHERE stage_id IS NULL OR stage_id NOT IN (SELECT id FROM crm_stage);

-- Step 5: Verify all leads have valid stages
SELECT 
    'Total Leads: ' || COUNT(*) as status
FROM crm_lead
UNION ALL
SELECT 
    'Leads with valid stages: ' || COUNT(*) 
FROM crm_lead l 
JOIN crm_stage s ON l.stage_id = s.id
UNION ALL
SELECT 
    'Visible stages: ' || COUNT(*)
FROM crm_stage 
WHERE fold = false
UNION ALL
SELECT 
    'SurePay stages created: ' || COUNT(*)
FROM crm_stage 
WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');

-- Step 6: Show stage details for verification
SELECT 
    'Stage: ' || (name->>'en_US') || ' (ID: ' || id || ', Fold: ' || fold || ', Visible: ' || CASE WHEN fold = false THEN 'YES' ELSE 'NO' END || ')' as info
FROM crm_stage 
ORDER BY sequence;

-- Fix complete! Refresh your CRM page.
