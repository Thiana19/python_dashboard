from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rolepermissions.roles import assign_role

class Command(BaseCommand):
    help = 'Verify and fix user roles'

    def handle(self, *args, **kwargs):
        # Create groups if they don't exist
        rd_group, _ = Group.objects.get_or_create(name='r_and_d')
        qa_group, _ = Group.objects.get_or_create(name='qa')
        manager_group, _ = Group.objects.get_or_create(name='manager')

        # R&D User
        try:
            rd_user = User.objects.get(username='rd_user')
            rd_user.groups.clear()  # Clear existing groups
            rd_user.groups.add(rd_group)  # Add to R&D group
            assign_role(rd_user, 'r_and_d')
            self.stdout.write(f"Assigned R&D role and group to {rd_user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('rd_user not found'))

        # QA User
        try:
            qa_user = User.objects.get(username='qa_user')
            qa_user.groups.clear()
            qa_user.groups.add(qa_group)
            assign_role(qa_user, 'qa')
            self.stdout.write(f"Assigned QA role and group to {qa_user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('qa_user not found'))

        # Manager User
        try:
            manager_user = User.objects.get(username='manager_user')
            manager_user.groups.clear()
            manager_user.groups.add(manager_group)
            assign_role(manager_user, 'manager')
            self.stdout.write(f"Assigned Manager role and group to {manager_user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('manager_user not found'))