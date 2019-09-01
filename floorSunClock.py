import pysolar
import numpy as np
import datetime
import svgwrite
import pytz

import sunClock


class FloorSunClock(sunClock.SunClock):

    def __init__(self, latitude, longitude):
        super().__init__(latitude, longitude)
        self.svgWidth = 1100  # mm
        self.svgHeight = 900  # mm

        self.svgNodusX = self.svgWidth / 2
        self.svgNodusY = self.svgHeight / 3

        self.stickLen = 60  # in mm
        self.stroke_width = 1
        self.circle_radius = 3


    def project_floor_sunclock(self, altitude, azimuth):

        # I want to have North 0° at the top
        azimuth -= 90
        shadow_len = self.stickLen / np.tan(np.deg2rad(altitude))  # in mm

        shadow_x = shadow_len * np.cos(np.deg2rad(azimuth))
        shadow_y = shadow_len * np.sin(np.deg2rad(azimuth))
        return shadow_len, shadow_x, shadow_y

    def draw_sun_clock(self, outpath):
        utc = pytz.timezone('UTC')
        now = datetime.datetime.now()

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
                for minute in range(0, 60, 5):
                    date = now.replace(month=month, day=1, hour=hour, minute=minute, second=0, tzinfo=utc)
                    sun_azimuth, sun_altitude = pysolar.solar.get_position(self.latitude, self.longitude, date)

                    if sun_altitude > 0:
                        shadow_len, shadow_len_x, shadow_len_y = self.project_floor_sunclock(sun_altitude, sun_azimuth)

                        if 20 < shadow_len_x + self.svgNodusX < (self.svgWidth - 20):
                            line.points.append([shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY])

                            if label_x == -1:
                                label_x = shadow_len_x + self.svgNodusX
                                label_y = shadow_len_y + self.svgNodusY

            dwg.add(line)
            dwg.add(
                dwg.text(str(month), insert=(label_x + 2, label_y + 2), fill=stroke, font_size="4mm"))
            dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius, fill=stroke))

        # Now over that we draw a line for every hour

        for hour in range(2, 23):
            # from month 1 to 6 the line is black
            line = svgwrite.shapes.Polyline(fill="none", stroke="black", stroke_width=self.stroke_width)
            label_x = -1
            label_y = -1

            for month in range(1, 13):
                for day in range(1, 32, 2):
                    try:
                        # To have this complete month 0 is replaced by 12.
                        actualMonth = month if month != 0 else 12

                        date = now.replace(month=actualMonth, day=day, hour=hour, minute=0, second=0, tzinfo=utc)

                        sun_azimuth, sun_altitude = pysolar.solar.get_position(self.latitude, self.longitude, date)
                        if sun_altitude > 0:
                            shadow_len, shadow_len_x, shadow_len_y = self.project_floor_sunclock(sun_altitude,
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
                    dwg.text(str(hour), insert=(label_x - 5, label_y + 20), fill="black", font_size="4mm"))
                dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius,
                                   fill="green"))

        # Now draw the current time
        date = now
        sun_azimuth, sun_altitude = pysolar.solar.get_position(self.latitude, self.longitude, date)
        if sun_altitude > 0:
            shadow_len, shadow_len_x, shadow_len_y = self.project_floor_sunclock(sun_altitude, sun_azimuth)
            dwg.add(dwg.circle(center=(shadow_len_x + self.svgNodusX, shadow_len_y + self.svgNodusY), r=self.circle_radius,
                               fill="red"))
        print(
            f"Now:{date} sunAltitude:{sun_altitude:.1f}° sunAzimuth:{sun_azimuth:.1f}° shadowLen:{shadow_len:.1f}cm shadowLenX:{shadow_len_x:.1f}cm shadowLenY:{shadow_len_y:.1f}cm")

        # Draw Nodus
        dwg.add(dwg.circle(center=(self.svgNodusX, self.svgNodusY), r=self.circle_radius, fill="black"))

        # Draw North
        dwg.add(dwg.text("0° / N", insert=(self.svgNodusX, self.svgHeight / 10), fill="black", font_size="4mm"))
        dwg.add(dwg.line(start=(self.svgNodusX, self.svgNodusY - 10), end=(self.svgNodusX, self.svgHeight / 10 + 10),
                         stroke_width=self.stroke_width, stroke="black"))

        dwg.save()
