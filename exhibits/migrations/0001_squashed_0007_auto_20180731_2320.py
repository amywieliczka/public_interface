# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-21 00:06
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('exhibits', '0001_squashed_0044_auto_20160606_1716'), ('exhibits', '0002_auto_20170614_1855'), ('exhibits', '0003_auto_20170616_2133'), ('exhibits', '0004_auto_20170619_2245'), ('exhibits', '0005_exhibititem_publish'), ('exhibits', '0006_auto_20180731_2143'), ('exhibits', '0007_auto_20180731_2320')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exhibit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ExhibitItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_id', models.CharField(max_length=200)),
                ('exhibit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit')),
                ('essay', models.TextField(blank=True, verbose_name='Item-level exhibit information')),
                ('order', models.IntegerField(blank=True, null=True)),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='T', max_length=1)),
                ('exact', models.BooleanField(default=False)),
                ('lat', models.FloatField(default=37.8086906)),
                ('lon', models.FloatField(default=-122.2675416)),
                ('place', models.CharField(blank=True, max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalEssay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField()),
                ('blockquote', models.CharField(blank=True, max_length=200)),
                ('about_essay', models.TextField(blank=True)),
                ('essay', models.TextField(blank=True)),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1)),
                ('go_further', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LessonPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField()),
                ('essay', models.TextField(blank=True, verbose_name='Lesson plan')),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='NotesItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('order', models.IntegerField(blank=True, null=True)),
                ('essay', models.TextField(blank=True)),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField()),
                ('color', models.CharField(blank=True, max_length=20)),
                ('about_theme', models.TextField(blank=True)),
                ('essay', models.TextField(blank=True, verbose_name='Theme overview')),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1)),
            ],
        ),
        migrations.AddField(
            model_name='exhibit',
            name='byline',
            field=models.TextField(blank=True, help_text='Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication', verbose_name='Credits'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='blockquote',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='overview',
            field=models.TextField(blank=True, verbose_name='Exhibit Overview'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='notesitem',
            name='exhibit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.CreateModel(
            name='HistoricalEssayExhibit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LessonPlanExhibit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ThemeExhibit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='exhibit',
            name='publish',
            field=models.BooleanField(default=False, verbose_name='Ready for publication?'),
        ),
        migrations.AlterField(
            model_name='notesitem',
            name='essay',
            field=models.TextField(blank=True, verbose_name='Note'),
        ),
        migrations.AlterField(
            model_name='notesitem',
            name='render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='T', max_length=1),
        ),
        migrations.AddField(
            model_name='themeexhibit',
            name='exhibit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AddField(
            model_name='themeexhibit',
            name='theme',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Theme'),
        ),
        migrations.AddField(
            model_name='lessonplanexhibit',
            name='exhibit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AddField(
            model_name='lessonplanexhibit',
            name='lessonPlan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.LessonPlan'),
        ),
        migrations.AddField(
            model_name='historicalessayexhibit',
            name='exhibit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AddField(
            model_name='historicalessayexhibit',
            name='historicalEssay',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.HistoricalEssay'),
        ),
        migrations.RenameField(
            model_name='themeexhibit',
            old_name='position',
            new_name='order',
        ),
        migrations.AlterUniqueTogether(
            name='themeexhibit',
            unique_together=set([('exhibit', 'theme')]),
        ),
        migrations.RenameField(
            model_name='lessonplanexhibit',
            old_name='position',
            new_name='order',
        ),
        migrations.AlterUniqueTogether(
            name='lessonplanexhibit',
            unique_together=set([('exhibit', 'lessonPlan')]),
        ),
        migrations.RenameField(
            model_name='historicalessayexhibit',
            old_name='position',
            new_name='order',
        ),
        migrations.AlterUniqueTogether(
            name='historicalessayexhibit',
            unique_together=set([('exhibit', 'historicalEssay')]),
        ),
        migrations.RenameModel(
            old_name='ThemeExhibit',
            new_name='ExhibitTheme',
        ),
        migrations.CreateModel(
            name='HistoricalEssayTheme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(blank=True, null=True)),
                ('historicalEssay', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.HistoricalEssay')),
                ('theme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Theme')),
            ],
            options={
                'verbose_name': 'Historical Essay',
            },
        ),
        migrations.CreateModel(
            name='LessonPlanTheme',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(blank=True, null=True)),
                ('lessonPlan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.LessonPlan')),
                ('theme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.Theme')),
            ],
            options={
                'verbose_name': 'Lesson Plan',
            },
        ),
        migrations.AlterModelOptions(
            name='exhibittheme',
            options={'verbose_name': 'Exhibit'},
        ),
        migrations.AlterModelOptions(
            name='historicalessayexhibit',
            options={'ordering': ['order'], 'verbose_name': 'Historical Essay'},
        ),
        migrations.AlterModelOptions(
            name='lessonplanexhibit',
            options={'ordering': ['order'], 'verbose_name': 'Lesson Plan'},
        ),
        migrations.AlterUniqueTogether(
            name='lessonplantheme',
            unique_together=set([('lessonPlan', 'theme')]),
        ),
        migrations.AlterUniqueTogether(
            name='historicalessaytheme',
            unique_together=set([('historicalEssay', 'theme')]),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='meta_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='meta_keywords',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='meta_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='meta_keywords',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='publish',
            field=models.BooleanField(default=False, verbose_name='Ready for publication?'),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='meta_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='meta_keywords',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='publish',
            field=models.BooleanField(default=False, verbose_name='Ready for publication?'),
        ),
        migrations.AddField(
            model_name='theme',
            name='meta_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='theme',
            name='meta_keywords',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='theme',
            name='publish',
            field=models.BooleanField(default=False, verbose_name='Ready for publication?'),
        ),
        migrations.AlterField(
            model_name='exhibit',
            name='title',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='historicalessay',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='lessonplan',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='theme',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='hero',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Hero Image'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='color',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='theme',
            name='hero',
            field=models.ImageField(blank=True, upload_to='uploads/', verbose_name='Hero Image'),
        ),
        migrations.CreateModel(
            name='BrowseTerm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('linkText', models.CharField(max_length=200)),
                ('linkLocation', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='BrowseTermGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(blank=True, null=True)),
                ('theme', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Theme')),
                ('group_note', models.TextField(blank=True)),
                ('group_title', models.CharField(blank=True, max_length=200)),
                ('render_as', models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1)),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='browseterm',
            name='browse_term_group',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='exhibits.BrowseTermGroup'),
        ),
        migrations.AddField(
            model_name='browseterm',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RenameField(
            model_name='browseterm',
            old_name='linkLocation',
            new_name='link_location',
        ),
        migrations.RenameField(
            model_name='browseterm',
            old_name='linkText',
            new_name='link_text',
        ),
        migrations.AlterModelOptions(
            name='browseterm',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='exhibit',
            name='scraped_from',
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.RemoveField(
            model_name='lessonplan',
            name='essay',
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='lesson_plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.LessonPlan'),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='byline',
            field=models.TextField(blank=True, help_text='Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication', verbose_name='Credits'),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='grade_level',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='lesson_plan',
            field=models.CharField(blank=True, max_length=255, verbose_name='Lesson Plan File URL'),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='overview',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='sub_title',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='exhibit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='lesson_plan_order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='byline_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1, verbose_name='Render credits as'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='short_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='hero',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Hero Image'),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='alternate_lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Alternate Lockup Image'),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='item_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Lockup Image'),
        ),
        migrations.RenameField(
            model_name='historicalessay',
            old_name='about_essay',
            new_name='byline',
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='byline_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1, verbose_name='Render credits as'),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='go_further_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1, verbose_name='Render as'),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='color',
            field=models.CharField(blank=True, help_text='Please provide color in <code>#xxx</code>, <code>#xxxxxx</code>, <code>rgb(xxx,xxx,xxx)</code>, or <code>rgba(xxx,xxx,xxx,x.x)</code> formats.', max_length=20),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='alternate_lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Alternate Lockup Image'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='item_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Lockup Image'),
        ),
        migrations.AlterModelOptions(
            name='historicalessaytheme',
            options={'ordering': ['order'], 'verbose_name': 'Historical Essay'},
        ),
        migrations.AlterModelOptions(
            name='lessonplantheme',
            options={'ordering': ['order'], 'verbose_name': 'Lesson Plan'},
        ),
        migrations.RenameField(
            model_name='theme',
            old_name='about_theme',
            new_name='byline',
        ),
        migrations.AddField(
            model_name='theme',
            name='alternate_lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Alternate Lockup Image'),
        ),
        migrations.AddField(
            model_name='theme',
            name='byline_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1, verbose_name='Render credits as'),
        ),
        migrations.AddField(
            model_name='theme',
            name='item_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='theme',
            name='lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Lockup Image'),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='byline_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='H', max_length=1, verbose_name='Render credits as'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='historical_essay',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.HistoricalEssay'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='historical_essay_order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='custom_crop',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/custom_item_crop/'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='custom_link',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='lessonPlan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.LessonPlan'),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='exhibit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='exhibit',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='lessonPlan',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='exhibits.LessonPlan'),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='notesitem',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='browsetermgroup',
            name='exhibit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Exhibit'),
        ),
        migrations.AddField(
            model_name='browsetermgroup',
            name='exhibit_order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exhibits.Theme'),
        ),
        migrations.AddField(
            model_name='theme',
            name='category',
            field=models.CharField(blank=True, choices=[('cal-history', 'California History'), ('cal-cultures', 'California Cultures'), ('jarda', 'JARDA')], max_length=20),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='hero_first',
            field=models.BooleanField(default=False, verbose_name='Use hero for lockups?'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='custom_title',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='hero_first',
            field=models.BooleanField(default=False, verbose_name='Use hero for lockups?'),
        ),
        migrations.AddField(
            model_name='theme',
            name='hero_first',
            field=models.BooleanField(default=False, verbose_name='Use hero for lockups?'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='custom_metadata',
            field=models.TextField(blank=True, verbose_name='Custom metadata'),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='metadata_render_as',
            field=models.CharField(choices=[('H', 'HTML'), ('T', 'Plain Text'), ('M', 'Markdown')], default='M', max_length=1),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='item_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='lockup_derivative',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/', verbose_name='Lockup Image'),
        ),
        migrations.AddField(
            model_name='theme',
            name='sort_title',
            field=models.CharField(blank=True, max_length=200, verbose_name='Sortable Title'),
        ),
        migrations.AlterField(
            model_name='browseterm',
            name='browse_term_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exhibits.BrowseTermGroup'),
        ),
        migrations.AlterField(
            model_name='browseterm',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='exhibittheme',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='historicalessayexhibit',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='historicalessaytheme',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='lessonplantheme',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='notesitem',
            name='order',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='exhibittheme',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='historicalessayexhibit',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='historicalessaytheme',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='lessonplantheme',
            name='order',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='browseterm',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='exhibittheme',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalessayexhibit',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalessaytheme',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lessonplanexhibit',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='lessonplantheme',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notesitem',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='exhibititem',
            name='publish',
            field=models.BooleanField(default=True, verbose_name='Ready for publication?'),
        ),
        migrations.AddField(
            model_name='exhibit',
            name='copyright_holder',
            field=models.TextField(default='Regents of the University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exhibit',
            name='copyright_year',
            field=models.IntegerField(default='2011'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exhibit',
            name='curator',
            field=models.TextField(default='University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='copyright_holder',
            field=models.TextField(default='Regents of the University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='copyright_year',
            field=models.IntegerField(default='2011'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalessay',
            name='curator',
            field=models.TextField(default='University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='copyright_holder',
            field=models.TextField(default='Regents of the University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='copyright_year',
            field=models.IntegerField(default='2011'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lessonplan',
            name='curator',
            field=models.TextField(default='University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='theme',
            name='copyright_holder',
            field=models.TextField(default='Regents of the University of California'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='theme',
            name='copyright_year',
            field=models.IntegerField(default='2011'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='theme',
            name='curator',
            field=models.TextField(default='University of California'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='historicalessay',
            name='byline',
            field=models.TextField(blank=True, help_text='Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication', verbose_name='Credits'),
        ),
        migrations.AlterField(
            model_name='theme',
            name='byline',
            field=models.TextField(blank=True, help_text='Curator name(s) and titles, Any other collaborators, Institutional affiliation, Date of publication', verbose_name='Credits'),
        ),
    ]
