import pysolar
import numpy as np
import datetime
import svgwrite
import pytz

import sunClock

class WallSunClock(sunClock.SunClock):

    def __init__(self, latitude, longitude):
        super().__init__(latitude, longitude)
        self.svgWidth = 1100  # cm
        self.svgHeight = 700  # cm

        self.svgNodusX = self.svgWidth / 2
        self.svgNodusY = self.svgHeight / 2

        self.stickLen = 170  # in cm, wasserwaage

        self.stroke_width = 1

        self.wallAngle = 157  # in °, Bochum
        # wallAngle = 90 # in °, perfekte Südwand

        self.circle_radius = 3

    def project_wall_sun_clock(self, altitude, azimuth):
        shadow_len_y = self.stickLen * np.tan(np.deg2rad(altitude))  # in cm
        shadow_len_x = -self.stickLen / np.tan(np.deg2rad(azimuth - self.wallAngle))

        shadow_len = np.sqrt(shadow_len_x * shadow_len_x + shadow_len_y * shadow_len_y)
        shadow_angle = np.rad2deg(np.arctan(shadow_len_x / shadow_len_y))
        return shadow_len, shadow_angle, shadow_len_x, shadow_len_y

    def draw_sun_clock(self, outpath):
        tz = pytz.timezone('Europe/Berlin')
        now = datetime.datetime.now()

        # now = now.replace(hour=17, minute=13)

        # 31.08.2019 16:14 an der Wand 14.4°
        dwg = svgwrite.Drawing(outpath, size=[self.svgWidth, self.svgHeight])

        # First we draw a line for every month

        for month in range(1, 13):
            # 1 2 3 4 5 6 are black
            # 7 8 9 10 11 12 are red
            stroke = "red" if month >= 7 else "black"

            line = svgwrite.shapes.Polyline(fill="none", stroke=stroke, stroke_width=self.stroke_width, stroke_dasharray=4)
            label_x = -1
            label_y = -1
            for hour in range(2, 23):
                for minute in range(0, 60, 15):
                    date = now.replace(month=month, day=1, hour=hour, minute=minute, second=0, tzinfo=tz)
                    sun_altitude = pysolar.solar.get_altitude(self.latitude, self.longitude, date)
                    sun_azimuth = pysolar.solar.get_azimuth(self.latitude, self.longitude, date)

                    # Backface culling lol
                    if sun_azimuth > self.wallAngle and sun_azimuth - self.wallAngle < 180:
                        shadow_len, shadow_angle, shadow_len_x, shadow_len_y = self.project_wall_sun_clock(sun_altitude,
                                                                                                           sun_azimuth)
                        if 10 < shadow_len_x + self.svgNodusX < self.svgWidth - 10:
                            line.points.append([shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY])
                            label_x = shadow_len_x + self.svgNodusX
                            label_y = shadow_len_y + self.svgNodusY

            dwg.add(line)
            dwg.add(
                dwg.text(str(month), insert=(label_x + 2, label_y + 2), fill=stroke, font_size="4mm"))
            dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius,
                               fill=stroke))

        # Now over that we draw a line for every hour
        for hour in range(2, 23):
            # from month 1 to 6 the line is black
            line = svgwrite.shapes.Polyline(fill="none", stroke="black", stroke_width=self.stroke_width)
            label_x = -1
            label_y = -1

            for month in range(1, 13):
                for day in range(1, 31, 5):
                    try:
                        date = now.replace(month=month, day=day, hour=hour, minute=0, second=0, tzinfo=tz)
                        sun_altitude = pysolar.solar.get_altitude(self.latitude, self.longitude, date)
                        sun_azimuth = pysolar.solar.get_azimuth(self.latitude, self.longitude, date)

                        if sun_azimuth > self.wallAngle and sun_azimuth - self.wallAngle < 180:
                            shadow_len, shadow_angle, shadow_len_x, shadow_len_y = self.project_wall_sun_clock(
                                sun_altitude,
                                sun_azimuth)

                            if 0 < shadow_len_x + self.svgNodusX < self.svgWidth:
                                line.points.append([shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY])
                                label_x = shadow_len_x + self.svgNodusX
                                label_y = shadow_len_y + self.svgNodusY

                    except ValueError:
                        # This can happen in case oh an invalid day for a month
                        pass

                    if len(line.points) > 0 and month == 7 and day == 1:
                        dwg.add(line)
                        line = svgwrite.shapes.Polyline(fill="none", stroke="red", stroke_width=self.stroke_width)
                        line.points.append([shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY])

            if len(line.points) > 0:
                dwg.add(line)
                dwg.add(
                    dwg.text(str(hour), insert=(label_x - 10, label_y - 10), fill="green", font_size="4mm"))
                dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius,
                                   fill="green"))

        # Now draw the current time
        date = now
        sun_azimuth, sun_altitude = pysolar.solar.get_position(self.latitude, self.longitude, date)
        if sun_altitude > 0:
            shadow_len, shadow_angle, shadow_len_x, shadow_len_y = self.project_wall_sun_clock(sun_altitude, sun_azimuth)
            dwg.add(dwg.circle(center=(shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY), r=self.circle_radius,
                           fill="red"))
        print(f"Now:{date} sunAltitude:{sun_altitude:.1f}° sun_azimuth:{sun_azimuth:.1f}° "
              f"shadowLen:{shadow_len:.1f}cm shadowAngle:{shadow_angle:.1f}° "
              f"shadowLenX:{shadow_len_x:.1f}cm shadowLenY:{shadow_len_y:.1f}cm")

        # Draw Nodus
        dwg.add(dwg.circle(center=(self.svgNodusX, self.svgNodusY), r=self.circle_radius, fill="black"))
        dwg.save()
