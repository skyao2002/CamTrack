from .people_counter import PeopleCounter
from .models import Count
from CamTrack import settings

def newTrack(name):
    obj = Count.objects.get(name=name)
    try:
        home_counter = PeopleCounter(threadID=obj.id, name=obj.name,prototxt=settings.MODELS + obj.prototxt_path, 
            model=settings.MODELS + obj.model_path, 
            input=obj.ip_path, 
            output=None,
            confidence=obj.confidence, 
            skip_frames=obj.skip_frames, 
            enter_direction=obj.enterDirection
        )
    except ValueError as e:
        print(e)
    except Exception as e:
        print("An unknown error occurred opening the video streams. ")
        print(e)
    
    try:
        home_counter.start()
    except Exception as e:
        print(e,'The camera likely did not connect')
    # objects = Count.objects.all()

    # for obj in objects:

