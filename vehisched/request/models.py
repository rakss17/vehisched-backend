from django.db import models
from accounts.models import User
from vehicle.models import Vehicle
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Type(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, choices=[
        ('Round Trip', 'Round Trip'),
        ('One-way - Drop', 'One-way - Drop'),
        ('One-way - Fetch', 'One-way - Fetch'),
    ])
    
    def __str__(self):
        return self.name

class Vehicle_Driver_Status(models.Model):
    vehicle_driver_status_id = models.AutoField(primary_key=True)
    driver_id = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    plate_number = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, choices=[
        ('Available', 'Available'),
        ('Reserved - Assigned', 'Reserved - Assigned'),
        ('On Trip', 'On Trip'),
        ('Unavailable', 'Unavailable'),
    ])

class Request(models.Model):
    request_id = models.AutoField(primary_key=True)
    requester_name = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='requester_requests')
    travel_date = models.DateField(null=True, blank=True)
    travel_time = models.TimeField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    office = models.CharField(max_length=255, null=True, blank=True)
    number_of_passenger = models.IntegerField(null=True, blank=True)
    passenger_name = models.TextField(null=True, blank=True, help_text="List of passenger names in JSON format")
    purpose = models.CharField(max_length=1000, null=True, blank=True)
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_capacity = models.IntegerField(null=True, blank=True)
    merged_with = models.TextField(null=True, blank=True)
    date_reserved = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    driver_name = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_requests')
    type = models.ForeignKey(
        Type, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_driver_status_id = models.OneToOneField(
        Vehicle_Driver_Status, on_delete=models.SET_NULL, null=True, blank=True)
    main_merge = models.BooleanField(default=False)
    status = models.CharField(max_length=255, choices=[
        ('Approved', 'Approved'),
        ('Approved - Alterate Vehicle', 'Approved - Alterate Vehicle'),
        ('Pending', 'Pending'),
        ('Canceled', 'Canceled'),
        ('Rescheduled', 'Rescheduled'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
        ('Awaiting Vehicle Alteration', 'Awaiting Vehicle Alteration'),
        ('Awaiting Rescheduling', 'Awaiting Rescheduling'),
        ('Ongoing Vehicle Maintenance', 'Ongoing Vehicle Maintenance'),
        ('Driver Absence', 'Driver Absence'),
    ], null=True, blank=True)
    from_vip_alteration = models.BooleanField(default=False)
    

    def __str__(self):
        return self.purpose or 'No Purpose'


class Question(models.Model):
    question_number = models.CharField(max_length=100, primary_key=True, default=None)
    question = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.question_number


class Answer(models.Model):
    request = models.ForeignKey(Request, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    suggestions = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.answer
    

@receiver(post_migrate)
def create_travel_types(sender, **kwargs):
    if sender.name == 'request':

        travel_types = ['Round Trip', 'One-way - Drop', 'One-way - Fetch']

        if not Type.objects.filter(name__in=travel_types).exists():
            for name in travel_types:
                Type.objects.create(name=name)
            print('Created types:', ', '.join(travel_types))


@receiver(post_migrate)
def create_questions(sender, **kwargs):
    if sender.name == 'request':

        question_numberS = ['CC1', 'CC2', 'CC3', 'SQD0', 'SQD1', 'SQD2', 'SQD3', 'SQD4', 'SQD5', 'SQD6', 'SQD7', 'SQD8']

        if not Question.objects.filter(question_number__in=question_numberS).exists():

            for question_number in question_numberS:
                Question.objects.create(question_number=question_number)
            print('Created questions:', ', '.join(question_numberS))


    