#!/usr/bin/env python3

import copy
import sys

#This function generate the index of the next router in current router table table_labels_list
#It inputs current router, next router, and the list contains all the router names, and outpus the
#index of the next router in current router table table_labels_list calculated
def generate_table_idx(router, next_router, router_names):
    table_labels_list = copy.deepcopy(router_names)
    table_labels_list.remove(router)
    table_idx = table_labels_list.index(next_router)
    return table_idx

#This function will get the second router in the path and the row to read in its table for update function
#It inputs the current router, and the row column numbers in current_router table we are at, and  the list contains all the router names,
#and outputs the second router name and the row to be read in its table.
def corresponding_router_and_row(current_router,r,c,router_names):
    table_labels_list = copy.deepcopy(router_names)
    table_labels_list.remove(current_router)
    router = table_labels_list[c]
    dest_router = table_labels_list[r]
    find_min_label_list = copy.deepcopy(router_names)
    find_min_label_list.remove(router)
    row = find_min_label_list.index(dest_router)
    return router,row

#This function prints out the dictionary routing tables into the required print_format
#It inputs the router and table dictionary, router names list and the count accumalated to be the time
#It outputs the count, so that in next print, the time is accumalated
def print_format(routers_and_tables,router_names,count):
    for router in router_names:
        table_label = copy.deepcopy(router_names)
        table_label.remove(router)
        table = routers_and_tables.get(router)
        print("router",router," at t=",count)
        print(" ",' '.join(str(label) if label else val for label in table_label))
        r = 0
        for ro_name in table_label:
            print(ro_name,' '.join(str(num) if num != float('inf') else "INF" for num in table[r]))
            r +=1
    print(" ")
    count += 1
    return count

#This function writes a summary for the converged routing tables
#It inputs the routing tables dictionary, and router names list
#outputs the current shortest paths
def conclusion(routers_and_tables,router_names):
    shortest = []
    for router in router_names:
        table_label = copy.deepcopy(router_names)
        table_label.remove(router)
        table = routers_and_tables.get(router)
        for dest_router_num in range(len(table_label)):
            the_row = table[dest_router_num]
            the_row = [val if val != '-' else float('inf') for val in the_row]
            print("router",router+":",table_label[dest_router_num],"is",min(the_row),"routing through",table_label[the_row.index(min(the_row))])
            path = [router,table_label[the_row.index(min(the_row))],min(the_row)]
            shortest.append(path)
    return shortest


#This function initialises the routing tables based on the link length information
#input: link information, router names list, and router tables dictionary
#output: the initialised router tables dictionary
def initial_tables(links,router_names,routers_and_tables):
    if len(links[0]) != 1:
        for lin_info in links:
            #lin_info = links[i]
            distance = int(lin_info[2])
            first_router_idx = router_names.index(lin_info[0])
            second_router_idx = router_names.index(lin_info[1])
            table_first = routers_and_tables.get(lin_info[0])
            table_second = routers_and_tables.get(lin_info[1])
            router1 = lin_info[0]
            router2 = lin_info[1]
            idx_1 = generate_table_idx(lin_info[0],lin_info[1],router_names)
            idx_2 = generate_table_idx(lin_info[1],lin_info[0],router_names)
            for r in range(len(table_first)):
                if distance == -1:
                    for r in range(len(table_first)):
                        table_first[r][idx_1] = "-"
                        table_second[r][idx_2] = "-"
                else:
                    original_1, original_2 = table_first[idx_1][idx_1], table_second[idx_2][idx_2]
                    change_1, change_2 = original_1 - distance, original_2 - distance
                    table_first[idx_1][idx_1] = distance
                    table_second[idx_2][idx_2] = distance
    else:
        lin_info = links
        distance = int(lin_info[2])
        first_router_idx = router_names.index(lin_info[0])
        second_router_idx = router_names.index(lin_info[1])
        table_first = routers_and_tables.get(lin_info[0])
        table_second = routers_and_tables.get(lin_info[1])
        router1 = lin_info[0]
        router2 = lin_info[1]
        idx_1 = generate_table_idx(lin_info[0],lin_info[1],router_names)
        idx_2 = generate_table_idx(lin_info[1],lin_info[0],router_names)
        for r in range(len(table_first)):
            if distance == -1:
                for r in range(len(table_first)):
                    table_first[r][idx_1] = "-"
                    table_second[r][idx_2] = "-"
            else:
                original_1, original_2 = table_first[idx_1][idx_1], table_second[idx_2][idx_2]
                change_1, change_2 = original_1 - distance, original_2 - distance
                table_first[idx_1][idx_1] = distance
                table_second[idx_2][idx_2] = distance
    return routers_and_tables


#This function initialise the routing tables when new link information link_changes
#it inputs the link information, router names, and routing table dictionary
#outputs updated routing tables dictionary
def reinitial_tables(links,router_names,routers_and_tables):
    lin_info = links
    distance = int(lin_info[2])
    first_router_idx = router_names.index(lin_info[0])
    second_router_idx = router_names.index(lin_info[1])
    table_first = routers_and_tables.get(lin_info[0])
    table_second = routers_and_tables.get(lin_info[1])
    router1 = lin_info[0]
    router2 = lin_info[1]
    idx_1 = generate_table_idx(lin_info[0],lin_info[1],router_names)
    idx_2 = generate_table_idx(lin_info[1],lin_info[0],router_names)
    for r in range(len(table_first)):
        if distance == -1:
            for r in range(len(table_first)):
                table_first[r][idx_1] = "-"
                table_second[r][idx_2] = "-"
        else:
            original_1, original_2 = table_first[idx_1][idx_1], table_second[idx_2][idx_2]
            change_1, change_2 = distance - original_1, distance - original_2
            table_first[idx_1][idx_1] = distance
            table_second[idx_2][idx_2] = distance
            for r in range(len(table_first)):
                if r != idx_1:
                    if change_1 != float('inf') and change_1 != float('-inf') and table_first[r][idx_1] != float('inf'):
                        table_first[r][idx_1] = table_first[r][idx_1] + change_1

                if r != idx_2:
                    if change_2 != float('inf') and change_2 != float('-inf') and table_second[r][idx_1] != float('inf'):
                        table_second[r][idx_2] = table_second[r][idx_2] + change_2

    return routers_and_tables


#This function updates the routing tables, it inputs dictionary contains the routers and their tables,m: the dimension of the table label(totoal routers number -1),
#and outputs the new updated dictionary
def update_table(routers_and_tables,m):
    new_routers_and_tables = copy.deepcopy(routers_and_tables)
    for router in routers_and_tables:
        table = copy.deepcopy(routers_and_tables.get(router))
        for r in range(m):#find min start
             for c in range(m): #the router's row to find min destination
                if r == c:
                    continue # because initial dist was set in initial_table function
                if table[r][c] == '-':
                    continue # if no link, skip computing distance
                cost = table[c][c]
                if cost == "-":
                    cost = float('inf')
                find_min_router, row = corresponding_router_and_row(router,r,c,router_names)
                find_min_table = routers_and_tables.get(find_min_router)
                find_min_row = copy.deepcopy(find_min_table[row])
                for i in range(len(find_min_row)):
                    if find_min_row[i] == "-":
                        find_min_row[i] = float('inf')
                min_dist = min(find_min_row)
                table[r][c] = cost + min_dist
                new_routers_and_tables.update({router:table})
    return new_routers_and_tables

#This function will initilaise the table when new edges information comes in and determine whether to update the table based on the shortest path,
#it inputs the big dictionary contains the routers and their tables, m: the dimension of the table label(totoal routers number -1), a list contain all routers,
#and the shortest path information. the function outputs the router table dictionary
def dict_after_edgeChanges(routers_and_tables,m,link_changes, router_names,shortest):
    for i in range(len(link_changes)):
        routers_and_tables = reinitial_tables(link_changes[i],router_names,routers_and_tables)
        if len(link_changes[0]) == 1:
            link_changes[2] = int(link_changes[2])
        else:
            link_changes[i][2] = int(link_changes[i][2])
        for j in range(len(shortest)):
            if len(link_changes[0]) != 1:
                if link_changes[i][2] == -1 or link_changes[i][2] == "-1":
                    continue
                if link_changes[i][0] == shortest[j][0] and link_changes[i][1] == shortest[j][1]:
                    if int(link_changes[i][2]) <  shortest[j][2]:
                        routers_and_tables = update_table(routers_and_tables,m)
            else:
                if link_changes[2] == "-1"or link_changes[2] == "-1":
                    continue
                    #link_changes[2] =float('inf')
                if link_changes[0] == shortest[j][0] and link_changes[1] == shortest[j][1]:
                    if int(link_changes[2]) <  shortest[j][2]:
                        routers_and_tables = update_table(routers_and_tables,m)
    return routers_and_tables


count = 0
router_names = []
user_input = input()
inp = "not_empty"
while True:
    #input router names
    r_name = user_input
    while r_name != "":
        router_names.append(r_name)
        user_input = input()
        r_name = user_input
    router_names = sorted(router_names)
    #create routers and their very initialised tables dictionary
    m = len(router_names)-1
    init_dist_table = [[float('inf') for j in range(m)] for i in range(m)]
    routers_and_tables = {}
    for i in range(len(router_names)):
        routers_and_tables.update({router_names[i]: copy.deepcopy(init_dist_table)})
    inp = user_input
    user_input = input()
    if user_input == "" and inp == "":
        exit()

    #receives edges inputs
    links = []
    lin_info = user_input
    while lin_info != "":
        lin_info = lin_info.strip().split()
        links.append(lin_info)
        user_input = input()
        lin_info = user_input
    inp = user_input

    routers_and_tables = initial_tables(links,router_names,routers_and_tables)
    count = print_format(routers_and_tables,router_names,count)
    new_routers_and_tables = update_table(routers_and_tables,m)
    count = print_format(new_routers_and_tables,router_names,count)
    #continue printing tables till converge
    while True:
        new_new_routers_and_tables = update_table(new_routers_and_tables,m)
        routers_and_tables = new_routers_and_tables
        new_routers_and_tables = new_new_routers_and_tables
        if routers_and_tables == new_routers_and_tables:
            break
        count = print_format(new_routers_and_tables,router_names,count)

    shortest = conclusion(routers_and_tables,router_names)
    print(" ")
    user_input = input()
    if user_input == "" and inp == "":
        exit()


    while True:
        link_changes = []
        change_info = user_input
        while change_info != "":
            change_info = change_info.strip().split()
            link_changes.append(change_info)
            user_input = input()
            change_info = user_input
        inp = user_input

        routers_and_tables = dict_after_edgeChanges(routers_and_tables,m,link_changes, router_names,shortest)
        count = print_format(routers_and_tables,router_names,count)
        new_routers_and_tables = update_table(routers_and_tables,m)
        count = print_format(new_routers_and_tables,router_names,count)
        #continue printing tables till converge
        while True:
            new_new_routers_and_tables = update_table(new_routers_and_tables,m)
            routers_and_tables = new_routers_and_tables
            new_routers_and_tables = new_new_routers_and_tables
            if routers_and_tables == new_routers_and_tables:
                break
            count = print_format(new_routers_and_tables,router_names,count)

        shortest = conclusion(routers_and_tables,router_names)
        print(" ")
        user_input = input()
        if user_input == "" and inp == "":
            exit()
