from django.db import models
import re

# Create your models here.

"""
Database format -

First table contains only songs.
S
"""

class Tag(models.Model):
    name = models.CharField()
    def __repr__(self):
        return self.name
    
class Chord(models.Model):
    root = models.CharField()
    QUALITIES = (
        ('aug', 'augmented'),
        ('dim', 'diminished')
        ('sus4', 'suspended second')
        ('sus2', 'suspended fourth')
        ('M', 'major'),
        ('m', 'minor'),
    )
    ADDITIONS = (
        ('2','add2/dom9'),
        ('4','add4/dom11'),
        ('6','add6/dom13'),
        ('7','dom7'),
        ('+7','major 7'),
    )
    root = models.CharField(max_length=60)
    quality = models.CharField(choices = QUALITIES)
    additions = models.ManyToManyField(to, db_constraint)
    
    def decode(symbol):
        """
        decodes a textual symbol representing a chord to provide a
        (root, quality, additions) tuple. Decoding rules roughly taken from -
        http://en.wikipedia.org/wiki/Chord_names_and_symbols_(popular_music)#Rules_to_decode_chord_names_and_symbols
        """
        symbol = symbol[:symbol.find('/')]#ignore bass instructions/inversions
        root = symbol[0]
        modus = symbol[1:]
        if symbol[1] in ('b','♭','#','♯','♮'):
            modus = symbol[2:]
            if symbol[1] in ('b','♭'): root += 'b'
            if symbol[1] in ('#','♯'): root += '#'
        
        quality = None
        for known_quality in (x[0] for x in QUALITIES):
            if known_quality in symbol:
                quality = known_quality
                modus = modus.replace(quality,'')
                break #we rely on 'dim' being listed before 'm' on the list
        if not quality: quality = 'M' #major is default if not specified
        
        additions = []
        if 'M7' in symbol:
            #M7 is exceptional, so the M refers not only to the quality, but the seventh
            additions.add('+7')
            modus = modus.replace('M7','')
        #split to treat each addition separately 
        for modifier,degree in zip(re.split('\d',modus)[:-1],re.findall('\d',modus)):
            #currently logic is simple - only 7 is allowed a modifier - maj
            if degree == '7' and modifier == 'maj': additions.add('+7')
            elif modifier: raise Exception('Chord not reconisable: \n' + symbol)
            if(int(degree) > 7): degree = str(int(degree)%7)
        
        return root, quality, additions
        
    
    def __init__(symbol, previous_chord = None):
        """
        create an instance of a chord, given a texual symbol representing it, with the 
        decoding rules defined in       
        If another Chord instance is given in previous_chord, store the signed difference 
        between their roots as well.
        """
        
    
    
class Song(models.Model):
    title = models.CharField()
    artist = models.CharField()
    tags = models.ManyToManyField(Tag)
    chords = models.ManyToManyField(Chord)
    def __repr__(self):
        return self.title + "," + self.artist

#class Song_Tag_Pair:
#    song = models.ForeignKey(Song)
#    tag = models.ForeignKey(Tag)
#    def __repr__self(self):
#        return "("+str(self.song)+","+str(self.tag)+")"
    
    