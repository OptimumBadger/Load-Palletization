# Contains all the important classes for the ROUTING PROBLEM


class Load:
    def __init__(self, type, weight, volume):
        self.type = type  # Gives the type of load, number between 1-10
        self.weight = weight  # total weight of the load
        self.volume = volume  # Total volume occupied by the load


class Task:
    def __init__(self, id, source, destination, status, cargo, departure_time, arrival_time, nodes, delay):
        self.id = id  # Task identification number
        self.source = source  # Object of Airport class giving source
        self.destination = destination  # Object of Airport class giving destination
        self.status = status  # tells whether the task is completed or not
        self.cargo = cargo  # List of objects of Load Class
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.nodes = nodes
        self.delay = delay

    def get_weight(self):
        # Gives the total weight to be carried in that task
        weight = 0
        for item in self.cargo:
            weight = weight + item.weight

        return weight

    def get_volume(self):
        # Gives the total volume to be carried in that task
        volume = 0
        for item in self.cargo:
            volume = volume + item.volume

        return volume

    def set_status(self, status):
        # Used for setting the status of task
        self.status = status


class Aircraft:
    def __init__(self, type, id, location, velocity, range, max_fuel_capacity, afcr, max_cargo_capacity,
                 max_cargo_space, pc, fuel,
                 reserve_fuel, ground_service_time, ACN, min_runway_length, c1, c2, c3, c4, dc1, dc2, dc3, dc4, SF,
                 time_in_air, flying_time,
                 time_flown,
                 ):
        self.type = type
        self.id = id
        self.velocity = velocity
        self.location = location  # Object of Airport class
        self.range = range
        self.max_fuel_capacity = max_fuel_capacity
        self.avg_fuel_consumption_rate = afcr
        self.max_cargo_capacity = max_cargo_capacity
        self.max_cargo_space = max_cargo_space
        self.pax_capacity = pc
        self.fuel = fuel
        self.reserve_fuel = reserve_fuel
        self.ground_service_time = ground_service_time
        self.ACN = ACN  # ACN ranges from 5 for light aircraft to 130 for heavy aircraft
        self.min_runway_length = min_runway_length
        self.mc1 = c1
        self.mc2 = c2
        self.mc3 = c3
        self.mc4 = c4
        self.dc1 = dc1
        self.dc2 = dc2
        self.dc3 = dc3
        self.dc4 = dc4
        self.SF = SF
        self.time_in_air = time_in_air
        self.flying_time = flying_time
        self.time_in_mission = time_flown

    def set_location(self, location):
        # Used for changing the location of flight
        self.location = location

    def set_fuel_level(self, fuel):
        # Used for changing the fuel level in flight
        self.fuel = fuel

    def maintenance_check(self):
        if self.time_in_air % self.mc4 >= self.SF * self.mc4:
            print("Flight {} is due for C4 maintenance".format(self.id))
            return True
        if self.time_in_air % self.mc3 >= self.SF * self.mc3:
            print("Flight {} is due for C3 maintenance".format(self.id))
            return True
        if self.time_in_air % self.mc2 >= self.SF * self.mc2:
            print("Flight {} is due for C2 maintenance".format(self.id))
            self.time_in_air = 0
            return True
        if self.time_in_air % self.mc1 >= self.SF * self.mc1:
            print("Flight {} is due for C1 maintenance".format(self.id))
            return True
        return False

    def maintenance_procedure(self):
        if self.time_in_air % self.mc4 >= self.SF * self.mc4:
            self.time_in_mission = self.time_in_mission + self.dc4
            self.flying_time = 0
        if self.time_in_air % self.mc3 >= self.SF * self.mc3:
            self.time_in_mission = self.time_in_mission + self.dc3
            self.flying_time = 0
        if self.time_in_air % self.mc2 >= self.SF * self.mc2:
            self.time_in_mission = self.time_in_mission + self.dc2
            self.flying_time = 0
        if self.time_in_air % self.mc1 >= self.SF * self.mc1:
            self.time_in_mission = self.time_in_mission + self.dc1
            self.flying_time = 0


class Airport:
    def __init__(self, name, rc, mc, PCN, runway_len):
        self.name = name
        self.RC = rc
        self.MC = mc
        self.PCN = PCN
        self.runway_len = runway_len
