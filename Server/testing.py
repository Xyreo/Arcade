class Peasant:
    def __init__(self):
        self.name = "Hello"

    def delete(self):
        print("del")


l = []
l2 = []
p = Peasant()
l.append(p)
l2.append(p)
print(l)
del p
print(l, l2)
print(l[0].name)
