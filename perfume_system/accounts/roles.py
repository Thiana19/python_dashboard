from rolepermissions.roles import AbstractUserRole

class RAndD(AbstractUserRole):
    available_permissions = {
        'access_formulations': True,
        'access_compliance': True,
        'access_inventory': True,
    }

class QA(AbstractUserRole):
    available_permissions = {
        'access_qa_dashboard': True,
        'access_formulations': True,
    }

class Manager(AbstractUserRole):
    available_permissions = {
        'access_dashboard': True,
        'access_reports': True,
        'access_inventory_summary': True,
    }