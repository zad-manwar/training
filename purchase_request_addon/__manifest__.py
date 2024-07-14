{
    'name': "Purchase request",
    'auther': "Me",
    'category': "",
    'version': "17.0.0.1.0",
    'depends': ['base','product','mail','purchase'],
    'data': [
        'security/manager_group.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/base_menu.xml',
        'views/purchase_requests_views.xml',
        'wizard/request_change_state_wizard_view.xml'

    ],
    'application': True,

}
