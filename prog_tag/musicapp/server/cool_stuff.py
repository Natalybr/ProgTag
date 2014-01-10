from django.http import HttpResponse
from musicapp.models import *

def foo(request):
    response = HttpResponse("Here is some text!")
    response.write("</br> haha!")

    return response