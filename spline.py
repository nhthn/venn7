import math

class Spline:

    def __init__(self, x_1, y_1, x_2, y_2, theta_1, theta_2, tension_1=1.0, tension_2=1.0):
        self.x_1, self.y_1 = x_1, y_1
        self.x_2, self.y_2 = x_2, y_2

        base_angle = math.atan2(self.y_2 - self.y_1, self.x_2 - self.x_1)
        self.theta_1, self.theta_2 = theta_1 - base_angle, base_angle - theta_2
        self.tension_1, self.tension_2 = tension_1, tension_2

        a = math.sqrt(2)
        b = 1 / 16
        c = (3 - math.sqrt(5)) / 2
        alpha = (
            a
            * (math.sin(self.theta_1) - b * math.sin(self.theta_2))
            * (math.sin(self.theta_2) - b * math.sin(self.theta_1))
            * (math.cos(self.theta_1) - math.cos(self.theta_2))
        )
        self.rho = (2 + alpha) / (1 + (1 - c) * math.cos(self.theta_1) + c * math.cos(self.theta_2))
        self.sigma = (2 - alpha) / (1 + (1 - c) * math.cos(self.theta_2) + c * math.cos(self.theta_1))

    def curve(self, t):
        x_hat = (
            self.rho / self.tension_1 * t * (1 - t) * (1 - t) * math.cos(self.theta_1)
            + t * t * (1 - t) * (3 - self.sigma * math.cos(self.theta_2) / self.tension_2)
            + t * t * t
        )
        y_hat = (
            self.rho / self.tension_1 * t * (1 - t) * (1 - t) * math.sin(self.theta_1)
            + t * t * (1 - t) * self.sigma * math.sin(self.theta_2) / self.tension_2
        )
        x = self.x_1 + (self.x_2 - self.x_1) * x_hat + (self.y_1 - self.y_2) * y_hat
        y = self.y_1 + (self.y_2 - self.y_1) * x_hat + (self.x_2 - self.x_1) * y_hat
        return (x, y)

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    spline = Spline(
        x_1=0.0,
        y_1=0.0,
        x_2=0.0,
        y_2=1.0,
        theta_1=0.0,
        theta_2=math.pi * 0.25,
    )
    points = [spline.curve(i / 100) for i in range(100 + 1)]
    plt.scatter(*zip(*points))
    plt.show()
