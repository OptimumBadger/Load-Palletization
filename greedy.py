import xlrd
from prettytable import PrettyTable
import Methods
import numpy as np
import pandas as pd
import helpers
import sys 
import os
os.makedirs('Solutions/routing_scheduling',exist_ok=True)
os.makedirs('Solutions/routing_scheduling/Results',exist_ok=True)
stdoutOrigin=sys.stdout 
sys.stdout = open("Solutions/routing_scheduling/routing_scheduling.txt", "w")

# Specify the Column Names while initializing the Table
df1 = pd.DataFrame(columns=['Task ID', 'Source', 'Destination', 'Departure Time',
                          'Arrival Time'])
df2 = pd.DataFrame(columns=['Task ID', 'Nodes', 'Aircraft Assigned', 'loading time', 'AircraftCargoLimit'])


myTable = PrettyTable(
    ["Task ID", "Task", "CargoWeight", "Aircraft Assigned", "Nodes visited with fuel charged"])
nodes_df = pd.DataFrame(columns=["Task ID", "Task", "CargoWeight", "Aircraft Assigned", "Nodes visited with fuel charged"])

myTable2 = PrettyTable(["Task ID", "Task", "Departure Time", "Arrival Time"])
schedule_df = pd.DataFrame(columns=["Task ID", "Task", "Departure Time", "Arrival Time"])

maintenance_df = pd.DataFrame(columns = ["instructions"])


dfs = pd.ExcelFile('Input_Data1_new.xls')

# extracting load type info
Box_df = dfs.parse('Box')
loadlist = {}

for i in Box_df.index:
    loadlist[Box_df['Box type'][i]] =  [ Box_df['Weight(kg)'][i], float((Box_df['Length(cm)'][i]*Box_df['Width(cm)'][i]*Box_df['Height(cm)'][i])/1000000) ]

Box_df = Box_df.set_index('Box type', inplace= True)

# Extracting airport info
Airport_info_df = dfs.parse('Airport_info')
airports = []

for i in Airport_info_df.index:
    airports.append(helpers.Airport(Airport_info_df['Airfield ID'][i], Airport_info_df['Refuelling center'][i], Airport_info_df['Maintenance facility'][i], Airport_info_df['PCN number'][i], Airport_info_df['Runway length(m)'][i]))

Airport_info_df = Airport_info_df.set_index('Airfield ID', inplace= True)

# extracting task info
Task_info_df = dfs.parse('Task_info')
tasks = []
id = 1
for i in Task_info_df.index:
    cargo = []
    # reading load info
    for type, l in loadlist.items():
        box = helpers.Load(type, float(Task_info_df[type][i] * l[0]),
                           float(Task_info_df[type][i] * l[1]) )
        cargo.append(box)

    source = next((item for item in airports if item.name == Task_info_df['Source'][i]))
    destination = next((item for item in airports if item.name == Task_info_df['Destination'][i]))
    d_time = 0
    a_time = 0
    n = []  # Nodes it goes to

    tasks.append(
        helpers.Task(id, source, destination, 'NC', cargo, d_time, a_time, n, 'N'))
    id = id + 1

# Creating loading_time matrix
Loading_Unloading_time_df = dfs.parse('Loading_Unloading_time')
loading_time = []

for i in Loading_Unloading_time_df.index:
    lt = [Loading_Unloading_time_df['Aircraft ID'][i]]
    for type, l in loadlist.items():
        lt.append(Loading_Unloading_time_df[type][i])
    loading_time.append(lt)

# extracting aircraft info
Aircraft_info_df = dfs.parse('Aircraft_info')
aircrafts = []

for i in Aircraft_info_df.index:
    ac_type = Aircraft_info_df['a/c type'][i]
    ac_id = Aircraft_info_df['a/c id'][i]
    initial_location = next((item for item in airports if item.name == Aircraft_info_df['Initial Flight Position'][i]))
    velocity = Aircraft_info_df['Velocity(km/hr)'][i]
    range_flight = Aircraft_info_df['Range(kms)'][i]
    max_fuel_capacity = Aircraft_info_df['Max fuel capacity(kgs)'][i]
    avg_fuel_cons_rate = Aircraft_info_df['Avg fuel consumption rate(kg/hr)'][i]
    weight_limit = Aircraft_info_df['Max cargo capacity(kgs)'][i]
    volume_limit = Aircraft_info_df['max cargo space(cube meter)'][i]
    pax_cap = Aircraft_info_df['pax capacity'][i]
    fuel = Aircraft_info_df['Initial Fuel(kgs)'][i]
    reserve_fuel = Aircraft_info_df['reserve fuel(kg)[.10 *ftank capacity]'][i]
    gst = Aircraft_info_df['ground service time(minute)'][i]
    acn = Aircraft_info_df['ACN number'][i]
    min_runway_length = Aircraft_info_df['Min runway len'][i]
    hours_for_c1 = Aircraft_info_df['C1'][i]
    hours_for_c2 = Aircraft_info_df['C2'][i]
    hours_for_c3 = Aircraft_info_df['C3'][i]
    hours_for_c4 = Aircraft_info_df['C4'][i]
    downtimec1 = Aircraft_info_df['Downtime for C1'][i]
    downtimec2 = Aircraft_info_df['Downtime for C2'][i]
    downtimec3 = Aircraft_info_df['Downtime for C3'][i]
    downtimec4 = Aircraft_info_df['Downtime for C4'][i]
    safety_factor = Aircraft_info_df['Safety factor'][i]
    time_in_air = Aircraft_info_df['Time_in_air'][i]
    flying_time = Aircraft_info_df['Flying_time'][i]
    time_spent = Aircraft_info_df['Time_in_mission'][i]
    aircrafts.append(helpers.Aircraft(ac_type, ac_id, initial_location, velocity, range_flight, max_fuel_capacity,
                                      avg_fuel_cons_rate, weight_limit, volume_limit, pax_cap, fuel, reserve_fuel, gst,
                                      acn, min_runway_length, hours_for_c1, hours_for_c2, hours_for_c3, hours_for_c4,
                                      downtimec1, downtimec2, downtimec3, downtimec4, safety_factor,
                                      time_in_air, flying_time,
                                      time_spent))

# creating distance matrix


Distance_matrix_df = dfs.parse('Distance_matrix')
distance = [Distance_matrix_df.columns[1:]]

for i in Distance_matrix_df.index:
    dist = []
    for col in Distance_matrix_df.columns[1:]:
        dist.append(Distance_matrix_df[col][i])
    distance.append(dist)

# extracting the airports with refuelling capacity
refuelling_nodes = []

for airport in airports:
    if airport.RC == 1:
        refuelling_nodes.append(airport)

# extracting the airports with maintenance facility
maintenance_nodes = []

for airport in airports:
    if airport.MC == 1:
        maintenance_nodes.append(airport)

# Create a dictionary that stores path of each flight
path = {}
for aircraft in aircrafts:
    path[aircraft.id] = ['{}({})'.format(aircraft.location.name[1], 0.00)]

time_when_task_done = 0  # time=0

last_task = len(tasks) # last_task_condition

# Start the program

for task in tasks:
    # print('task{}'.format(task.id))

    if task.status == 'C':
        continue

    # Creating task_list
    task_list = []
    for type, l in loadlist.items():
        task_list.append(Task_info_df[type][task.id - 1])
    # Creating the list of compatible aircraft

    valid_aircrafts = []
    for aircraft in aircrafts:
        if aircraft.ACN <= task.destination.PCN and task.destination.runway_len >= aircraft.min_runway_length:
            valid_aircrafts.append(aircraft)
    number_of_valid_aircrafts = len(valid_aircrafts)
    if number_of_valid_aircrafts == 0:
        msg = 'Task{} cant be done safely.Sorry!!'.format(task.id)
        print(msg)
        maintenance_df.loc[len(maintenance_df)] = str(msg)
        continue
    ranking = Methods.flight_ranking(task, task_list, distance, loading_time, valid_aircrafts, refuelling_nodes)

    ac_alloted = ranking[0][0]

    time_spent_in_mission = ranking[0][1]

    air_time_spent_in_mission = ranking[0][2]

    loading_time_in_plane = ranking[0][3]

    fuel_remaining = ranking[0][4]

    Rc_nodes = ranking[0][5]

    pretask_time = ranking[0][6]

    fly_time = ranking[0][7]

    # If no plane can be assigned to given task
    if time_spent_in_mission == float('inf'):
        msg = 'Task{} cant be done since flight is getting stuck. Bring another plane.Sorry!!'.format(task.id)
        print(msg)
        maintenance_df.loc[len(maintenance_df)] = str(msg)
        continue

    # Flight is taking off at departure time, time of execution of this task
    capacity = ac_alloted.max_cargo_capacity
    speed = ac_alloted.velocity

    space_left = capacity - task.get_weight()
    cargo_getting_loaded = task.get_weight() if task.get_weight() <= ac_alloted.max_cargo_capacity else ac_alloted.max_cargo_capacity
    loading_factor = cargo_getting_loaded / task.get_weight()

    loading_time_in_plane = loading_time_in_plane if space_left >= 0 else loading_time_in_plane * loading_factor

    departure_time = ac_alloted.time_in_mission + pretask_time + loading_time_in_plane
    arrival_time = time_spent_in_mission - loading_time_in_plane
    task.departure_time = departure_time
    task.arrival_time = arrival_time
    task.nodes = Rc_nodes
    # This step is critical for defining when the flight was lifted for the task
    if departure_time > time_when_task_done:
        time_when_task_done = departure_time

    i = 1
    current_task = task
    gen = (item for item in tasks if item.id == task.id + i)
    next_task = next(gen) if task.id != last_task else "last task"
    case1 = 0
    case2 = 0

    # Checking 2 cases

    # Case 1: Checking if the current task can be done fully or not

    if space_left < 0:
        Methods.loading(current_task, ac_alloted, time_spent_in_mission, air_time_spent_in_mission, fly_time,
                        fuel_remaining)
        Methods.path_update(current_task, loading_factor, ac_alloted, path, myTable, df2, nodes_df, loading_time_in_plane)
        Methods.time_update(current_task, myTable2, df1, schedule_df)
        # Sending the flight for maintenance
        if ac_alloted.maintenance_check():
            chosen_facility = Methods.best_MC(ac_alloted.location, maintenance_nodes, distance)
            msg = "Flight {} is sent for maintenance at airport {} after task {}".format(ac_alloted.id, chosen_facility.name, task.id)
            print(msg)
            maintenance_df.loc[len(maintenance_df)] = str(msg)
            ac_alloted.maintenance_procedure()

    # Keep assigning further flights till all the cargo is loaded
    # how much weight needs to be carried more
    cargo_left = task.get_weight() - ac_alloted.max_cargo_capacity

    flight_id = 1

    while space_left < 0:
        # Loop enters here,so,case 1 was selected
        ranking_for_rem_task = Methods.flight_ranking(task, task_list, distance, loading_time, valid_aircrafts,
                                                      refuelling_nodes)

        case1 = 1
        ac_alloted_next = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][0]
        cargo_getting_loaded = cargo_left if cargo_left < ac_alloted_next.max_cargo_capacity else ac_alloted_next.max_cargo_capacity
        loading_factor = cargo_getting_loaded / task.get_weight()
        time_spent_in_mission_next = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][1]
        air_time_spent_in_mission_next = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][2]
        loading_time_in_plane_next = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][3]
        fuel_left = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][4]
        Rc_nodes1 = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][5]
        pretask_time_for_next_task = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][6]
        fly_time_for_next_task = ranking_for_rem_task[flight_id % number_of_valid_aircrafts][7]

        if time_spent_in_mission_next == float('inf'):
            msg = 'Task{} cant be done.Plane is getting stuck. Bring another plane.Sorry!!'.format(task.id)
            print(msg)
            maintenance_df.loc[len(maintenance_df)] = str(msg)
            break

        loading_time_in_plane_next = loading_time_in_plane_next * -space_left / task.get_weight() \
            if -space_left < ac_alloted_next.max_cargo_capacity \
            else loading_time_in_plane_next * ac_alloted_next.max_cargo_capacity / task.get_weight()

        departure_time = ac_alloted_next.time_in_mission + pretask_time_for_next_task + loading_time_in_plane_next
        arrival_time = time_spent_in_mission_next - loading_time_in_plane_next
        current_task.departure_time = departure_time
        current_task.arrival_time = arrival_time
        current_task.nodes = Rc_nodes1

        Methods.loading(current_task, ac_alloted_next, time_spent_in_mission_next, air_time_spent_in_mission_next,
                        fly_time_for_next_task,
                        fuel_left)
        Methods.path_update(current_task, loading_factor, ac_alloted_next, path, myTable, df2, nodes_df, loading_time_in_plane_next)
        Methods.time_update(current_task, myTable2, df1, schedule_df)

        if departure_time > time_when_task_done:
            time_when_task_done = departure_time

            # Sending the flight for maintenance
            if ac_alloted.maintenance_check():
                chosen_facility = Methods.best_MC(ac_alloted.location, maintenance_nodes, distance)
                msg = "Flight {} is sent for maintenance at airport {} after task {}".format(ac_alloted.id, chosen_facility.name, task.id)
                print(msg)
                maintenance_df.loc[len(maintenance_df)] = str(msg)
                ac_alloted.maintenance_procedure()

        space_left = space_left + ac_alloted_next.max_cargo_capacity
        cargo_left = cargo_left - cargo_getting_loaded
        flight_id = flight_id + 1

    task.status = 'C'

    if space_left < 0:
        for aircraft in aircrafts:
            if aircraft.time_in_mission < time_when_task_done:
                aircraft.time_in_mission = time_when_task_done
        msg = 'Task{} cant be done fully. Bring another plane.Sorry!!'.format(task.id)
        print(msg)
        maintenance_df.loc[len(maintenance_df)] = str(msg)
        continue

    # Check if it is last task

    if task.id == last_task:
        # do the loading, schedule the flight,update the path and break out of loop

        Methods.loading(task, ac_alloted, time_spent_in_mission, air_time_spent_in_mission, fly_time,
                        fuel_remaining)

        for aircraft in aircrafts:
            if aircraft.time_in_mission < departure_time:
                aircraft.time_in_mission = departure_time

        Methods.path_update(task, loading_factor, ac_alloted, path, myTable, df2, nodes_df, loading_time_in_plane_next)
        Methods.time_update(task, myTable2, df1, schedule_df)
        break

    if case1 == 1:
        # Case 1 was already selected,so,no need to check for case 2, hence, continue to next task
        for aircraft in aircrafts:
            if aircraft.time_in_mission < time_when_task_done:
                aircraft.time_in_mission = time_when_task_done
        continue

    # Case 2: when weight to be loaded is less than capacity of flight, and space left is sufficient to carry next task
    delays = 0
    Methods.loading(task, ac_alloted, time_spent_in_mission, air_time_spent_in_mission, fly_time, fuel_remaining)
    Methods.path_update(task,loading_factor, ac_alloted, path, myTable, df2, nodes_df, loading_time_in_plane_next)
    # Sending the flight for maintenance
    if ac_alloted.maintenance_check():
        chosen_facility = Methods.best_MC(ac_alloted.location, maintenance_nodes, distance)
        msg = "Flight {} is sent for maintenance at airport {} after task {}".format(ac_alloted.id, chosen_facility.name, task.id)
        print(msg)
        maintenance_df.loc[len(maintenance_df)] = str(msg)
        ac_alloted.maintenance_procedure()
        while space_left > next_task.get_weight() and ac_alloted.ACN <= next_task.destination.PCN and next_task.destination. \
                runway_len >= ac_alloted.min_runway_length:

            # Check if next task source node is same or not

            if next_task.source == current_task.source:

                ptask = helpers.Task(next_task.id, current_task.destination, next_task.destination, 'NC',
                                     next_task.cargo, 0, 0, [], 'N')

                x1 = Methods.distances([next_task.source.name, next_task.destination.name], distance)
                x2 = Methods.distances([current_task.destination.name, next_task.destination.name], distance)

                # time to do next task
                t_for_ptask, RC_for_ptask, fuel_for_ptask = Methods.task_time(ptask, distance, ac_alloted,
                                                                              refuelling_nodes)
                nodes_for_ptask = list(zip(RC_for_ptask, fuel_for_ptask))
                fuel_remaining_after_ptask = fuel_remaining + sum(
                    fuel_for_ptask) - t_for_ptask * ac_alloted.avg_fuel_consumption_rate

                # Checking safety for maintenance before alloting next task

                if not Methods.safety_check(ac_alloted, t_for_ptask):
                    break

                # Note that if next task can be done in finite time, it will be alloted
                if t_for_ptask == float('inf'):
                    break

                # Check if the distance between the destination of next task and destination of current task is smaller
                # than source of next task and destination of next task

                if x2 < x1:
                    case2 = 1
                    current_task.delay = 'Y'

                    next_task_list = []
                    for type, l in loadlist.items():
                        next_task_list.append(Task_info_df[type][next_task.id - 1])

                    time_to_load_for_next_task = Methods.loading_time_calc(next_task_list, ac_alloted, loading_time)
                    delays = delays + time_to_load_for_next_task
                    arrival_time = ac_alloted.time_in_mission + t_for_ptask
                    next_task.departure_time = departure_time
                    next_task.arrival_time = arrival_time
                    next_task.nodes = nodes_for_ptask
                    next_task.delay = 'Y'
                    time_add = t_for_ptask + ac_alloted.time_in_mission + time_to_load_for_next_task
                    air_time_add = t_for_ptask + ac_alloted.time_in_air
                    air_time_add1 = t_for_ptask + ac_alloted.flying_time

                    Methods.loading(next_task, ac_alloted, time_add, air_time_add, air_time_add1,
                                    fuel_remaining_after_ptask)
                    Methods.path_update(next_task,1, ac_alloted, path, myTable, df2, nodes_df, time_to_load_for_next_task)
                    next_task.status = 'C'

                    # Sending the flight for maintenance
                    if ac_alloted.maintenance_check():
                        chosen_facility = Methods.best_MC(ac_alloted.location, maintenance_nodes, distance)
                        msg = "Flight {} is sent for maintenance at airport {} after task{}".format(ac_alloted.id, chosen_facility.name, next_task.id)
                        print(msg)
                        maintenance_df.loc[len(maintenance_df)] = str(msg)
                        ac_alloted.maintenance_procedure()

                    space_left = space_left - next_task.get_weight()
                    # print(current_task.id)
                    current_task = next_task
                    i = i + 1
                    next_task = next(gen)

                    if task.id == len(tasks) + 1:
                        break

                else:
                    break
            else:
                break

    if case2 == 1:
        for task in tasks:
            if task.status == 'C' and task.delay == 'Y':
                task.departure_time = task.departure_time + delays
                task.arrival_time = task.arrival_time + delays
                task.delay = 'N'
                Methods.time_update(task, myTable2, df1, schedule_df)

        departure_time = departure_time + delays
        for aircraft in aircrafts:
            if aircraft.time_in_mission < departure_time:
                aircraft.time_in_mission = departure_time

        delays = 0
        continue

    Methods.time_update(task, myTable2, df1, schedule_df)
    for aircraft in aircrafts:
        if aircraft.time_in_mission < departure_time:
            aircraft.time_in_mission = departure_time

# Print the solution

path_df = pd.DataFrame(columns = ["instructions"])
Methods.solution_printer(path, aircrafts, path_df)

# Print a table with tasks and corresponding relevant information
print(myTable)
print(myTable2)
df1['Nodes'] = df2['Nodes'].copy()
df1['Aircraft Assigned'] = df2['Aircraft Assigned'].copy()
df1['loading time'] = df2['loading time'].copy()

prev = 'xyz'
cnt = 0
multi = []
for i in nodes_df.index:
    if nodes_df["Task ID"][i] == prev:
        cnt += 1
        if cnt == 1:
            multi.append( ( prev, [(nodes_df["Aircraft Assigned"][i-1], df2['AircraftCargoLimit'][i-1]), (nodes_df["Aircraft Assigned"][i], df2['AircraftCargoLimit'][i])] ))
        else:
            multi[-1][1].append( (nodes_df["Aircraft Assigned"][i], df2['AircraftCargoLimit'][i]) )
    else:
        cnt = 0
        prev = schedule_df["Task ID"][i]

#df1.to_excel('Output_Greedy1.xlsx')
#print(df1)
#print(nodes_df)
#print(schedule_df)

maintenance_df.to_excel('Solutions/routing_scheduling/Results/Maintenance.xls')
path_df.to_excel('Solutions/routing_scheduling/Results/Path.xls')
nodes_df.to_excel('Solutions/routing_scheduling/Results/Nodes.xls')
schedule_df.to_excel('Solutions/routing_scheduling/Results/Schedule.xls')


sys.stdout.close()
sys.stdout=stdoutOrigin