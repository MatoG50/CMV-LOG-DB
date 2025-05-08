# models.py
from django.db import models
from datetime import timedelta, datetime
from django.utils import timezone

class Trip(models.Model):
    current_location = models.CharField(max_length=200)
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200)
    current_cycle_hours = models.FloatField()
    total_distance = models.FloatField(blank=True, null=True)
    start_time = models.DateTimeField(default=timezone.now)

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

    def generate_log_sheets(self):
        log_sheets = []
        time = timedelta(hours=0)
        drive_speed = 60  # mph
        max_drive_hours = 11
        break_after = 8  # hours driving before 30-min break
        off_duty_reset = 10  # hours
        max_on_duty = 14  # max on-duty hours per day

        if not self.total_distance:
            return log_sheets

        total_drive_hours = self.total_distance / drive_speed
        remaining_drive_hours = total_drive_hours
        current_on_duty = 0
        current_drive = 0
        day_counter = 1
        remaining_fuel_stops = self.fuel_stops

        # Initialize first day's log
        current_day_entries = []
        current_day_start = time
        current_day_drive = 0
        current_day_on_duty = 0

        # 1 hour ON-duty for pickup
        current_day_entries.append({
            'time': str(time),
            'status': 'ON',
            'duration': 1.0,
            'activity': 'Pickup',
            'location': self.pickup_location
        })
        time += timedelta(hours=1)
        current_on_duty += 1
        current_day_on_duty += 1

        while remaining_drive_hours > 0:
            # Check for 30-min break requirement
            if current_drive >= break_after:
                current_day_entries.append({
                    'time': str(time),
                    'status': 'OFF',
                    'duration': 0.5,
                    'activity': '30-min break'
                })
                time += timedelta(minutes=30)
                current_on_duty += 0.5
                current_day_on_duty += 0.5
                current_drive = 0

            # Check for 14-hour on-duty limit
            if current_on_duty >= max_on_duty:
                # Finalize current day's log
                log_sheets.append(self._create_log_sheet(
                    day_counter,
                    current_day_entries,
                    current_day_start,
                    time
                ))
                
                # Start new day
                day_counter += 1
                current_day_entries = []
                current_day_start = time
                current_day_drive = 0
                current_day_on_duty = 0
                
                # 10-hour reset
                current_day_entries.append({
                    'time': str(time),
                    'status': 'OFF',
                    'duration': off_duty_reset,
                    'activity': '10-hour reset'
                })
                time += timedelta(hours=off_duty_reset)
                current_on_duty = 0
                current_drive = 0

            # Calculate next driving segment
            drive_chunk = min(
                max_drive_hours - current_drive,
                max_on_duty - current_on_duty,
                remaining_drive_hours
            )

            if drive_chunk <= 0:
                break

            # Add driving segment
            progress = 1 - (remaining_drive_hours / total_drive_hours)
            location = f"Route {progress:.1%}"
            current_day_entries.append({
                'time': str(time),
                'status': 'DR',
                'duration': drive_chunk,
                'location': location
            })
            time += timedelta(hours=drive_chunk)
            current_on_duty += drive_chunk
            current_day_on_duty += drive_chunk
            current_drive += drive_chunk
            current_day_drive += drive_chunk
            remaining_drive_hours -= drive_chunk

            # Handle fuel stops
            if (remaining_fuel_stops > 0 and 
                (total_drive_hours - remaining_drive_hours) >= 
                (self.fuel_stops - remaining_fuel_stops + 1) * (1000/drive_speed)):
                current_day_entries.append({
                    'time': str(time),
                    'status': 'ON',
                    'duration': 0.25,
                    'activity': 'Fuel stop',
                    'location': location
                })
                time += timedelta(minutes=15)
                current_on_duty += 0.25
                current_day_on_duty += 0.25
                remaining_fuel_stops -= 1

        # Drop-off 1 hour ON
        current_day_entries.append({
            'time': str(time),
            'status': 'ON',
            'duration': 1.0,
            'activity': 'Drop-off',
            'location': self.dropoff_location
        })
        time += timedelta(hours=1)
        
        # Finalize last day's log
        log_sheets.append(self._create_log_sheet(
            day_counter,
            current_day_entries,
            current_day_start,
            time
        ))

        return log_sheets

    def _create_log_sheet(self, day, entries, start_time, end_time):
        """Helper to create a structured log sheet for a day"""
        drive_hours = sum(e['duration'] for e in entries if e['status'] == 'DR')
        on_duty_hours = sum(e['duration'] for e in entries if e['status'] in ('DR', 'ON'))
        off_duty_hours = sum(e['duration'] for e in entries if e['status'] in ('OFF', 'SB'))
        
        # Calculate date based on trip start time
        sheet_date = (self.start_time + start_time).date()
        
        return {
            'day': day,
            'date': sheet_date.strftime('%Y-%m-%d'),
            'start_time': str(start_time),
            'end_time': str(end_time),
            'entries': entries,
            'summary': {
                'drive_hours': round(drive_hours, 2),
                'on_duty_hours': round(on_duty_hours, 2),
                'off_duty_hours': round(off_duty_hours, 2),
                'fuel_stops': sum(1 for e in entries if e.get('activity') == 'Fuel stop')
            }
        }

    class Meta:
        verbose_name = "Trip"
        verbose_name_plural = "Trips"