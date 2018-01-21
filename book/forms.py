from django import forms

from .models import Book, Profile, Term

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'cover', 'genre', 'description', 'language')
