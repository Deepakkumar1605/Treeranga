from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import threading
import time

def request_deletion(user):
    user.deletion_requested = True
    user.deletion_date = timezone.now() + timedelta(days=30)  # Set deletion date to 30 days from now
    user.save()
    
    # Schedule account deletion after 30 days (2592000 seconds)
    threading.Thread(target=delete_user_after_delay, args=(user.pk,)).start()

def cancel_deletion(user):
    user.deletion_requested = False
    user.deletion_date = None
    user.save()

def delete_user_after_delay(user_pk):
    User = get_user_model()
    user = User.objects.get(pk=user_pk)
    
    # Calculate the time to wait before deletion (time until deletion_date)
    time_to_wait = (user.deletion_date - timezone.now()).total_seconds()
    
    # Delay until the deletion date is reached
    time.sleep(max(time_to_wait, 0))  # Ensure no negative sleep time
    
    # Check if deletion is still requested
    if user.deletion_requested:
        user.delete()






