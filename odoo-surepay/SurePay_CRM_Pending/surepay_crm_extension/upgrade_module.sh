#!/bin/bash
# Script to upgrade the SurePay CRM Extension module from terminal

echo "Upgrading SurePay CRM Extension module..."

# Update the module list
echo "Updating module list..."
docker-compose exec -T odoo bash -c "odoo -d odoo --stop-after-init --update=all" || {
    echo "Failed to update module list. Trying alternative approach..."
}

# Alternative approach: Update only our specific module
echo "Upgrading SurePay CRM Extension module..."
docker-compose exec -T odoo bash -c "odoo -d odoo --stop-after-init --update=surepay_crm_extension" || {
    echo "Failed to upgrade module. Trying database approach..."
}

# If the above fails, try direct database approach
echo "Checking if module needs database update..."
docker-compose exec -T db psql -U odoo -d odoo -c "
    UPDATE ir_module_module 
    SET state = 'to upgrade' 
    WHERE name = 'surepay_crm_extension';
"

echo "Module marked for upgrade. Please restart Odoo and the upgrade should complete automatically."
echo ""
echo "To complete the upgrade:"
echo "1. Restart Odoo: docker-compose restart odoo"
echo "2. Wait a few minutes for the upgrade to complete"
echo "3. Clear browser cache and refresh"
echo "4. Access referral form: http://localhost:8060/referral/form"
