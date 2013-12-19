from django.db import models

# Create your models here.

class Tag(models.Model):
    tag_name = models.CharField(max_length = 200)
    
class Song(models.Model):
    
    def __repr__(self):
        return self.song_name
    song_name = models.CharField(max_length=200)
    song_tag = models.ForeignKey(Tag)
