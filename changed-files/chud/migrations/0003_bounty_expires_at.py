from datetime import timedelta

from django.db import migrations, models


def backfill(apps, schema_editor):
    Bounty = apps.get_model("chud", "Bounty")
    window = timedelta(days=14)
    for bounty in Bounty.objects.filter(expires_at__isnull=True).iterator():
        bounty.expires_at = bounty.created_at + window
        bounty.save(update_fields=["expires_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("chud", "0002_gift_sender_may_leave"),
    ]

    operations = [
        migrations.AddField(
            model_name="bounty",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
