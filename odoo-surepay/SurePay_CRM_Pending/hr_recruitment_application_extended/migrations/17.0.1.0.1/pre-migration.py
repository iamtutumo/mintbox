# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Pre-migration script to prepare for mail.thread inheritance
    """
    # Check if mail_message table exists (it should if mail module is installed)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'mail_message'
        );
    """)
    
    if cr.fetchone()[0]:
        # Models will inherit mail.thread, so we don't need to do anything special
        # The ORM will handle adding the necessary fields
        pass
