from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from django.db.models import Q
from .forms import BookForm
from .models import Profile, Term, Book, User
from .tasks import recommendBooks, updateTerms
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
    books=Book.objects.all()

    query = request.GET.get("search")
    if query:
        books=books.filter(Q(title__icontains=query) | Q(author__icontains=query)).distinct()
    return render(request, 'book/home.html', {'profile': profile, 'recBooks': recBooks[0:6], 'books': books})


def book_detail(request, idb):
    book = get_object_or_404(Book, id=idb)
    read = False
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES or None, instance=book)
    else:
        form = BookForm(instance=book)
    allBooksuser1 = list(request.user.profile.likedBooks.all())
    allBooksuser1.extend(list(request.user.profile.dislikedBooks.all()))
    if allBooksuser1:
        read = book in allBooksuser1
    return render(request, 'book/book_detail.html', {'form': form, 'book': book, 'read': read})

def book_like(request, idb):
    object = get_object_or_404(Book, id=idb)
    updateTerms.delay(request.user.profile,object.author, 0.8) #run by celery
    updateTerms.delay(request.user.profile,object.genre, 1.0) #run by celery
    updateTerms.delay(request.user.profile,object.language, 0.2) #run by celery
    request.user.profile.likedBooks.add(object)
    recommendBooks.delay(request.user.profile) #run by celery
    return redirect('home')

def book_dislike(request, idb):
    object = get_object_or_404(Book, id=idb)
    updateTerms.delay(request.user.profile,object.author, -0.8) #run by celery
    updateTerms.delay(request.user.profile,object.genre, -1.0) #run by celery
    updateTerms.delay(request.user.profile,object.language, -0.2) #run by celery
    request.user.profile.dislikedBooks.add(object)
    recommendBooks.delay(request.user.profile) #run by celery
    return redirect('home')
