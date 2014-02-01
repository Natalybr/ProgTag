#-*- coding: UTF-8 -*-
from django.db import models
import re

class Tag(models.Model):
    name = models.CharField(max_length=100)
    def __repr__(self):
        return self.name
    def __str__(self): return self.__repr__()
    
class DecodingFailedException():
    symbol = None
    def __init__(self, symbol):
        self.symbol = symbol
    def __str__(self):
        return "Could not decode the chord " + str(self.symbol)

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
    #maj7 immediately after the root is a special case, in which the 'm' does not imply a minor chord
    if quality == 'm' and additions and additions[0][0] == 'aj':
        notes[3] = 0
        notes[4] = 1
        additions[0] = 'maj',additions[0][1]
    
    if bass_note:
        bass_index = (note_names[bass_note] - root)%12
        if bass_accidental: bass_index += accidentals[bass_accidental]
        notes[bass_index]=1
    
    
    for modifier,degree in additions:
        if not modifier or (modifier == 'add'): notes[chord_degrees[degree]]=1
        elif modifier in ('+','maj'): notes[chord_degrees[degree] + 1]=1
        else:
            print modifier, degree 
            raise DecodingFailedException(symbol)
    
    return root, tuple(notes)

class Chord(models.Model):
    symbol = models.CharField(max_length = 30)
    root = models.IntegerField()
    notes = models.CharField(max_length=36) #no option to put tuples or similarly complex objects
    
    def __repr__(self):
        return 'chord: ' + self.symbol + ' root=' + str(self.root) + ' notes=' + str(self.notes)
    def __str__(self): return self.__repr__()
    
class Abstract_chord(models.Model):
    """
    only used inside chord progressions, has no data on absolute root and symbol,
    only the modus (through notes) and the difference in root key from previous chord
    in the progression (assuming there is one)
    """
    root_difference = models.IntegerField(null=True)
    notes = models.CharField(max_length = 36)
    def __repr__(self):
        return 'abstract chord: ' + ' root_difference=' + str(self.root_difference) + ' notes=' + str(self.notes)
    def __str__(self): return self.__repr__()

class Chord_progression(models.Model):
    length = models.IntegerField()
    chords = models.ManyToManyField(Abstract_chord, through='Progression_chord_index')
    appearances = models.IntegerField()
    
    def __repr__(self):
        chords = [None]*self.length
        for i in range(self.length):
            pair = Progression_chord_index.objects.get(progression=self, index = i)
            chords[i] = pair.chord
        res = "chord progression: (appearances - " + str(self.appearances) + ")\n"
        for chord in chords:
            res += str(chord) + "\n"
        return res
    def __str__(self):
        return self.__repr__()

    
class Progression_chord_index(models.Model):
    progression = models.ForeignKey(Chord_progression)
    chord = models.ForeignKey(Abstract_chord)
    index = models.IntegerField()
    def __repr__(self):
        return "progression_chord_index: " + str(self.chord) + " index " + str(self.index)
    def __str__(self): return self.__repr__()

           
class Song(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    tags = models.ManyToManyField(Tag)
    chords = models.ManyToManyField(Chord,through='Song_chord_index',null=True)
    previously_failed_chords = models.BooleanField(default = False)
    progressions = models.ManyToManyField(Chord_progression, through='Song_progression_count')
    
    def __repr__(self):
        return "song: " + self.title + "," + self.artist
    def __str__(self): return self.__repr__()

class Song_chord_index(models.Model):
    song = models.ForeignKey(Song)
    chord = models.ForeignKey(Chord)
    index = models.IntegerField()
    
    def __repr__(self):
        return "Song chord index: " + str(self.song) +' '+ str(self.chord) +' '+ str(self.index)
    def __str__(self): return self.__repr__()
    
class Song_progression_count(models.Model):
    song = models.ForeignKey(Song)
    progression = models.ForeignKey(Chord_progression)
    appearance_count = models.IntegerField(default = 0)
    
    
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
    