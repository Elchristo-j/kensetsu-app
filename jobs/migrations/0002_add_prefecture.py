from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'), # 前の設計図の名前に合わせます
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='prefecture',
            field=models.CharField(default='未設定', max_length=10, verbose_name='都道府県'),
        ),
    ]