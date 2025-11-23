from django.db import models
from django.core.validators import MinValueValidator

class Cat(models.Model):
    name = models.CharField(max_length=100)
    experience_years = models.IntegerField(validators=[MinValueValidator(0)])
    breed = models.CharField(max_length=50)
    salary = models.FloatField(validators=[MinValueValidator(0.0)])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Mission(models.Model):

    cat = models.OneToOneField(
        Cat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_mission'
    )
    is_completed = models.BooleanField(default=False)

    def is_target_range_valid(self):
        return 1 <= self.targets.count() <= 3

    def __str__(self):
        return f"Mission #{self.id} ({'Completed' if self.is_completed else 'Active'})"

class Target(models.Model):

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name='targets'
    )
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    notes = models.TextField(default="")
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Target: {self.name} in {self.country}"

    class Meta:
        unique_together = ('mission', 'name')