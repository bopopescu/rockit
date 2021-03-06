from django.db import models


class ModelBase(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        abstract = True
        get_latest_by = 'created'
