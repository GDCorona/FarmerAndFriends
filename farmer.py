from collections import deque
start = (0, 0, 0, 0)
goal = (1, 1, 1, 1)
#F: Farmer, C: Fox, G: Goose, B: Bean
def valid(state):
    F, C, G, B = state
    if C == G and F != C: #Fox eat goose
        return False
    if G == B and F != G: #Goose eat bean
        return False
    return True

def nextStates(state):
    F, C, G, B = state
    next_states = []
    moves = [
        (1,0,0,0),  # farmer
        (1,1,0,0),  # farmer + fox
        (1,0,1,0),  # farmer + goose
        (1,0,0,1)   # farmer + bean
    ]
    for move in moves:
        new = list(state) #convert to list cuz tuple cant be changed (immutable)
        if move[1] == 1 and C != F: #Fox and farmer not on the same side
            continue
        if move[2] == 1 and G != F: #Goose and farmer not on the same side
            continue
        if move[3] == 1 and B != F: #Bean and farmer not on the same side
            continue
        for i in range(4):
            new[i] = (new[i] + move[i]) % 2
        if valid(new):
            next_states.append(tuple(new)) #convert back to tuple, list cant go into set
    return next_states
def bfs():
    queue = deque([(start, [start])]) # [state: tuple, path: list of tuples]
    visited = set() #faster lookup
    while(queue):
        state, path = queue.popleft()
        if state == goal:
            return path
        if state in visited:
            continue
        visited.add(state)
        for i in nextStates(state):
            queue.append((i, path + [i]))
ans = bfs()
for step in ans:
    print(step)

"""
(0,0,0,0)
(1,0,1,0)
(0,0,1,0)
(1,1,1,0)
(0,1,0,0)
(1,1,0,1)
(0,1,0,1)
(1,1,1,1)
"""