#-*- coding: UTF-8 -*-
from django.db import models
import re

class Tag(models.Model):
    name = models.CharField()
    def __repr__(self):
        return self.name
    
#old method (replaced by fancy regex
'''def decode(symbol):
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
    qualities = dict((
        ('aug', (1,0,0,0,1,0,0,0,1,0,0,0)),
        ('dim', (1,0,0,1,0,0,1,0,0,0,0,0)),
        ('sus4', (1,0,0,0,0,1,0,1,0,0,0,0)),
        ('sus2', (1,0,1,0,0,0,0,1,0,0,0,0)),
        ('M', (1,0,0,0,1,0,0,1,0,0,0,0)),('major', (1,0,0,0,1,0,0,1,0,0,0,0)),
        ('m', (1,0,0,1,0,0,0,1,0,0,0,0)),('minor', (1,0,0,1,0,0,0,1,0,0,0,0))
    ))
    #map degrees of chord (1-13) to half-tone steps from root (moduli 12)
    chord_degrees = dict(zip(map(str,range(1,14)),(0,2,None,5,7,9,10,2,5,7)))
    #(maj/min)3,8,10 and 12 should not appear explicitly, ever, so are mapped to None
    
    
    #Find bass_inversion and root key. Seperate symbol to key and modus
    bass_inversion = symbol[symbol.find('/') + 1:] if '/' in symbol else None
    chord = symbol[:symbol.find('/')] if bass_inversion else symbol
    root = note_names[chord[0]]
    modus = chord[1:]
    if len(chord) >= 2 and chord[1] in accidentals:
        root += accidentals[chord[1]]
        modus = chord[2:]
        
    #represent all existing notes in chord, by difference from root
    #find the chord quality, if it is explicitly stated. Otherwise choose major
    for quality in qualities:
        if quality in modus:
            notes = list(qualities[quality])
            #don't delete the quality, since M might be used later
    if not 'notes' in locals(): notes = list(qualities['major'])

    if 'M7' in symbol:
        #M7 is an exceptional notation, so the M refers not only to the quality, 
        #but to the seventh type as well (CM7 = Cmaj+7)
        notes[11]=1
        modus = modus.replace('M7','')
    #now it's safe to remove quality symbols
    for quality in qualities:
        if modus.startswith(quality):
            modus = modus[len(quality):]
    #and we can add the bass note (relatively to the root)
    if bass_inversion:
        bass_index = (note_names[bass_inversion[0]] - root)%12
        if len(bass_inversion)>1:
            assert len(bass_inversion) == 2
            bass_index += accidentals[bass_inversion[1]]
        notes[bass_index] = 1
    
    #split to treat each addition separately, with +/maj/add modifiers before them
    for modifier,degree in zip(re.split('\d',modus)[:-1],re.findall('\d',modus)):
        if not modifier or (modifier == 'add'): notes[chord_degrees[degree]]=1
        elif modifier in ('+','maj'): notes[chord_degrees[degree] + 1]=1
        else:
            print modifier, degree 
            raise Exception()
    
    return root, notes'''

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
    if quality == 'M' and additions[0][1] == '7':
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
    root = models.IntegerField
    notes = models.CharField #no option to put tuples or similarly complex objects
    relative_difference = models.IntegerField
        
    def __init__(self, symbol, previous_chord = None):
        """
        create an instance of a chord, given a texual symbol representing it. 
        If another Chord instance is given in previous_chord, store the signed difference 
        between their roots as well.
        """
        self.root, tuple_notes = decode(symbol)
        self.notes = str(tuple_notes)
        if previous_chord: self.relative_difference  = (self.root - previous_chord.root)%12
    
        
class Song(models.Model):
    title = models.CharField()
    artist = models.CharField()
    tags = models.ManyToManyField(Tag)
    chords = models.ManyToManyField(Chord,through='Chord_index')
    
    def __repr__(self):
        return self.title + "," + self.artist

class Chord_index(models.Model):
    song = models.ForeignKey(Song)
    chord = models.ForeignKey(Chord)
    index = models.IntegerField

#class Song_Tag_Pair:
#    song = models.ForeignKey(Song)
#    tag = models.ForeignKey(Tag)
#    def __repr__self(self):
#        return "("+str(self.song)+","+str(self.tag)+")"
    
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
    