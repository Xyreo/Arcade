import random

win = 0
for i in range(100000):
    secret = random.randint(1, 100)
    hint = random.randint(1, 100)
    choice = -1 if hint < 50 else 1
    if hint > secret and choice == 1:
        win += 1
    elif hint < secret and choice == -1:
        win += 1

print(win)
