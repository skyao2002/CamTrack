from .models import Count
from CamTrack import settings
from .tasks import track
from time import sleep

def newTrack(name):
    obj = Count.objects.get(name=name)
    message = track.delay(name=obj.name,
        input=obj.ip_path, 
        output=None,
        confidence=float(obj.confidence), 
        skip_frames=obj.skip_frames, 
        enter_direction=obj.enterDirection
    )
    sleep(3.5)
    if message.status != 'SUCCESS':
        return "Successfully started tracking!"
    else:
        return message.get()
    
    # objects = Count.objects.all()

    # for obj in objects:

