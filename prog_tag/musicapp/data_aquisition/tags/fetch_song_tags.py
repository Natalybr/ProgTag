from sources.last_fm import last_fm_tags_iterator as iterator

for (title, artist), tags in iterator():
    if len(tags)>0:
        S

