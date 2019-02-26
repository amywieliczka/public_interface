# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-19 22:45


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exhibits', '0003_auto_20170616_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='browseterm',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='exhibit_order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='browsetermgroup',
            name='order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='historical_essay_order',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='exhibititem',
            name='lesson_plan_order',
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
    ]
