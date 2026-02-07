from django.db import migrations


def normalize_statuses(apps, schema_editor):
    Appointment = apps.get_model("appointments", "Appointment")
    status_map = {
        "CI": "WD",
        "CH_I": "WD",
        "CNC": "CN",
    }

    for old_status, new_status in status_map.items():
        Appointment.objects.filter(status=old_status).update(status=new_status)


class Migration(migrations.Migration):
    dependencies = [
        ("appointments", "0005_careroom_alter_appointment_options_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_statuses, migrations.RunPython.noop),
    ]
