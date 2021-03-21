import math
direction = [1,0]

def rotate(direction, angle):
    direction_matrix = [[1, 0], [0, 1], [-1, 0], [0, -1]]
    current_index = direction_matrix.index(direction)
    direction = direction_matrix[(current_index + angle) % len(direction_matrix)]
    return direction

print(rotate(direction, -4))