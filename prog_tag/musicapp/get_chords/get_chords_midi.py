
import music21 as m21
import urllib2

BASE_URL = 'http://www.free-midi.org/midi1/'
    
"""
check if the midi exists. if so, download it and convert to a music21 stream.
return song stream (or None).
"""  
def parse_midi(query):
    try:
        req = urllib2.Request(query)
        #check if midi exists
        urllib2.urlopen(req)
        #if exists, parse it into a music21 stream object
        song_stream = m21.converter.parse(query)
        return song_stream
    except:
        return None
    
"""
given (title,artist), downloads midi (if exists), 
and uses music21 lib to chordify the song.
returns a chord vector. 
"""    
def get_chords(title,artist):
    m21.environment.set('autoDownload', 'allow')
    name = artist.lower().replace(' ','_')+ "-"+title.lower().replace(' ','_')+".mid"
    query = BASE_URL+"/"+artist[0]+"/"+name
    
    song_stream = parse_midi(query)
    if song_stream == None: return None

    chords_list = song_stream.chordify()
    chord_vector = []
    for thisChord in chords_list.flat:
        if 'Chord' not in thisChord.classes: # not a chord
            continue
        else:
            chord_vector.append(thisChord)
    print chord_vector
    return chord_vector
        
        
        
        
def test():            
    get_chords('moonshine','bruno mars')

test()



    
    