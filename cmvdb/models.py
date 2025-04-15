from django.db import models

class Trip(models.Model):
 
    current_location = models.CharField(max_length=200, help_text="Enter the current location of the trip")
    pickup_location = models.CharField(max_length=200, help_text="Enter the pickup location")
    dropoff_location = models.CharField(max_length=200, help_text="Enter the dropoff location")
    current_cycle_hours = models.FloatField(help_text="Enter the current cycle used (in hours)")
    total_distance = models.FloatField(help_text="Total distance of the trip in miles")

    # Calculated fields
    worked_hours = models.FloatField(default=0, help_text="Total hours worked by the driver")
    fuel_stops = models.IntegerField(default=0, help_text="Number of fuel stops required")
    pickup_dropoff_time = models.FloatField(default=2, help_text="Total time spent on pickup and drop-off (in hours)")

    def __str__(self):
        return f"{self.pickup_location} to {self.dropoff_location}"

    def save(self, *args, **kwargs):
        self.fuel_stops = int(self.total_distance // 1000)
        self.worked_hours = round(self.current_cycle_hours + self.pickup_dropoff_time, 2)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Trip"
        verbose_name_plural = "Trips"
