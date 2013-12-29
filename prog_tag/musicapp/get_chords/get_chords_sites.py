from bs4 import BeautifulSoup
from urllib2 import urlopen

BASE_URL = "http://www.ultimate-guitar.com/"
 
def make_soup(url):
    html = urlopen(url).read()
    return BeautifulSoup(html, "lxml")

def get_rating(chords):
    return int(chords[2].span.span["class"][0][2])

def get_raters(chords):
    return int(chords[2].text[2:-2])

def get_url(chords):
    return chords[1].a["href"]

def choose_best_chords(by_rate, by_raters):
    last = len(by_rate)-1
    if get_raters(by_rate[last]) >= (get_raters(by_raters[last])/2):
        return get_url(by_rate[last])
    if get_rating(by_raters[last]) >= (get_rating(by_rate[last])-1):
        return get_url(by_raters[last])
    else: 
        return get_url(by_rate[last])
        
"""
get the result page in ultimate-guitar with all the results for the given (artist, title), 
parse the results page. each result has a url, type rating and raters. 
filter by type and get only chords (remove tabs, bass, ukulele etc.). 
then sort by rating and raters and choose best chords based on those parameters. 
finally, return the url of best chords to parse
"""         
def get_best_chords(all_url):
    soup = make_soup(all_url)
    all_results = soup.find("table", "tresults")
    all_chords = []
    #filter all non-chords out
    for stripe in all_results.findAll("tr"):
        stripe_params = [td for td in stripe.findAll("td")]
        if len(stripe_params) == 0: continue
        if stripe_params[3].text == 'chords': all_chords.append(stripe_params)
    #find highest rated chords  
    by_rate = sorted(all_chords, key=lambda chord: get_rating(chord))
    by_raters = sorted(all_chords, key=lambda chord: get_raters(chord))
    return choose_best_chords(by_rate, by_raters)

"""
given a url of best chords, parses the page and returns a chord vector which contains
the ordered sequence of the songs' chords. 
(currently includes noise: if the chords are prsented before the song, they are added to the vector, 
if they are repeated by a special sign, they are not added, and so on)
"""
def get_chord_vector(chords_url):
    soup = make_soup(chords_url)
    song_text = soup.findAll("pre")[2]
    chord_vector = [str(chord.text) for chord in song_text.findAll('span')]
    return chord_vector


"""
given (artist, title), finds best chords, scrapes chord vector
"""
def get_chords(title,artist):
    name = (artist+"+"+title).replace(' ','+')
    all_chords_url = (BASE_URL + "search.php?search_type=title&value="+name)
    best_chords_url = get_best_chords(all_chords_url)
    chord_vector = get_chord_vector(best_chords_url)
    print chord_vector
    return chord_vector
    
    
    
def test():
    get_chords("society", "eddie vedder") 



