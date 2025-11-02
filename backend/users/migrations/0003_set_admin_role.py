# Generated manually to set ADMIN role for existing superusers
from django.db import migrations


def set_admin_role_for_superusers(apps, schema_editor):
    """Set role='ADMIN' for all existing superusers"""
    User = apps.get_model('users', 'User')
    User.objects.filter(is_superuser=True).update(role='ADMIN')
    # Also set staff users to STAFF role if they're not superuser
    User.objects.filter(is_staff=True, is_superuser=False).update(role='STAFF')


def reverse_set_role(apps, schema_editor):
    """Reverse migration - set role back to CUSTOMER"""
    User = apps.get_model('users', 'User')
    User.objects.filter(role__in=['ADMIN', 'STAFF']).update(role='CUSTOMER')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_options_user_role'),
    ]

    operations = [
        migrations.RunPython(set_admin_role_for_superusers, reverse_set_role),
    ]

