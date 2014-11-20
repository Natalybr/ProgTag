HarmoniTag
======

A system for tagging songs based on their [chord progressions](http://en.wikipedia.org/wiki/Chord_progression).

Overview
--------

HarmoniTag is a project and pipeline aimed at for tagging songs, utilizing machine learning to infer genres by the appearances of chord progressions. Its first iteration was made as part of a CS workshop for B.Sc. It is currently under work, to refine the methods use for scientific publication.
The data used is taken from the [Million Song Dataset's Last.fm dataset](http://labrosa.ee.columbia.edu/millionsong/lastfm), and various chord websites (such as chordie.com and ultimate-guitar.com).

The GitHub repository mostly contains code for:
1. A Django ORM database structure for storing song/tag/chord-progression data (database itself not included in the repository).
2. Populating the database with song-tag data from the Last.fm dataset. 
3. Populating the database with song-chord data by querying and parsing relevant websites.
4. Performing feature selection, training and testing various models of machine learning on the data.
