# HR Recruitment - SurePay Custom Stages

## Overview
This module adds custom recruitment stages tailored to SurePay Ltd's recruitment workflow.

## Features
- **9 Custom Recruitment Stages**:
  1. Application Received
  2. Eligibility Screening
  3. Shortlisting
  4. Committee Review
  5. Interview
  6. Committee Final Review
  7. Offer
  8. Onboarding
  9. Rejected (folded)

- **Status History Integration**: Automatically maps stage changes to status history
- **Proper Sequencing**: Stages are ordered logically in the recruitment pipeline

## Installation

### Prerequisites
- Odoo 17.0
- `hr_recruitment` (Odoo standard module)
- `hr_applicant_tracking_random` (base tracking module)

### Steps
1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install "HR Recruitment - SurePay Custom Stages"

## Usage

### Viewing Stages
1. Go to **Recruitment > Configuration > Stages**
2. You'll see all 9 custom stages

### Using Stages
1. Open any applicant record
2. Use the status bar at the top to move applicants through stages
3. Status history is automatically updated with each stage change

### Stage Mapping
The module maps stages to status history as follows:

| Stage | Status History |
|-------|----------------|
| Application Received | Draft |
| Eligibility Screening | In Progress |
| Shortlisting | In Progress |
| Committee Review | In Progress |
| Interview | Interview |
| Committee Final Review | In Progress |
| Offer | Offer |
| Onboarding | Hired |
| Rejected | Rejected |

## Technical Details

### Models Extended
- `hr.applicant`: Overrides `write()` method to update stage mapping

### Data Files
- `data/hr_recruitment_stage_data.xml`: Creates the 9 custom stages

### Dependencies
```python
'depends': [
    'hr_recruitment',
    'hr_applicant_tracking_random',
]
```

## Configuration
No additional configuration required. Stages are created automatically on module installation.

## Known Issues
None

## Changelog

### Version 1.0.0 (2025-10-19)
- Initial release
- 9 custom recruitment stages
- Status history mapping integration

## Support
For support, contact SurePay Ltd IT Department

## License
LGPL-3

## Author
SurePay Ltd
