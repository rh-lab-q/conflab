from django.db import models

class Room(models.Model):
    s_name = models.CharField(max_length=20)
    name = models.CharField(max_length=256)
    desc = models.TextField()
    color = models.ChaarField(max_length=8)
    #conf = models.ForeignKey(Confs)
