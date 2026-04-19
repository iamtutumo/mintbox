{
    'name': 'SurePay Client Visits',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Track client visits with location data',
    'description': """
        This module allows tracking of client visits with:
        - Visit details and purpose
        - Location tracking with OpenStreetMap
        - Integration with CRM leads and partners
    """,
    'author': 'SurePay',
    'website': 'https://www.surepay.com',
    'depends': [
        'crm',
        'base_geolocalize',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/client_visit_views.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_web': [
            'surepay_client_visits/static/src/js/client_visit.js',
            'surepay_client_visits/static/src/js/visit_map.js',
            'surepay_client_visits/static/src/js/visit_map_embed.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
