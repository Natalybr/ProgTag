from django.contrib import admin

# Register your models here.

def test():
    print "hi"

class GetMIDI(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['question']}),
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    
test()