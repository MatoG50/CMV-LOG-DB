from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Trip
from .serializers import TripSerializer
from rest_framework.decorators import api_view         
import requests

@api_view(['GET', 'POST'])
def trip_list(request):
    if request.method == 'GET':
        trips = Trip.objects.all()
        serializer = TripSerializer(trips, many=True)
        return JsonResponse({"trips": serializer.data})

    if request.method == 'POST':
        serializer = TripSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"trip": serializer.data}, status=201)
        return JsonResponse(serializer.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
def trip_detail(request, id):
    try:
        trip = Trip.objects.get(pk=id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    if request.method == 'GET':
        serializer = TripSerializer(trip)
        return JsonResponse({"trip": serializer.data})

    if request.method == 'PUT':
        serializer = TripSerializer(trip, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"trip": serializer.data})
        return JsonResponse(serializer.errors, status=400)

    if request.method == 'DELETE':
        trip.delete()
        return JsonResponse({"message": "Trip deleted"}, status=204) 

    
@api_view(['GET'])
def trip_route(request, id):
    try:
        trip = Trip.objects.get(pk=id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    ORS_API_KEY = "5b3ce3597851110001cf6248f28417b551294803bad6ac6d95732a67"

    def geocode_location(location):
        geo_url = f"https://api.openrouteservice.org/geocode/search"
        params = {
            "api_key": ORS_API_KEY,
            "text": location,
            "size": 1
        }
        response = requests.get(geo_url, params=params)
        if response.status_code == 200:
            data = response.json()
            coords = data['features'][0]['geometry']['coordinates'] 
            return coords
        else:
            return None

    pickup_coords = geocode_location(trip.pickup_location)
    dropoff_coords = geocode_location(trip.dropoff_location)

    if not pickup_coords or not dropoff_coords:
        return JsonResponse({"error": "Failed to geocode one or both locations"}, status=400)

    # Build route URL
    directions_url = (
        f"https://api.openrouteservice.org/v2/directions/driving-car"
        f"?api_key={ORS_API_KEY}"
        f"&start={pickup_coords[0]},{pickup_coords[1]}"
        f"&end={dropoff_coords[0]},{dropoff_coords[1]}"
    )

    route_response = requests.get(directions_url)

    if route_response.status_code == 200:
        route_info = route_response.json()
        distance = route_info['features'][0]['properties']['summary']['distance']
        total_distance = round(distance / 1609.34, 2)
        trip.total_distance = total_distance
        # trip.current_cycle_hours = trip.worked_hours + trip.pickup_dropoff_time
        trip.current_location = trip.dropoff_location
        trip.save()

      # Generate ELD log based on updated trip data
        log_data = trip.generate_log()

        # Return route info along with the generated log
        return JsonResponse({
            "route": route_info,
            "eld_log": log_data
        })
    else:
        return JsonResponse({"error": "Failed to fetch route information"}, status=route_response.status_code)

class TripLogView(View):
    def get(self, request, trip_id):
        try:
            # Fetch the trip based on the provided trip_id
            trip = Trip.objects.get(pk=trip_id)
        except Trip.DoesNotExist:
            return JsonResponse({"error": "Trip not found"}, status=404)
        
        # Generate the log using the generate_log method of the Trip model
        log = trip.generate_log()
        
        # Return the log as a JSON response
        return JsonResponse({"log": log})