# HR Recruitment - Onboarding Portal

## Overview
Complete onboarding system for hired candidates with portal access, task management, document upload, and automated employee creation.

## Features
- Onboarding session creation when moved to "Onboarding" stage
- Task checklist with progress tracking
- Document upload portal
- Portal access for candidates
- Automated employee record creation
- Employee number generation
- Contract management integration
- Progress tracking (tasks and documents)

## Models
- `hr.applicant.onboarding`: Main onboarding session
- `onboarding.task`: Task templates
- `onboarding.task.line`: Task instances
- `onboarding.document`: Document requirements

## Portal Access
Candidates access portal via: `/onboarding/<access_token>`

## Installation
Requires: `hr_recruitment`, `hr`, `hr_contract`, `website`, `hr_applicant_tracking_random`, `hr_recruitment_stages_surepay`

## Usage
1. Move applicant to "Onboarding" stage
2. Onboarding session auto-created
3. Invitation email sent with portal link
4. Candidate completes tasks and uploads documents
5. HR verifies documents
6. Click "Create Employee" to generate employee record

**Module 6 Complete** ✅
