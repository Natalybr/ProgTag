#-*- coding: UTF-8 -*-
from django.db import models
import re

class Tag(models.Model):
    name = models.CharField(max_length=100)
    def __repr__(self):
        return self.name

def decode(symbol):
    """
    decodes a textual symbol representing a chord to provide a
    (root, notes) tuple. Decoding rules roughly taken from -
    http://en.wikipedia.org/wiki/Chord_names_and_symbols_(popular_music)#Rules_to_decode_chord_names_and_symbols
    """    
    #represent root key as numbers between 0 and 11. 
    note_names = dict((('A',0),('B',2),('C',3),('D',5),('E',7),('F',8),('G',10)))
    accidentals = dict((
        ('b',-1),('♭',-1),
        ('#',1),('♯',1),
        ('♮',0)
    ))
    #represent qualities as ordered set of notes, with half tone steps, and represent 
    #those by a binary appearance vector (of length 12). 
    if "qualities" not in decode.__dict__: #static variable for efficiency
        qualities = dict((
            ('aug', (1,0,0,0,1,0,0,0,1,0,0,0)),
            ('dim', (1,0,0,1,0,0,1,0,0,0,0,0)),
            ('sus4', (1,0,0,0,0,1,0,1,0,0,0,0)),
            ('sus2', (1,0,1,0,0,0,0,1,0,0,0,0)),
            ('M', (1,0,0,0,1,0,0,1,0,0,0,0)),('major', (1,0,0,0,1,0,0,1,0,0,0,0)),
            ('m', (1,0,0,1,0,0,0,1,0,0,0,0)),('minor', (1,0,0,1,0,0,0,1,0,0,0,0))
        ))
    #map degrees of chord (1-13) to half-tone steps from root (moduli 12)
    #(maj/min)3,8,10 and 12 should not appear explicitly, ever, so are mapped to None
    if "chord_degrees" not in decode.__dict__: 
        chord_degrees = dict(zip(map(str,range(1,14)),(0,2,None,5,7,9,10,2,5,7)))
    if "chord_regex" not in decode.__dict__:
        chord_regex = \
            "([A-G])([#b])?(M|m|Major|Minor|major|minor|aug|dim|sus4|sus2)?([^/]*)(/([A-G])([#b])?)?"
        
    root, accidental , quality, additions, _, bass_note, bass_accidental  = \
        re.match(chord_regex, symbol).groups()
    additions = [(addition[:-1],addition[-1]) \
                 for addition in re.findall("(\D*\d)", additions)]
    
    root = note_names[root] if not accidental else note_names[root] + accidentals[accidental]  
    notes = list(qualities[quality]) if quality else list(qualities['major'])
    #M7 is a special notation, noting the 7'th is a major one, besides denoting quality.
    if quality == 'M' and additions and additions[0][1] == '7':
        notes[11]=1
        additions = additions[1:]
    
    if bass_note:
        bass_index = (note_names[bass_note] - root)%12
        if bass_accidental: bass_index += accidentals[bass_accidental]
        notes[bass_index]=1
    
    
    for modifier,degree in additions:
        if not modifier or (modifier == 'add'): notes[chord_degrees[degree]]=1
        elif modifier in ('+','maj'): notes[chord_degrees[degree] + 1]=1
        else:
            print modifier, degree 
            raise Exception()
    
    return root, tuple(notes)

class Chord(models.Model):
    root = models.IntegerField()
    notes = models.CharField(max_length=36) #no option to put tuples or similarly complex objects
    relative_difference = models.IntegerField(null=True)
    previously_failed_chords = models.BooleanField(default = False)
    original = models.CharField(max_length=30) #the original representation of the chord scraped
        
    '''overriding __init__ disturbes django methods
    def __init__(self, symbol, previous_chord = None):
        """
        create an instance of a chord, given a texual symbol representing it. 
        If another Chord instance is given in previous_chord, store the signed difference 
        between their roots as well.
        """
        self.root, tuple_notes = decode(symbol)
        self.notes = str(tuple_notes)
        if previous_chord: self.relative_difference  = (self.root - previous_chord.root)%12
    '''
           
class Song(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag)
    chords = models.ManyToManyField(Chord,through='Chord_index',null=True)
    
    def __repr__(self):
        return "{"+self.title + ", " + self.artist+"}"

class Chord_index(models.Model):
    song = models.ForeignKey(Song)
    chord = models.ForeignKey(Chord)
    index = models.IntegerField()
    
def test():
    chord1 = "C"
    chord2 = "Am"
    chord3 = "G#/F#"
    chord4 = "Edimadd46"
    chord5 = "C#sus2maj7/Gb"
    
    assert decode(chord1) == (3, (1,0,0,0,1,0,0,1,0,0,0,0))
    assert decode(chord2) == (0, (1,0,0,1,0,0,0,1,0,0,0,0))
    assert decode(chord3) == (11, (1,0,0,0,1,0,0,1,0,0,1,0))
    assert decode(chord4) == (7, (1,0,0,1,0,1,1,0,0,1,0,0))
    assert decode(chord5) == (4, (1,0,1,0,0,1,0,1,0,0,0,1))
    