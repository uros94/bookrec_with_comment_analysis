from django import forms

from .models import Book, Profile, Term, Comment

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'cover', 'genre', 'description', 'language')

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment',)
