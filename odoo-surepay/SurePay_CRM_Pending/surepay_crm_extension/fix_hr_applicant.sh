#!/bin/bash
# Quick fix for hr.applicant KeyError error

echo "Fixing hr.applicant KeyError error..."

# Run SQL command directly to remove hr.applicant activities
docker-compose exec -T db psql -U odoo -d odoo -c "DELETE FROM mail_activity WHERE res_model = 'hr.applicant';"

echo "Cleanup completed. Please refresh your browser and try accessing the referral form again."
