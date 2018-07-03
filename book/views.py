from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.template import RequestContext
from django.db import models
from django.db.models import Q
import datetime
from .forms import BookForm, CommentForm
from .models import Profile, Term, Book, User, Comment
#from .tasks import recommendBooks, updateTerms
from .semantics import commentSemantics
#import semantic
from django.http import HttpResponseRedirect

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def home(request):
    profile = Profile.objects.get(user=request.user)
    recBooks = list(profile.recommendedBooks.all())
    # remove already read books from recBooks
    allBooksuser1 = list(profile.likedBooks.all())
    allBooksuser1.extend(list(profile.dislikedBooks.all()))
    if allBooksuser1:
        for book in allBooksuser1:
            if book in recBooks:
                recBooks.remove(book)
    booksQuerry=Book.objects.all()
    query = request.GET.get("search")
    if query:
        booksQuerry=booksQuerry.filter(Q(title__icontains=query) | Q(author__icontains=query)).distinct()
    books=list(booksQuerry)
    books.sort(key=lambda x: x.title)
    return render(request, 'book/home.html', {'profile': profile, 'recBooks': recBooks[0:6], 'books': books})

def book_detail(request, idb):
    book = get_object_or_404(Book, id=idb)
    read = False
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES or None, instance=book)
        comment = request.POST.get('comment')
        if comment:
            sentiment = commentSemantics.classify(comment)
            now = datetime.datetime.now().strftime("%Y-%m-%d at %H:%M")
            newComment = Comment(comment = comment,book = book, user=request.user.username, semantics=sentiment, date=str(now))
            newComment.save()
            if sentiment=='0':
                sentiment= int(-1)
            user = request.user.profile
            user.updateTerms(book.author, float(sentiment)*0.8) #run by celery
            user.updateTerms(book.genre, float(sentiment)*1.0) #run by celery
            user.updateTerms(book.language, float(sentiment)*0.2) #run by celery
            if sentiment==1:
                user.likedBooks.add(book)
            else:
                user.dislikedBooks.add(book)
            user.recommendBooks()
            return redirect('book_detail', idb)
    else:
        form = BookForm(instance=book)
    allBooksuser1 = list(request.user.profile.likedBooks.all())
    allBooksuser1.extend(list(request.user.profile.dislikedBooks.all()))
    comments = list(Comment.objects.filter(book=book))
    if allBooksuser1:
        read = book in allBooksuser1
    return render(request, 'book/book_detail.html', {'form': form, 'book': book, 'read': read, 'comments':comments})
