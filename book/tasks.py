import string
import math
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from .models import Profile, Term, Book

### NAPOMENA: svaki put kad menjas nesto, prekini izvrsavanje Celery, pa pokreni opet da bi prepoznao izmene!!!
from celery import shared_task

##### recommendation
@shared_task
def recommendBooks(user1):
    print("\nrecomendation start!!!")
    booksColl = recommendBooksColl(user1)
    print("\ncollaborative: "+ str(booksColl))
    booksCont = recommendBooksCont(user1)
    print("\ncontent: "+ str(booksCont))
    rec = []
    ### OVO RADI SAMO CESTO JE PRESEK PRAZAN SKUP, TAKO DA SAM ZAKOMENTARISAO
    ##intersect
    """for b1 in booksColl:
        if b1 in booksCont:
            rec.append(b1)"""
    ##if intersection is not empty list
    """if rec:
        return rec"""
    ##if it is empty than use union
    rec = booksCont
    for b2 in booksColl:
        if rec.count(b2)==0:
            rec.append(b2)
    user1.recommendedBooks.clear()
    #add new ones
    for book in rec:
        user1.recommendedBooks.add(book)
    print("\nreccomended: "+ str(rec))
    return rec

##### content filtering
@shared_task
def updateTerms(user1, term, newValue):
    termOld = Term.objects.filter(user=user1)#ovde moze da se upotrebi Q biblioteka
    termOld = termOld.filter(term=term)
    if(termOld):
        termOld[0].value = termOld[0].value+newValue
        termOld[0].save()
    else:
        termNew = Term(term = term,value = newValue,user = user1)
        termNew.save()
    return

def recommendBooksCont(user1):
    topTerms = list(Term.objects.filter(user=user1))
    topTerms.sort(key=lambda x: x.value, reverse=True)
    #note that I have used only top 4 terms
    topTerms = topTerms[0:4]
    allBooks = list(Book.objects.all())
    """ moved to views.home"""
    allBooksuser1 = list(user1.likedBooks.all())
    allBooksuser1.extend(list(user1.dislikedBooks.all()))
    if allBooksuser1:
        for book in allBooksuser1:
            allBooks.remove(book)
    recBooks = []
    for term in topTerms:
        for book in allBooks:
            if(book.author==term.term or book.genre==term.term or book.language==term.term):
                recBooks.append(book)
                allBooks.remove(book)
    return recBooks

##### collaborative filtering
def recommendBooksColl(user1):
    updateSimilarUsers(user1)
    recBooks = []
    for user in list(user1.similarUsers.all()):
        recBooks.extend(list(user.likedBooks.all()))
    for book in recBooks:
        if recBooks.count(book)>1:
            recBooks.remove(book)
    """ moved to views.home"""
    allBooksuser1 = list(user1.likedBooks.all())
    allBooksuser1.extend(list(user1.dislikedBooks.all()))
    if allBooksuser1:
        for book in allBooksuser1:
            if book in recBooks:
                recBooks.remove(book)
    return recBooks

def updateSimilarUsers(user1):#this could also be used asyc
    allUsers = Profile.objects.all()
    #first element is value of pearson coef and second is user
    similarity = [[]*2 for i in range(len(allUsers)-1)]
    i=0
    for u in allUsers:
        if(u != user1):
            commonTermsValues=commonTerms(user1, u)
            pc = pearsonCoef(commonTermsValues[0],commonTermsValues[1])
            similarity[i].append(pc)
            similarity[i].append(u)
            i=i+1
    similarity.sort(key=lambda x: x[0], reverse=True)
    #remove old similarities
    user1.similarUsers.clear()
    #add new ones -- note that I have used only top 4 most similar users
    for newSimilarUser in similarity[0:4]:
        user1.similarUsers.add(newSimilarUser[1])
    return

#find common terms and return two lists of values of those terms for both user1 and otherUser
def commonTerms(user1,otherProfile):
    terms1stUser = Term.objects.filter(user=user1)
    terms2ndUser = Term.objects.filter(user=otherProfile)
    #first list is for values of sefl and second for term values of otherUser
    commonTermsValues = [[]*(len(terms1stUser)) for i in range(2)]
    for t1 in terms1stUser:
        for t2 in terms2ndUser:
            if(t1.term==t2.term):
                commonTermsValues[0].append(t1.value)
                commonTermsValues[1].append(t2.value)
    return commonTermsValues

def pearsonCoef(termsValues1st, termsValues2nd):
    if(len(termsValues1st) != len(termsValues2nd)):
        return -1
    if(len(termsValues1st)==0):
        return 0
    sum1 = sum(termsValues1st)
    sum2 = sum(termsValues2nd)
    avg1=sum1/len(termsValues1st)
    avg1 = [avg1] * len(termsValues1st)
    avg2=sum2/len(termsValues2nd)
    avg2 = [avg2] * len(termsValues2nd)
    sqrSum1 = sum(map(lambda el,avg: (el-avg)**2, termsValues1st, avg1))
    sqrSum2 =  sum(map(lambda el,avg: (el-avg)**2, termsValues2nd, avg2))
    complexSum = sum(map(lambda el1,avg1,el2,avg2: (el1-avg1)*(el2-avg2), termsValues1st, avg1, termsValues2nd, avg2))
    if math.sqrt(sqrSum1*sqrSum2) == 0:
        return 0
    coef = complexSum / math.sqrt(sqrSum1*sqrSum2)
    return coef
