# Generated by Django 2.2.12 on 2020-05-19 20:16

from django.db import migrations

def populate_project_organizations(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Organization = apps.get_model('organizations', 'Organization')

    # assignment of existing projects to orgs based on project name based on
    # discussions w/ Matt Spencer (2020-05-20)
    org_project_mapping = {
        '18F': ['18F', 'TTS Acq'],
        'CoE': ['CoE'],
        'cloud.gov': ['cloud.gov'],
        'Login.gov': ['Login.gov'],
        'OA': ['TTS OA'],
        'PIF': ['PIF']
    }

    for org_name in org_project_mapping.keys():
        try:
            org = Organization.objects.get(name=org_name)

            for project_name_start in org_project_mapping[org_name]:
                Project.objects.filter(name__istartswith=project_name_start).update(organization=org)
        except:
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_auto_20200303_1821'),
        ('organizations', '0006_unit_initial_data')
    ]

    operations = [
        migrations.RunPython(populate_project_organizations),
    ]
