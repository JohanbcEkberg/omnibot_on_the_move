# import json
# import matplotlib.pyplot as plt

# f1 = open("traj.json")
# traj = json.load(f1)

# f2 = open("actual_trajectory.json")
# act_traj = json.load(f2)

# positions = traj["q"]  # [[x, y, theta], ...]
# actual_positions = [act_traj["q"]]

# x1 = [p[0] for p in positions]
# y1 = [p[1] for p in positions]


# x2 = [p[0] for p in actual_positions]
# y2 = [p[1] for p in actual_positions]

# plt.figure()
# plt.plot(x1, y1, label="Planned trajectory")
# plt.scatter(x1[0], y1[0], label="start")
# plt.scatter(x1[-1], y1[-1], label="end")

# plt.plot()

# plt.axis("equal")
# plt.grid()
# plt.legend()
# plt.xlabel("x (m)")
# plt.ylabel("y (m)")
# plt.title("Trajectory")
# plt.show()

import json
import matplotlib.pyplot as plt


def load(path):
    with open(path, "r") as f:
        data = json.load(f)

    # supports either raw list OR {"q": [...]}
    if isinstance(data, dict):
        data = data.get("q", [])

    return data


def xy(traj):
    return [p[0] for p in traj], [p[1] for p in traj]


def plot(planned_path, actual_path):
    planned = load(planned_path)
    actual = load(actual_path)

    plt.figure()

    if planned:
        xp, yp = xy(planned)
        plt.plot(xp, yp, "--", label="planned")
        plt.scatter(xp[0], yp[0], label="start planned")

    if actual:
        xa, ya = xy(actual)
        plt.plot(xa, ya, label="actual")
        plt.scatter(xa[0], ya[0], label="start actual")

    plt.title("Planned vs Actual Trajectory")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.grid(True)
    plt.legend()

    plt.show()


if __name__ == "__main__":
    plot("traj.json", "actual_traj.json")