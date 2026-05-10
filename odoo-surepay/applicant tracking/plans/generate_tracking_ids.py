"""
Run this script from Odoo shell to generate tracking IDs for existing applicants

Usage:
1. Open terminal in Odoo directory
2. Run: python odoo-bin shell -d YOUR_DATABASE_NAME --addons-path=/path/to/addons
3. Copy and paste this code into the shell
"""

# Get all applicants without tracking IDs
applicants = env['hr.applicant'].search([('tracking_id', '=', False)])

print(f"Found {len(applicants)} applicants without tracking IDs")

# Generate tracking IDs
for applicant in applicants:
    tracking_id = applicant._generate_tracking_id()
    applicant.write({'tracking_id': tracking_id})
    print(f"Generated tracking ID {tracking_id} for applicant: {applicant.partner_name or applicant.name}")

print(f"\nSuccessfully generated {len(applicants)} tracking IDs!")

# Verify
applicants_with_tracking = env['hr.applicant'].search([('tracking_id', '!=', False)])
print(f"Total applicants with tracking IDs: {len(applicants_with_tracking)}")
