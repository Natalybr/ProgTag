import csv
from musicapp.models import * 
from django.core import management
from musicapp.data_aquisition.chords.fetch_song import get_chords
from musicapp.data_aquisition.data_usher import acquire_song_chords
from musicapp.data_processing.create_chord_progressions_from_database import create_song_progressions

#management.call_command('syncdb', verbosity=0, interactive=False)
#management.call_command('flush', verbosity=0, interactive=False)
#management.call_command('loaddata','C:\\Users\\arielbro\\Downloads\\db.json',verbosity=0, interactive=False)

#songs = [0]*5
#songs[0] = Song.objects.create(title='come together', artist='beatles')
#songs[1] = Song.objects.create(title='let it be', artist='beatles')
#songs[2] = Song.objects.create(artist='leonard cohen',title='halleluja')
#songs[3] = Song.objects.create(title='smells like teen spirit', artist='nirvana')
#songs[4] = Song.objects.create(artist='charlie parker', title='blues for alice')
##songs[5] = Song.objects.create(title='i\'m yours', artist='jason marz')
#
#for song in songs:
#    acquire_song_chords(song.title, song.artist)
###res = MyList.objects.filter(items__name='1', ownership__order=1).filter(items__name='2', ownership__order=2)
#
#for song in Song.objects.all():
#    create_song_progressions(song, 3, 5)
#    
#for progression in Chord_progression.objects.filter(appearances__gte=5):
#    print progression
#    
#    