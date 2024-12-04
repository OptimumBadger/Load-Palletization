import helpers
from copy import deepcopy
from itertools import zip_longest


def distances(route, matrix):
    # gives the distance between two destinations
    source = route[0]
    destination = route[1]

    for row_number, node in enumerate(matrix[0]):
        if node == source:
            row_num = row_number
            break
    for col_number, node in enumerate(matrix[0]):
        if node == destination:
            col_num = col_number
            break
    return matrix[row_num + 1][col_num]


def loading_time_calc(task_list, aircraft, matrix1):
    # Given a task_list and an aircraft, it calculates the loading and unloading time for that aircraft
    row = [item for item in matrix1 if item[0] == aircraft.id]
    time = 0
    for i in range(len(task_list)):
        time = time + i * row[0][i + 1]

    return time / 60


def best_RC(task, matrix, aircraft, refuelling_nodes):
    # chooses the RC which it should go visit next
    # sort all the possible RCs which it can go with existing fuel and choose RC which is nearest to destination
    # first arrange the compatible refuelling nodes
    compatible_rcs = []
    for node in refuelling_nodes:
        if aircraft.ACN <= node.PCN and node.runway_len >= aircraft.min_runway_length:
            compatible_rcs.append(node)
    RC = task.source
    if not compatible_rcs:
        return RC

    initial_fuel_qty = aircraft.fuel
    speed = aircraft.velocity
    avg_fuel_cons_rate = aircraft.avg_fuel_consumption_rate
    max_radius = initial_fuel_qty / avg_fuel_cons_rate * speed
    available_rcs = []
    for airport in compatible_rcs:
        if distances([task.source.name, airport.name], matrix) <= max_radius:
            available_rcs.append(airport)
    if not available_rcs:
        return RC

    dmin = distances([task.source.name, task.destination.name], matrix)
    for airport in available_rcs:
        if distances([airport.name, task.destination.name], matrix) < dmin:
            RC = airport
            dmin = distances([airport.name, task.destination.name], matrix)
    return RC


def task_time(task, matrix, aircraft, refuelling_nodes):
    # Given a task and the aircraft, it gives the time flight takes tp complete the task, all the refuelling nodes it
    # goes to and fuel recharged at each location
    # Note that aircraft is always standing at source node of this task
    # It returns infinity time with empty nodes and 0 fuel as outputs in case if the task can't be done with that flight
    current_location = aircraft.location  # object
    speed = aircraft.velocity
    time = 0
    RC, fuel = refuel(task, matrix, deepcopy(aircraft), refuelling_nodes[:], 1)
    if RC == ['Plane is stuck']:
        return float('inf'), [], [0]
    for item in RC:
        time = time + distances([current_location.name, item.name], matrix) / speed
        current_location = item
    return time, RC, fuel


def flight_time(task, task_list, matrix, matrix1, aircraft, refuelling_nodes):
    # given a task and a aircraft, it calculates the time taken by that flight to complete the task as well as fuel
    # remaining after it. Returns infinity if the task can't be done with that aircraft

    current_location = aircraft.location
    pickup_location = task.source
    pre_task = helpers.Task(0, current_location, pickup_location, 'NC', task.cargo, 0, 0, [], 0)
    aircraft_copy1 = deepcopy(aircraft)
    time1, RC1, fuel1 = task_time(pre_task, matrix, aircraft_copy1, refuelling_nodes[:])
    if time1 == float('inf'):
        return float('inf'), float('inf'), 0, 0, [], time1
    fuel_refilled = sum(fuel1)
    aircraft_copy2 = deepcopy(aircraft)
    aircraft_copy2.location = pickup_location
    aircraft_copy2.fuel = aircraft_copy2.fuel - time1 * aircraft.avg_fuel_consumption_rate + fuel_refilled
    time2, RC2, fuel2 = task_time(task, matrix, aircraft_copy2, refuelling_nodes[:])
    if time2 == float('inf'):
        return float('inf'), float('inf'), 0, 0, [], time1

    # calculating fuel
    fuel_refilled = sum(fuel2) + sum(fuel1)
    fuel_after = aircraft.fuel + fuel_refilled - (time1 + time2) * aircraft.avg_fuel_consumption_rate
    RC1.extend(RC2)
    fuel1.extend(fuel2)
    Rc_with_fuel = list(zip(RC1, fuel1))

    # modifying Rc_with_fuel
    Rc_w_fuel = [i for i, j in list(zip_longest(Rc_with_fuel, Rc_with_fuel[1:], fillvalue=(0, 0))) if i[0] != j[0]]

    # Calculating loading time
    loading_time = loading_time_calc(task_list, aircraft, matrix1)
    task_total_weight = task.get_weight()
    loading_factor = aircraft.max_cargo_capacity / task_total_weight  # modifies the loadig time when full cargo is
    # not getting carried
    if loading_factor < 1:
        loading_time = loading_factor * loading_time
    unloading_time = loading_time

    flying_time = time1 + time2

    total_time = time1 + time2 + (loading_time + unloading_time)

    return total_time, flying_time, loading_time, fuel_after, Rc_w_fuel, time1


def flight_ranking(task, task_list, matrix, matrix1, aircrafts, refuelling_nodes):
    # given the available set of flights and given task, it gives the ranking of flights for that task
    time = []
    fuel_in_flight = []
    loading_time = []
    r_with_f = []
    air_time = []
    fly_time = []
    pre_task_time = []

    for flight in aircrafts:
        t, ft, l, f, r, t1 = flight_time(task, task_list, matrix, matrix1, flight, refuelling_nodes)
        t = t + flight.time_in_mission
        ft = ft + flight.time_in_air
        gt = ft + flight.flying_time
        time.append(t)
        air_time.append(ft)
        fly_time.append(gt)
        loading_time.append(l)
        fuel_in_flight.append(f)
        r_with_f.append(r)
        pre_task_time.append(t1)
    ranking = zip(aircrafts, time, air_time, loading_time, fuel_in_flight, r_with_f, pre_task_time, fly_time)
    result = sorted(ranking, key=lambda x: x[1])
    return result


def loading(task, aircraft, time, air_time, fly_time, fuel):
    # assigns the task to flight and changes its location and total time flown
    aircraft.location = task.destination
    aircraft.time_in_mission = time
    aircraft.time_in_air = air_time
    aircraft.flying_time = fly_time
    aircraft.fuel = fuel


def solution_printer(path, aircrafts, path_df):
    for i in range(len(aircrafts)):
        test_list = path[aircrafts[i].id]
        res = [i for i, j in zip_longest(test_list, test_list[1:]) if i != j]
        path[aircrafts[i].id] = res

    # print(path)
    # Prints final solution
    
    obj_value = 0

    for item in aircrafts:

        if item.time_in_mission > obj_value:
            obj_value = item.time_in_mission
            
    msg = 'Objective value:{} hours'.format(f'{obj_value:.2f}')
    print(msg)
    path_df.loc[len(path_df)] = str(msg)

    for item in aircrafts:
        msg = '{}:{} hours'.format(item.id, f'{item.time_in_air:.2f}')
        print(msg)
        path_df.loc[len(path_df)] = str(msg)

    plan_output = ''
    for item in path:
        msg = 'Route for plane {}:\n'.format(item)
        for node in path[item]:
            msg += ' {} -> '.format(node)
        msg = msg[:-4]
        path_df.loc[len(path_df)] = str(msg)
        plan_output += msg
        plan_output += '\n'

    print(plan_output)


def refuel(task, matrix, aircraft, refuelling_nodes, counter):
    # Given a task and a aircraft, it returns all the airports aircraft goes to complete the task and refuelling amount
    # at each airport
    # counter tells whether the flight is starting the path from source of task or it is in middle of task
    # counter=0 means flight is in middle of task, visiting some RC
    # counter=1 means flight is starting from source node

    source = task.source
    destination = task.destination
    initial_fuel_qty = aircraft.fuel
    speed = aircraft.velocity
    avg_fuel_cons_rate = aircraft.avg_fuel_consumption_rate
    fuel_capacity = aircraft.max_fuel_capacity
    fuel_consumed = (distances([source.name, destination.name], matrix)) / speed * avg_fuel_cons_rate
    fuel = []
    RC = []

    # Case1: when destination is refuelling node
    if task.destination in refuelling_nodes:
        min_fuel_needed = 0
        if initial_fuel_qty - fuel_consumed >= min_fuel_needed:
            # No need for refuelling
            RC.append(source)
            fuel.append(0)
            RC.append(destination)
            fuel.append(0)

            return RC, fuel
        else:
            # refuelling needs to be done, go to the best RC which is closest to destination, update location and fuel
            # quantity in aircraft and call function again

            # Case 1: source is not rc and flight is going to next rc
            if source not in refuelling_nodes and counter == 1:
                nextstop = best_RC(task, matrix, aircraft, refuelling_nodes)
                if nextstop == source:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                aircraft.location = nextstop
                aircraft.fuel = initial_fuel_qty - distances([source.name, nextstop.name],
                                                             matrix) / speed * avg_fuel_cons_rate
                refuelling_nodes.remove(nextstop)
                newtask = helpers.Task(task.id, nextstop, destination, 'NC', task.cargo, 0, 0, [], 0)
                moreRC, morefuel = refuel(newtask, matrix, aircraft, refuelling_nodes, 0)
                RC.extend(moreRC)
                fuel.extend(morefuel)
                if 'Plane is stuck' in RC:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                return RC, fuel

            # Case 2: source is rc
            if min_fuel_needed + fuel_consumed - initial_fuel_qty < fuel_capacity - initial_fuel_qty:
                # after refuelling, the flight is going to destination
                fuel_refilled = min_fuel_needed + fuel_consumed - initial_fuel_qty
                fuel.append(fuel_refilled)
                RC.append(source)
                RC.append(destination)
                fuel.append(0)
                return RC, fuel
            else:
                # after refuelling, flight is going to next RC
                fuel_refilled = fuel_capacity - initial_fuel_qty
                fuel.append(fuel_refilled)
                RC.append(source)
                aircraft.fuel = fuel_capacity
                nextstop = best_RC(task, matrix, aircraft, refuelling_nodes)
                if nextstop == source:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                aircraft.location = nextstop
                aircraft.fuel = fuel_capacity - distances([source.name, nextstop.name],
                                                          matrix) / speed * avg_fuel_cons_rate
                refuelling_nodes.remove(nextstop)
                newtask = helpers.Task(task.id, nextstop, destination, 'NC', task.cargo, 0, 0, [], 0)
                moreRC, morefuel = refuel(newtask, matrix, aircraft, refuelling_nodes, 0)
                RC.extend(moreRC)
                fuel.extend(morefuel)
                if 'Plane is stuck' in RC:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                return RC, fuel

    # Case2: when destination is not a refuelling node
    else:
        min_fuel_needed = distances([task.source.name, task.destination.name], matrix) / speed * avg_fuel_cons_rate
        if initial_fuel_qty - fuel_consumed >= min_fuel_needed:
            # No need for refuelling
            RC.append(source)
            fuel.append(0)
            RC.append(destination)
            fuel.append(0)
            return RC, fuel
        else:
            # refuelling needs to be done go to the best RC which is closest to destination, update location and fuel
            # quantity in aircraft and call function again

            # Case 1: source is not RC and flight is going to next RC
            if source not in refuelling_nodes and counter == 1:
                nextstop = best_RC(task, matrix, aircraft, refuelling_nodes)
                if nextstop == source:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                aircraft.location = nextstop
                aircraft.fuel = initial_fuel_qty - distances([source.name, nextstop.name],
                                                             matrix) / speed * avg_fuel_cons_rate
                refuelling_nodes.remove(nextstop)
                newtask = helpers.Task(task.id, nextstop, destination, 'NC', task.cargo, 0, 0, [], 0)
                moreRC, morefuel = refuel(newtask, matrix, aircraft, refuelling_nodes, 0)
                RC.extend(moreRC)
                fuel.extend(morefuel)
                if 'Plane is stuck' in RC:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                return RC, fuel

            # Case 2: Source is RC
            if min_fuel_needed + fuel_consumed - initial_fuel_qty <= fuel_capacity - initial_fuel_qty:
                # Flight after refuelling is going to destination
                fuel_refilled = min_fuel_needed + fuel_consumed - initial_fuel_qty
                fuel.append(fuel_refilled)
                RC.append(source)
                fuel.append(0)
                RC.append(destination)
                return RC, fuel
            else:
                # after refuelling, flight is going to next RC
                fuel_refilled = fuel_capacity - initial_fuel_qty
                fuel.append(fuel_refilled)
                RC.append(source)
                aircraft.fuel = fuel_capacity
                nextstop = best_RC(task, matrix, aircraft, refuelling_nodes)
                if nextstop == source:
                    return ['Plane is stuck'], ['Not enough fuel capacity']

                aircraft.location = nextstop
                aircraft.fuel = fuel_capacity - distances([source.name, nextstop.name],
                                                          matrix) / speed * avg_fuel_cons_rate
                refuelling_nodes.remove(nextstop)
                newtask = helpers.Task(task.id, nextstop, destination, 'NC', task.cargo, 0, 0, [], 0)
                moreRC, morefuel = refuel(newtask, matrix, aircraft, refuelling_nodes, 0)
                RC.extend(moreRC)
                fuel.extend(morefuel)
                if 'Plane is stuck' in RC:
                    return ['Plane is stuck'], ['Not enough fuel capacity']
                return RC, fuel


def path_update(task, LF, aircraft, path, table, df2, nodes_df, loading_time):
    # updates path traversed by flight
    weight = task.get_weight() * LF
    airport = [item[0].name for item in task.nodes]
    airport_cut = [i for i, j in zip_longest(airport, airport[1:]) if i != j]
    fuel_recharged = [item[1] for item in task.nodes]
    nodes_again = list(zip(airport, fuel_recharged))
    # Adding RCs to the path and filling the table
    for i in range(len(task.nodes)):
        path[aircraft.id].append('{}({})'.format(nodes_again[i][0][1:], f'{nodes_again[i][1]:.2f}'))

    table.add_row(
        [task.id, [task.source.name, task.destination.name], weight, aircraft.id, nodes_again])
    nodes_df.loc[len(nodes_df),nodes_df.columns] = task.id, [task.source.name, task.destination.name], weight, aircraft.id, nodes_again
    nodes = []
    for i in range(len(nodes_again)):
        nodes.append(nodes_again[i][0])

    df2.loc[len(df2),df2.columns] = task.id, nodes, aircraft.id, f'{loading_time:.2f}', aircraft.max_cargo_capacity


def time_update(task, table, df1, schedule_df):
    table.add_row(
        [task.id, [task.source.name, task.destination.name], f'{task.departure_time:.2f}', f'{task.arrival_time:.2f}'])
    schedule_df.loc[len(schedule_df),schedule_df.columns] = task.id, [task.source.name, task.destination.name], f'{task.departure_time:.2f}', f'{task.arrival_time:.2f}'
    df1.loc[len(df1),df1.columns] = task.id,task.source.name,task.destination.name,f'{task.departure_time:.2f}',f'{task.arrival_time:.2f}'


def safety_check(aircraft, time_for_task):
    if aircraft.mc1 - time_for_task < 0:
        return False
    if aircraft.mc2 - time_for_task < 0:
        return False
    if aircraft.mc3 - time_for_task < 0:
        return False
    if aircraft.mc4 - time_for_task < 0:
        return False

    return True


def possible_RC(airport, refuelling_nodes, matrix):
    a = {}
    for item in refuelling_nodes:
        x = distances([airport.name, item.name], matrix)
        a[item.name] = x
    return a


def maintenance_facility(airport, maintenance_nodes, matrix):
    facility = {}
    for item in maintenance_nodes:
        x = distances([airport.name, item.name], matrix)
        facility[item.name] = x
    return facility


def best_MC(airport, maintenance_nodes, matrix):
    dmin = distances([airport.name, maintenance_nodes[0].name], matrix)
    MC = maintenance_nodes[0]
    for node in maintenance_nodes:
        x = distances([airport.name, node.name], matrix)
        if x < dmin:
            dmin = x
            MC = node
    return MC
