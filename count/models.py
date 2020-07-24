from django.db import models

# Create your models here.
class Count(models.Model):
    DIRECTIONS = [
        ("LR", "Left Right"),
        ("UD", "Up Down")
    ]
    ENTER_DIRECTIONS = [
        ("U", "Up"),
        ("D", "Down"),
        ("L", "Left"),
        ("R", "Right"),
    ]

    name            = models.CharField(max_length=100)
    ip_path         = models.CharField(max_length=50)
    count           = models.PositiveSmallIntegerField(default = 0)
    enterDirection  = models.CharField(max_length=10, choices=ENTER_DIRECTIONS)

    prototxt_path   = models.CharField(max_length=50, default="MobileNetSSD_deploy.prototxt")
    model_path      = models.CharField(max_length=50, default="MobileNetSSD_deploy.caffemodel")
    confidence      = models.DecimalField(max_digits= 4, decimal_places = 4,default = 0.4)
    skip_frames     = models.PositiveSmallIntegerField(default = 30)
    tracking        = models.BooleanField(default=False)
    # live_img        = models.ImageField()

    def __str__(self):
        return self.name