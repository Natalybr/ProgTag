from django.http import HttpResponse
from musicapp.models import *

def foo(request):
    
    x = Song()
    x.song_name = 'a'
    y = Tag()
    y.tag_name = 'hello'
    y.save()
    x.song_tag = y
    x.save()
    
    
    
    response = HttpResponse("Here is some text!")
    response.write("</br> haha!")

    return response