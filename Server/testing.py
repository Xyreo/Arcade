def tell(*stuff):
    num = stuff[-1]
    n = len(stuff) - 1
    h = stuff[:n]
    plot = [(i, h[i]) for i in range(len(h))]
    if n == 3 and sum(h) % 3 == 1 and sum(h) % 3 != 0:
        plot = sorted(plot, key=lambda x: x[-1])
        return (0, 0, 0, 1, (plot[0][0], plot[1][0]))
    else:
        base = (sum(h) + num) // n
        return tuple(base - i for i in h) + ((sum(h) + num) % n,)


print(tell(1, 2, 1, 1))

"""
(1,2,1,4) - (1,0,1,2)
(1,2,2,5) - (2,1,1,1)
(1,2,2,6) - (2,1,1,2)
(1,2,3) - (2,1,0)
"""
