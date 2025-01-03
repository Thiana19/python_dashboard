from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from rolepermissions.roles import assign_role, clear_roles
from rolepermissions.permissions import grant_permission

class Command(BaseCommand):
    help = 'Create users, assign roles, groups, and permissions'

    def handle(self, *args, **kwargs):
        users_data = [
            {
                'username': 'rd_user',
                'email': 'rd_user@example.com',
                'password': 'rd123456',
                'role': 'r_and_d',
                'group_name': 'R&D Group',
                'permissions': ['access_formulations', 'access_compliance', 'access_inventory'],
            },
            {
                'username': 'qa_user',
                'email': 'qa_user@example.com',
                'password': 'qa123456',
                'role': 'qa',
                'group_name': 'QA Group',
                'permissions': ['access_dashboard', 'access_qa', 'access_formulations'],
            },
            {
                'username': 'manager_user',
                'email': 'manager_user@example.com',
                'password': 'manager123456',
                'role': 'manager',
                'group_name': 'Manager Group',
                'permissions': ['access_dashboard', 'access_reports', 'access_inventory_summary'],
            },
        ]

        for user_data in users_data:
            # Create user if it doesn't exist
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_staff': True,
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f"Created user {user.username}")
            else:
                self.stdout.write(f"User {user.username} already exists")

            # Create or fetch group
            group, _ = Group.objects.get_or_create(name=user_data['group_name'])

            # Clear existing groups and roles
            user.groups.clear()
            clear_roles(user)

            # Assign group and role
            user.groups.add(group)
            assign_role(user, user_data['role'])
            self.stdout.write(f"Assigned {user_data['role']} role and group '{user_data['group_name']}' to {user.username}")

            # Grant permissions to the user
            for perm in user_data['permissions']:
                grant_permission(user, perm)
                self.stdout.write(f"Granted permission '{perm}' to {user.username}")

        self.stdout.write(self.style.SUCCESS("Users, roles, groups, and permissions updated successfully!"))
