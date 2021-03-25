import math

def correction(angle_correction):
    angle_correction = 0.75*(-90 / math.pi) * math.atan(math.radians(angle_correction))
    return angle_correction

for i in range(-25, 25):
    print(f'{i}: {-i/3:.2f} {correction(i)}')