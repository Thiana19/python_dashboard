from rolepermissions.roles import AbstractUserRole

class RAndD(AbstractUserRole):
    role_name = 'r_and_d'  
    available_permissions = {
        'access_formulations': True,
        'access_compliance': True,
        'access_inventory': True,
    }

class QA(AbstractUserRole):
    role_name = 'qa'
    available_permissions = {
        'access_dashboard': True,
        'access_qa': True,
        'access_formulations': True,
    }

class Manager(AbstractUserRole):
    role_name = 'manager'
    available_permissions = {
        'access_dashboard': True,
        'access_reports': True,
        'access_inventory_summary': True,
    }
