-- Quick Diagnosis of CRM White Page Issue
-- Run this to see what's actually in your database

-- Check 1: Total stages and their visibility
SELECT 
    'Total Stages: ' || COUNT(*) as info
FROM crm_stage
UNION ALL
SELECT 
    'Visible Stages: ' || COUNT(*)
FROM crm_stage WHERE fold = false
UNION ALL
SELECT 
    'Hidden Stages: ' || COUNT(*)
FROM crm_stage WHERE fold = true;

-- Check 2: List all stages with details
SELECT 
    id,
    name->>'en_US' as stage_name,
    sequence,
    CASE WHEN fold = false THEN 'VISIBLE' ELSE 'HIDDEN' END as visibility,
    CASE WHEN is_won = true THEN 'WON' ELSE 'ACTIVE' END as status
FROM crm_stage 
ORDER BY sequence;

-- Check 3: Total leads and their stage status
SELECT 
    'Total Leads: ' || COUNT(*) as info
FROM crm_lead
UNION ALL
SELECT 
    'Leads with NULL stage: ' || COUNT(*)
FROM crm_lead WHERE stage_id IS NULL
UNION ALL
SELECT 
    'Leads with valid stages: ' || COUNT(*)
FROM crm_lead l 
JOIN crm_stage s ON l.stage_id = s.id;

-- Check 4: Leads by stage (if any exist)
SELECT 
    s.name->>'en_US' as stage_name,
    COUNT(l.id) as lead_count
FROM crm_lead l 
JOIN crm_stage s ON l.stage_id = s.id
GROUP BY s.name->>'en_US'
ORDER BY lead_count DESC;

-- Check 5: Check if SurePay stages exist
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Cold Lead') THEN '✅ Cold Lead exists'
        ELSE '❌ Cold Lead missing'
    END as status
UNION ALL
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Prospecting') THEN '✅ Prospecting exists'
        ELSE '❌ Prospecting missing'
    END
UNION ALL
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Preparation') THEN '✅ Preparation exists'
        ELSE '❌ Preparation missing'
    END
UNION ALL
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Closing') THEN '✅ Closing exists'
        ELSE '❌ Closing missing'
    END
UNION ALL
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Won') THEN '✅ Won exists'
        ELSE '❌ Won missing'
    END
UNION ALL
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM crm_stage WHERE name->>'en_US' = 'Lost') THEN '✅ Lost exists'
        ELSE '❌ Lost missing'
    END;
