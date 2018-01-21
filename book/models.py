from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
import math

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=30, blank=True)
    ##intrest vector is acctually represented as list of terms related to some Profile
    likedBooks = models.ManyToManyField(
        "Book",
        null=True,
        blank=True,
        default = None,
        related_name='likedBy'
    )
    dislikedBooks = models.ManyToManyField(
        "Book",
        null=True,
        blank=True,
        default = None,
        related_name='dislikedBy'
    )
    recommendedBooks = models.ManyToManyField(
        "Book",
        null=True,
        blank=True,
        default = None,
        related_name='recommendedTo'
    )
    similarUsers = models.ManyToManyField(
        to='self',
        null=True,
        blank=True,
        default = None,
        related_name='similarTo',
        symmetrical=False
    )

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        terms = Term.objects.select_related().filter(user = self)
        return "Name : "+ self.user.username + "\t(terms: "+str(list(terms))+")"#+ "\t(similarUsers: "+str(users)+")"

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=60)
    genre_list =  (
    #ovo je naopako - zameni
        ('Classic','Classic'),
        ('Fiction','Fiction'),
        ('Romance','Romance'),
        ('History','History'),
        ('Drama','Drama'),
        ('Politics','Politics'),
        ('Thriler','Thriler'),
        ('Poetry','Poetry'),
    )
    genre = models.CharField(max_length=20, choices=genre_list)
    cover = models.FileField(null=True, blank=True)
    description = models.TextField()
    language = models.CharField(max_length=30)

    def __str__(self):
        return self.title+" by "+self.author

class Term(models.Model):
    term = models.CharField(max_length=60)
    value = models.FloatField()
    user = models.ForeignKey(Profile, related_name='terms')

    def get_terms(self):
        return ', '.join(self.terms_set.values_list('name', flat=True))

    def __str__(self):
        return self.term+": "+str(self.value)
