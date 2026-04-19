from odoo import api, fields, models

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_default = fields.Boolean(string='Is Default', default=False)

    @api.model
    def _default_surepay_stage_ids(self):
        """Return default SurePay stage IDs.
        
        This includes:
        - Renamed default stages: Cold Lead (from New), Prospecting (from Qualified), Preparation (from Proposition)
        - New custom stages: Closing, Won, Lost
        """
        stage_names = ['Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost']
        stages = self.search([('name', 'in', stage_names)])
        return stages.ids
    
    @api.model
    def cleanup_duplicate_stages(self):
        """Manual cleanup method to remove duplicate CRM stages.
        
        This method can be called manually to fix duplicate stage issues.
        Returns: True if cleanup was successful, False otherwise.
        """
        try:
            # Archive ALL existing stages first
            self.env.cr.execute("UPDATE crm_stage SET fold = true")
            print("Archived all existing stages")
            
            # Define our 6 SurePay stages
            surepay_stages = [
                ('Cold Lead', 1, False, False),
                ('Prospecting', 10, False, False),
                ('Preparation', 20, False, False),
                ('Closing', 30, False, False),
                ('Won', 40, False, True),
                ('Lost', 50, False, False),
            ]
            
            # Create/update each stage
            for stage_name, sequence, fold, is_won in surepay_stages:
                # Check if stage already exists
                self.env.cr.execute("SELECT id FROM crm_stage WHERE name->>'en_US' = %s", (stage_name,))
                existing_stage = self.env.cr.fetchone()
                
                if existing_stage:
                    # Update existing stage
                    stage_id = existing_stage[0]
                    self.env.cr.execute("""
                        UPDATE crm_stage 
                        SET name = %s, sequence = %s, fold = %s, is_won = %s, write_date = NOW()
                        WHERE id = %s
                    """, (f'{{"en_US": "{stage_name}"}}', sequence, fold, is_won, stage_id))
                    print(f"Updated existing stage: {stage_name}")
                else:
                    # Create new stage
                    self.env.cr.execute("""
                        INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, %s, %s, NULL, 1, 1, NOW(), NOW())
                    """, (f'{{"en_US": "{stage_name}"}}', sequence, fold, is_won))
                    print(f"Created new stage: {stage_name}")
            
            # Final cleanup: Archive any duplicate SurePay stages
            self.env.cr.execute("""
                UPDATE crm_stage SET fold = true
                WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')
                AND id NOT IN (
                    SELECT MIN(id) 
                    FROM crm_stage 
                    WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')
                    GROUP BY name->>'en_US'
                )
            """)
            print("Cleaned up duplicate SurePay stages")
            
            # Ensure our 6 SurePay stages are visible and properly sequenced
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 1 WHERE name->>'en_US' = 'Cold Lead'")
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 10 WHERE name->>'en_US' = 'Prospecting'")
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 20 WHERE name->>'en_US' = 'Preparation'")
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 30 WHERE name->>'en_US' = 'Closing'")
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 40 WHERE name->>'en_US' = 'Won'")
            self.env.cr.execute("UPDATE crm_stage SET fold = false, sequence = 50 WHERE name->>'en_US' = 'Lost'")
            print("Ensured SurePay stages are visible and properly sequenced")
            
            # Show final result
            self.env.cr.execute("SELECT COUNT(*) FROM crm_stage WHERE fold = false")
            visible_count = self.env.cr.fetchone()[0]
            self.env.cr.execute("SELECT name, sequence FROM crm_stage WHERE fold = false ORDER BY sequence")
            final_stages = self.env.cr.fetchall()
            print(f"Final visible stages count: {visible_count}")
            print("Final visible stages:", final_stages)
            
            return True
            
        except Exception as e:
            print(f"Error during stage cleanup: {str(e)}")
            return False
