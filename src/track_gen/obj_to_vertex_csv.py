import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

vertices = []

with open("tracks/monza/outside_line.obj", "r") as file:
    for line in file:
        if line.startswith("v "):
            vertex = line.split()
            x = float(vertex[1])
            y = float(vertex[2])
            z = float(vertex[3])
            vertices.append((x, y, z))

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

xs = [vertex[0] for vertex in vertices[::5]]
ys = [vertex[1] for vertex in vertices[::5]]
zs = [vertex[2] for vertex in vertices[::5]]

# Because X, Y, Z and we want to maintain Z to be "up"
ax.scatter(xs, zs, ys)

ax.set_xlabel("X")
ax.set_ylabel("Z")
ax.set_zlabel("Y")
ax.set_aspect("equal")

plt.show()
