import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Credentials',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_key', models.CharField(max_length=255)),
                ('secret_key', models.CharField(max_length=255)),
                ('storage', models.CharField(choices=[('S3', 'S3'), ('Azure', 'Azure'), ('GC', 'Gc'), ('Custom', 'Custom')], max_length=10)),
            ],
        ),
        migrations.CreateModel(

            name='EmailVerification',
            fields=[
                ('email', models.EmailField(default='default@example.com', max_length=255, primary_key=True, serialize=False)),
                ('verification_code', models.CharField(max_length=6, null=True)),
                ('token_time_to_live', models.DateTimeField(null=True)),
                ('tries_left', models.IntegerField(default=3)),
            ],
            options={
                'verbose_name': 'Email Verification',
                'verbose_name_plural': 'Email Verifications',
            },
        ),
        migrations.CreateModel(

            name='FileReference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file_name', models.CharField(max_length=255)),
                ('url', models.URLField(max_length=500)),

                ('storage_provider', models.CharField(choices=[('AWS', 'Aws'), ('S3', 'S3'), ('GoogleDrive', 'Google Drive'), ('LocalStorage', 'Local')], default='LocalStorage', max_length=20)),
                ('size', models.PositiveBigIntegerField()),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('upload_status', models.CharField(choices=[('Complete', 'Complete'), ('Pending', 'Pending'), ('Failed', 'Failed'), ('Processing', 'Processing')], default='Pending', max_length=20)),
                ('file_type', models.CharField(choices=[('EventFile', 'Event File'), ('PredictionFile', 'Prediction File')], default='EventFile', max_length=20)),

                ('storage_provider', models.IntegerField(choices=[(1, 'AWS'), (2, 'S3'), (3, 'Google Drive'), (4, 'Local Storage')], default=4)),
                ('size', models.PositiveBigIntegerField()),
                ('upload_date', models.DateTimeField(auto_now_add=True)),
                ('upload_status', models.IntegerField(choices=[(1, 'Complete'), (2, 'Pending'), (3, 'Failed'), (4, 'Processing')], default=2)),
                ('file_type', models.IntegerField(choices=[(1, 'Event File'), (2, 'Prediction File')], default=1)),

                ('is_selected', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the user', primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),

                ('is_active', models.BooleanField(default=False)),

                ('valid_account', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('rating', models.FloatField(default=0.0)),
                ('num_of_usages', models.IntegerField(default=0)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),

                ('token_time_to_live', models.DateTimeField(blank=True, null=True)),
                ('verification_code', models.CharField(blank=True, max_length=6, null=True)),

                ('is_password_reset_pending', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(blank=True, related_name='core_user_groups', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='core_user_permissions', to='auth.permission')),
            ],
        ),
        migrations.CreateModel(
            name='EventSystem',
            fields=[
                ('name', models.CharField(max_length=255)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),

                ('status', models.CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active', max_length=8)),

                ('status', models.IntegerField(choices=[(1, 'Active'), (2, 'Inactive')], default=1)),

                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_updated_at', models.DateTimeField(auto_now=True)),
                ('users', models.ManyToManyField(related_name='event_systems_user', to=settings.AUTH_USER_MODEL)),
                ('file_objects', models.ManyToManyField(related_name='event_systems', to='core.filereference')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='event_systems',
            field=models.ManyToManyField(related_name='associated_users', to='core.eventsystem'),
        ),
        migrations.CreateModel(
            name='UserToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField()),
                ('refresh_token', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserSystemPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission_level', models.IntegerField(choices=[(1, 'Viewer'), (2, 'Editor'), (3, 'Admin'), (4, 'Owner')], default=1)),
                ('event_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.eventsystem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'event_system')},
            },
        ),
    ]
