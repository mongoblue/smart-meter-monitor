from django.db import models

class SystemOption(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    value = models.TextField()
    editable = models.BooleanField(default=True)   # 只读标记
    desc = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.key