from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0001_initial'),
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResearchReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('ticker', models.CharField(db_index=True, max_length=20)),
                ('company_name', models.CharField(max_length=255)),
                ('report_title', models.CharField(max_length=255)),
                ('report_type', models.CharField(default='institutional_equity_research', max_length=64)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('private_file_path', models.CharField(blank=True, max_length=500, null=True)),
                ('page_count', models.PositiveIntegerField(default=1)),
                ('page_limit', models.PositiveIntegerField(default=50)),
                ('generation_date', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('execution_time_seconds', models.FloatField(blank=True, null=True)),
                ('error_details', models.TextField(blank=True, null=True)),
                ('conviction_rating', models.CharField(blank=True, max_length=100, null=True)),
                ('principles_pass_rate_pct', models.FloatField(blank=True, null=True)),
                ('principles_passed_count', models.PositiveSmallIntegerField(default=0)),
                ('principles_total_count', models.PositiveSmallIntegerField(default=0)),
                ('research_snapshot', models.JSONField(default=dict, help_text='Reproducible snapshot of all quantitative & qualitative inputs')),
                ('markdown_content', models.TextField(blank=True, null=True)),
                ('html_content', models.TextField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='companies.company')),
                ('user', models.ForeignKey(help_text='Authenticated user who requested and owns this report', on_delete=django.db.models.deletion.CASCADE, related_name='research_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'company_research_reports',
                'ordering': ['-generation_date'],
            },
        ),
        migrations.CreateModel(
            name='ReportSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_number', models.PositiveSmallIntegerField(help_text='1 to 15')),
                ('section_key', models.CharField(db_index=True, max_length=64)),
                ('title', models.CharField(max_length=255)),
                ('page_count', models.PositiveSmallIntegerField(default=1)),
                ('content_markdown', models.TextField(blank=True, default='')),
                ('structured_data', models.JSONField(default=dict)),
                ('has_qualitative_evidence', models.BooleanField(default=False)),
                ('citations', models.JSONField(default=list)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='api.researchreport')),
            ],
            options={
                'db_table': 'report_sections',
                'ordering': ['report', 'section_number'],
            },
        ),
        migrations.AddIndex(
            model_name='researchreport',
            index=models.Index(fields=['user', '-generation_date'], name='company_res_user_id_c28c89_idx'),
        ),
        migrations.AddIndex(
            model_name='researchreport',
            index=models.Index(fields=['ticker', '-generation_date'], name='company_res_ticker_58c2be_idx'),
        ),
        migrations.AddIndex(
            model_name='researchreport',
            index=models.Index(fields=['report_id'], name='company_res_report__006ee7_idx'),
        ),
        migrations.AddConstraint(
            model_name='reportsection',
            constraint=models.UniqueConstraint(fields=('report', 'section_number'), name='unique_report_section_num'),
        ),
    ]
