-- Quick Fix for CRM White Page Issue
-- Run this in Odoo: Settings > Technical > Database Structure > Execute Query

-- Step 1: Create SurePay stages if they don't exist
INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
VALUES 
    ('{"en_US": "Cold Lead"}', 1, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Prospecting"}', 10, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Preparation"}', 20, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Closing"}', 30, false, false, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Won"}', 40, false, true, NULL, 1, 1, NOW(), NOW()),
    ('{"en_US": "Lost"}', 50, false, false, NULL, 1, 1, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
    sequence = EXCLUDED.sequence,
    fold = false,
    is_won = EXCLUDED.is_won,
    write_date = NOW();

-- Step 2: Get Cold Lead stage ID for reference
WITH cold_lead_stage AS (
    SELECT id FROM crm_stage WHERE name->>'en_US' = 'Cold Lead' LIMIT 1
)

-- Step 3: Fix leads with NULL stage_id
UPDATE crm_lead 
SET stage_id = (SELECT id FROM cold_lead_stage)
WHERE stage_id IS NULL;

-- Step 4: Fix leads with invalid stage references  
UPDATE crm_lead 
SET stage_id = (SELECT id FROM cold_lead_stage)
WHERE stage_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM crm_stage WHERE id = crm_lead.stage_id);

-- Step 5: Archive all non-SurePay stages
UPDATE crm_stage 
SET fold = true 
WHERE name->>'en_US' NOT IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');

-- Step 6: Ensure SurePay stages are visible
UPDATE crm_stage 
SET fold = false 
WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');

-- Step 7: Verify the fix
SELECT 
    'Total Leads: ' || COUNT(*) as info
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
    'SurePay stages: ' || COUNT(*)
FROM crm_stage 
WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');

-- Fix complete! Refresh your CRM page.
