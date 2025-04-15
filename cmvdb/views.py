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

# Route 
@api_view(['GET'])
def trip_route(request, id):
    try:
        trip = Trip.objects.get(pk=id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    # start_coords = [trip.start_latitude, trip.start_longitude]
    # end_coords = [trip.end_latitude, trip.end_longitude]

    start_coords = [8.681495,49.41461]
    end_coords = [8.687872,49.420318]

    ors_url = f"https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248f28417b551294803bad6ac6d95732a67&start={start_coords[0]},{start_coords[1]}&end={end_coords[0]},{end_coords[1]}"
   
    response = requests.get(ors_url)
    
    if response.status_code == 200:
        route_info = response.json()
        return JsonResponse(route_info)
    else:
        return JsonResponse({"error": "Failed to fetch route information"}, status=response.status_code)