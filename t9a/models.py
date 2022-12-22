from django.db import models
from django.contrib.auth.models import User


class Deployments(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Secondaries(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Army(models.Model):
    name = models.CharField(max_length=16)
    long_name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Map(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.id}. {self.name}'


class Lists(models.Model):
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    army = models.ForeignKey('Army', null=True, on_delete=models.SET_NULL)
    list = models.TextField()
    name = models.CharField(max_length=256)


class Games(models.Model):
    date = models.DateField()
    map = models.ForeignKey('Map', null=True, on_delete=models.SET_NULL)
    deploy = models.ForeignKey('Deployments', null=True, on_delete=models.SET_NULL)
    secondary = models.ForeignKey('Secondaries', null=True, on_delete=models.SET_NULL)
    turns = models.IntegerField()
    event = models.CharField(max_length=256)
    points_event = models.IntegerField()


class Results(models.Model):
    choice_list = [
        (1, 'winner'),
        (2, 'draw'),
        (3, 'loose')
    ]
    game = models.ForeignKey('Games', null=True, on_delete=models.SET_NULL)
    player = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    secondary = models.IntegerField(choices=choice_list)
    score = models.IntegerField()
    result = models.IntegerField(choices=choice_list)
    list = models.ForeignKey('Lists', null=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True)
    points = models.IntegerField()
    approved = models.BooleanField(null=True)
