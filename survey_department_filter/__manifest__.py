{
    'name': 'Survey Department Filter',
    'version': '16.0.1.0.0',
    'summary': 'Restrict survey responses to user\'s department',
    'category': 'Tools',
    'author': 'HyperIT Consultants',
    'depends': ['survey', 'hr'],
    'data': [
        'security/survey_user_input_rules.xml',
        'views/survey_user_input.xml',
        'views/survey_views.xml',
    ],
    'installable': True,
}
