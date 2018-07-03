from django.contrib import admin
from .models import Term, Profile, Book, Comment

admin.site.register(Term)
admin.site.register(Book)
admin.site.register(Comment)
admin.site.register(Profile)
