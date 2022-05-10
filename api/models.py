from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Task(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=200, default='write content')
    completed = models.BooleanField(default=False,blank=False)

    def __str__(self):
        return self.title