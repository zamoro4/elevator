import threading, time, sys
# threading - to split user input listener and state/action calculator

#elevator setup. 4 params from task + some used for work
elevator={
    'floor_count':5, 'floor_height':3, 'move_speed':1, 'open_time':5,
    'opening_time': 1, #time for doors to open/close
    'direction':0, 'floor':1, 'next_floor':None, 'action':None, #state properties
    'call_queue':[], 'dest_queue':[], #lists with calls
}

#describes and returns actions and following actions
def calculate_actions():
    next_floor = elevator['next_floor'] if elevator['next_floor'] else 0
    return {#action Door_open takes 'opening_time' from elevator setup, followed by 'door_keep' action, message 'Opening the door' and shifts floor for 0
            'door_open':[elevator['opening_time'], 'door_keep', 'Opening the door', 0],
             'door_keep':[elevator['open_time'], 'door_close', 'Door opened', 0],
             'door_close':[elevator['opening_time'], None, 'Closing the door', 0],
            # action moove_one mooves one floor (or zero, if elevator is called from the floor it's already on),
            # takes time, calculated from floor height and moove speed from elevator setup, followed by 'door_open' action, message 'mooving to next floor' and shifts floor for 1
             'moove one':[elevator['floor_height']/elevator['move_speed']*min(abs(elevator['floor']-next_floor), 1), 'door_open', 'Moving to next floor', 1*elevator['direction']],
             }

#elevator is set up with some initials and now takes args from console
try: elevator['floor_count']=int(sys.argv[1])
except BaseException: pass
try: elevator['floor_height']=float(sys.argv[2])
except BaseException: pass
try: elevator['move_speed']=float(sys.argv[3])
except BaseException: pass
try: elevator['open_time']=float(sys.argv[4])
except BaseException: pass

print ('Initials: floor_count - {0}, floor_height(m) - {1}, move_speed(m/s) - {2}, open_time(s) - {3}'.format(elevator['floor_count'], elevator['floor_height'], elevator['move_speed'], elevator['open_time']))

#here are all calculations for needed actions ang elevator operation logic
#this func runs in separate thread 'state_calculator'
def state_calculator():
    while True: #infinite loop for operating
        time.sleep(0.1) #tick time not to hang cpu
        #open door if elevator is called from/directed to the floor it's already on
        if not elevator['action'] and elevator['next_floor'] and elevator['next_floor']==elevator['floor']: elevator['action']='door_open'
        #start mooving if elevator was sleeping and got new input
        if not elevator['action'] and elevator['next_floor']: elevator['action']='moove one'
        #remove actions and move direction if no floors in queues
        if not elevator['action'] and not elevator['next_floor']:
            elevator['action'], elevator['direction']=None, 0
            #print time.asctime(), '------------> actions ended'

        #if there is particular action in elevator - perform it, sleep for time this action takes and set new action
        if elevator['action']:
            params = calculate_actions()[elevator['action']]  #calculate action times (especialy for movement)
            print (time.asctime(), 'Floor {3}, {0}, waiting - {1}, direction - {4}, calls - {5}, destinations - {6}'.format(params[2], params[0], params[1], elevator['floor'],
                                'Up' if elevator['direction']>0 else 'Down' if elevator['direction']<0 else None, elevator['call_queue'], elevator['dest_queue']))
            time.sleep(params[0])   #sleep for action time
            elevator['floor']+=params[3]    #shift floor
            elevator['action']=params[1]    #shift to next action

            #continue mooving if not on destination floor. by default movving is followed by door open, this condition overrides default
            if elevator['floor']!=elevator['next_floor'] and elevator['next_floor']:
                elevator['action']='moove one'
            #if on destination floor and all needed actions are passed - delete destination floor from queues and clear next floor. it will be recalculated later
            if elevator['floor']==elevator['next_floor'] and not elevator['action']:
                elevator['call_queue'] = [k for k in elevator['call_queue'] if k != elevator['next_floor']]
                elevator['dest_queue'] = [k for k in elevator['dest_queue'] if k != elevator['next_floor']]
                elevator['next_floor']=None

        #this part only recalculates next destination floor based on logic: if there is no moving direction - takes closest floor from queues
        #if elevator is already mooving in some direction - calculates closest floor in this direction
        if len(elevator['call_queue']+elevator['dest_queue'])>0: #so if queues are not empty
            #calculate tuples of floor number and distance from current floor using set of inputs (from queues)
            floors = [[k, k- elevator['floor']] for k in list(set(elevator['call_queue'] + elevator['dest_queue']))]
            if elevator['direction']:   #if elevator has direction, take only floors in this direction
                floors = [k for k in floors if k[1] * elevator['direction'] >= 0]
                elevator['next_floor'] = sorted(floors, key=lambda x: abs(x[1]))[0][0] if len(floors)>0 else None #sort by distance and take closest one
            if not elevator['direction']:   #if elevator has no direction - take closest destination floor in i=any direction
                elevator['next_floor'] = sorted(floors, key=lambda x: abs(x[1]))[0][0]
                elevator['direction'] = 1 if elevator['next_floor'] - elevator['floor'] > 0 else 0 if elevator['next_floor'] == elevator['floor'] else -1


#this func is for treating user input and runs in separate thread user_input. just checks inputs for some rules in infinite loop
def user_input():
    print ('=================> To call elevator - type "call [floor number]", to enter destination floor - type "dest [floor number]')
    while True:
        uinput=input()
        uinput=uinput.split(' ') #as I ask to type something like 'call #' or 'dest #' - split call type and call floor by space
        if len(uinput)!=2:   #check input format
            print ('Missing something in input')
            continue
        if uinput[0] not in ['call','dest']: #check action type
            print ('Wrong action')
            continue
        if uinput[1] not in [str(k) for k in range(1, elevator['floor_count']+1)]:   #check floor number to be between 1 and max floor from setup
            print ('Wrong floor, floor should be between {0} and {1}'. format(1, elevator['floor_count']))
            continue
        #if OK - print acceptance and put to corresponding queue
        #remark - at the end there is no difference between dest and call, though they are 2 separate queues, they are treated similarly
        print (time.asctime(), 'Accepted {0} to floor {1}'.format(uinput[0], uinput[1]))
        elevator[uinput[0] + '_queue'] = list(set(elevator[uinput[0] + '_queue']+[int(uinput[1])]))

# now start 2 threads - for user input and for state calculations
print ('start threads')
t1=threading.Thread(target=user_input)
t2=threading.Thread(target=state_calculator)
t1.start()
t2.start()

