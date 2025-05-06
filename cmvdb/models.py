from django.db import models
from datetime import timedelta

class Trip(models.Model):
    current_location = models.CharField(max_length=200)
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200)
    current_cycle_hours = models.FloatField()
    total_distance = models.FloatField(blank=True, null=True)

    worked_hours = models.FloatField(default=0)
    fuel_stops = models.IntegerField(default=0)
    pickup_dropoff_time = models.FloatField(default=2)

    def __str__(self):
        return f"{self.pickup_location} to {self.dropoff_location}"

    def save(self, *args, **kwargs):
        if self.total_distance is not None:
            self.fuel_stops = int(self.total_distance // 1000)
        self.worked_hours = round(self.current_cycle_hours + self.pickup_dropoff_time, 2)
        super().save(*args, **kwargs)

    def generate_log(self):
        log = []
        time = timedelta(hours=0)
        drive_speed = 60  # mph
        max_drive_hours = 11
        break_after = 8  # hours driving before 30-min break
        off_duty_reset = 10  # hours
        max_on_duty = 14  # max on-duty hours per day

        if not self.total_distance:
            return log

        total_drive_hours = self.total_distance / drive_speed
        remaining_drive_hours = total_drive_hours
        current_on_duty = 0
        current_drive = 0
        day_counter = 1  # Tracks the current day in the trip

        # 1 hour ON-duty for pickup
        log.append({'time': str(time), 'status': 'ON'})
        time += timedelta(hours=1)
        current_on_duty += 1

        fuel_stop_counter = self.fuel_stops
        fuel_thresholds = [total_drive_hours - (i + 1) * 16.67 for i in range(fuel_stop_counter)]

        while remaining_drive_hours > 0:
            if current_drive >= break_after:
                log.append({'time': str(time), 'status': 'OFF'})
                time += timedelta(minutes=30)
                current_on_duty += 0.5
                current_drive = 0

            if current_on_duty >= max_on_duty:
                # Day over, reset for a new day
                log.append({'time': str(time), 'status': 'OFF'})
                time += timedelta(hours=off_duty_reset)
                current_on_duty = 0
                current_drive = 0
                day_counter += 1  # New day starts

            drive_chunk = min(
                max_drive_hours - current_drive,
                max_on_duty - current_on_duty,
                remaining_drive_hours
            )

            if drive_chunk <= 0:
                log.append({'time': str(time), 'status': 'OFF'})
                time += timedelta(hours=off_duty_reset)
                current_on_duty = 0
                current_drive = 0
                continue

            log.append({'time': str(time), 'status': 'DR'})
            time += timedelta(hours=drive_chunk)
            current_on_duty += drive_chunk
            current_drive += drive_chunk
            remaining_drive_hours -= drive_chunk

            # Handle fuel stops
            while self.fuel_stops > 0 and remaining_drive_hours < total_drive_hours - (self.fuel_stops * 16.67):
                log.append({'time': str(time), 'status': 'OFF'})
                time += timedelta(minutes=15)
                current_on_duty += 0.25
                self.fuel_stops -= 1

        # Drop-off 1 hour ON
        log.append({'time': str(time), 'status': 'ON'})
        time += timedelta(hours=1)

        # End with OFF duty
        log.append({'time': str(time), 'status': 'OFF'})

        return log

    class Meta:
        verbose_name = "Trip"
        verbose_name_plural = "Trips"
