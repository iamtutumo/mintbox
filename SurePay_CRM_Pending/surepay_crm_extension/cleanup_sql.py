#!/usr/bin/env python3
"""
Direct SQL cleanup script to remove hr.applicant activities.
This provides an immediate fix for the KeyError: 'hr.applicant' error.
"""

import psycopg2
import sys

def cleanup_hr_applicant_sql():
    """Clean up hr.applicant activities using direct SQL"""
    
    # Database connection parameters - adjust as needed
    db_params = {
        'dbname': 'odoo',
        'user': 'odoo',
        'password': 'odoo',
        'host': 'db',  # Docker service name
        'port': '5432'
    }
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check for hr.applicant activities
        cursor.execute("SELECT COUNT(*) FROM mail_activity WHERE res_model = 'hr.applicant'")
        count = cursor.fetchone()[0]
        
        print(f"Found {count} activities for hr.applicant model")
        
        if count > 0:
            # Delete the activities
            cursor.execute("DELETE FROM mail_activity WHERE res_model = 'hr.applicant'")
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"Successfully deleted {deleted_count} activities")
        else:
            print("No hr.applicant activities found")
        
        # Also check for any other potentially problematic activities
        cursor.execute("""
            SELECT DISTINCT res_model, COUNT(*) 
            FROM mail_activity 
            GROUP BY res_model 
            ORDER BY COUNT(*) DESC
        """)
        
        models = cursor.fetchall()
        print("\nCurrent activity models:")
        for model, count in models:
            print(f"  {model}: {count} activities")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    success = cleanup_hr_applicant_sql()
    if success:
        print("Cleanup completed successfully")
    else:
        print("Cleanup failed")
        sys.exit(1)
