from collections import defaultdict
import uuid

class User:
    def __init__(self, name):
        self.name = name
        self.vehicles = {}
    
    def add_vehicle(self, vehicle_category, vehicle_number, total_seats, is_available=True):
        if vehicle_number in self.vehicles:
            raise ValueError(f"Vehicle {vehicle_number} is already registered for user {self.name}")
        self.vehicles[vehicle_number] = (vehicle_category, total_seats, is_available) 
    
    def update_vehicle_status(self, vehicle_number, status):
        if vehicle_number in self.vehicles:
            temp = list(self.vehicles[vehicle_number])
            temp[-1] = status
            self.vehicles[vehicle_number] = tuple(temp)
        else:
            raise ValueError(f"Vehicle {vehicle_number} not found for user {self.name}")

class RideSharing:
    def __init__(self):
        self.users = {}
        self.active_rides = {}
        self.available_rides = defaultdict(list)
        self.user_stats = defaultdict(lambda: {"offered_rides": 0, "taken_rides": 0})
        self.ride_selections = defaultdict(list)
    
    def add_user(self, user_name):
        user_id = str(uuid.uuid4())
        self.users[user_id] = User(user_name)
        return user_id
    
    def add_vehicle(self, user_id, vehicle_category, vehicle_number, total_seats):
        if user_id in self.users:
            self.users[user_id].add_vehicle(vehicle_category, vehicle_number, total_seats)
        else:
            raise ValueError(f"User {user_id} not found")
    
    def offer_ride(self, user_id, vehicle_number, src, destination, vacant_seats):
        user = self._get_user(user_id)
        if vehicle_number in user.vehicles and user.vehicles[vehicle_number][-1]:
            ride_id = str(uuid.uuid4())
            self.available_rides[src].append((ride_id, destination, user_id, vehicle_number, vacant_seats))
            self.user_stats[user_id]['offered_rides'] += 1
            user.update_vehicle_status(vehicle_number, False)
            self.active_rides[ride_id] = (user_id, vehicle_number, vacant_seats)
        else:
            raise Exception(f"Vehicle {vehicle_number} is not available or does not exist for user {user_id}")
    
    def select_ride(self, user_id, src, destination, preferences={}):
        seats = preferences.get('vacant_seats', 1)
        category = preferences.get('vehicle_category', '')
        selected_ride = self._find_rides(src, destination, category, seats)
        
        if selected_ride:
            ride_id, ride_dest, ride_user_id, ride_vehicle_number, ride_seats = selected_ride[0]
            if ride_id not in self.ride_selections:
                self.ride_selections[ride_id] = []
            self.ride_selections[ride_id].append((user_id, seats))
            self.user_stats[user_id]['taken_rides'] += 1
            self._update_ride_seats(ride_id, -seats)
            return selected_ride
        return None
    
    def end_ride(self, ride_id):
        if ride_id in self.active_rides:
            user_id, vehicle_number, _ = self.active_rides.pop(ride_id)
            user = self._get_user(user_id)
            user.update_vehicle_status(vehicle_number, True)
        else:
            raise ValueError(f"Ride ID {ride_id} not found")
    
    def cancel_ride(self, ride_id):
        if ride_id in self.active_rides:
            user_id, vehicle_number, _ = self.active_rides.pop(ride_id)
            user = self._get_user(user_id)
            user.update_vehicle_status(vehicle_number, True)
            for src, rides in self.available_rides.items():
                self.available_rides[src] = [ride for ride in rides if ride[0] != ride_id]
        else:
            raise ValueError(f"Ride ID {ride_id} not found")
    
    def print_ride_stats(self):
        for user_id, stats in self.user_stats.items():
            user = self._get_user(user_id)
            print(f"User {user.name}: {stats['offered_rides']} offered rides, {stats['taken_rides']} taken rides")
    
    def _find_rides(self, src, destination, category, seats):
        rides = []
        visited = set()
        queue = [(src, [])]
        
        while queue:
            current, current_rides = queue.pop(0)
            if current == destination:
                rides.extend(current_rides)
                break
            
            for ride in self.available_rides[current]:
                ride_id, ride_dest, ride_user_id, ride_vehicle_number, ride_seats = ride
                if ride_dest not in visited:
                    user = self._get_user(ride_user_id)
                    vehicle_category = user.vehicles[ride_vehicle_number][0]
                    remaining_seats = self._get_remaining_seats(ride_id)
                    if (category == '' or vehicle_category == category) and remaining_seats >= seats:
                        visited.add(ride_dest)
                        new_rides = current_rides + [ride]
                        queue.append((ride_dest, new_rides))
        
        return rides
    
    def _update_ride_seats(self, ride_id, seat_change):
        if ride_id in self.active_rides:
            user_id, vehicle_number, vacant_seats = self.active_rides[ride_id]
            new_vacant_seats = vacant_seats + seat_change
            if new_vacant_seats < 0:
                raise Exception("Not enough seats available")
            self.active_rides[ride_id] = (user_id, vehicle_number, new_vacant_seats)
        else:
            raise ValueError(f"Ride ID {ride_id} not found")
    
    def _get_remaining_seats(self, ride_id):
        if ride_id in self.active_rides:
            return self.active_rides[ride_id][2]
        return 0
    
    def _get_user(self, user_id):
        if user_id in self.users:
            return self.users[user_id]
        else:
            raise ValueError(f"User ID {user_id} not found")

# Sample Test Cases

ride_sharing = RideSharing()

# Onboard users
user1_id = ride_sharing.add_user('Rider 1')
user2_id = ride_sharing.add_user('Rider 2')
user3_id = ride_sharing.add_user('Rider 3')
user4_id = ride_sharing.add_user('Passenger 1')
user5_id = ride_sharing.add_user('Passenger 2')

# Add vehicles
ride_sharing.add_vehicle(user1_id, 'XUV', 'xa-213-1231', 5)
ride_sharing.add_vehicle(user2_id, 'XUV', 'xa-521-31', 5)
ride_sharing.add_vehicle(user3_id, 'SEDAN', 'xa-12-1231', 5)

# Offer rides
ride_sharing.offer_ride(user1_id, 'xa-213-1231', 'bangalore', 'chennai', 2)
ride_sharing.offer_ride(user2_id, 'xa-521-31', 'chennai', 'madurai', 2)
ride_sharing.offer_ride(user3_id, 'xa-12-1231', 'madurai', 'delhi', 2)

# Select rides
rides_user4 = ride_sharing.select_ride(user4_id, 'bangalore', 'madurai', {'vehicle_category': 'XUV'})
print("Selected Rides for User 4:", rides_user4)

# User 5 attempts to select the same ride
rides_user5 = ride_sharing.select_ride(user5_id, 'bangalore', 'madurai', {'vehicle_category': 'XUV'})
print("Selected Rides for User 5:", rides_user5)

# End rides
for ride in rides_user4:
    ride_sharing.end_ride(ride[0])

# Print ride stats
ride_sharing.print_ride_stats()
