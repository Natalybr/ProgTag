import time
from django.db import transaction

def time_elapsed_minutes(start_time):
    return str(((time.time() - start_time)//6)/10) + ' minutes.'

@transaction.commit_manually
def delete_queryset(queryset):
    """since sqlite doesn't allow batch deletions of more than 999 objects with foreign-key pointing at them, 
    this method divides the job to 999 sized pieces (and minimizes number of db queries for it)"""
    for i in range(len(queryset)):
        queryset[i].delete()
        if not (i+1)%999: transaction.commit()
    transaction.commit()
        