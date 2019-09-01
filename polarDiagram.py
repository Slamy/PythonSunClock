import pysolar
import numpy as np
import datetime
import svgwrite
import pytz

import sunClock


class SunPolarDiagram(sunClock.SunClock):

    def __init__(self, latitude, longitude):
        super().__init__(latitude, longitude)
        self.svgWidth = 1000  # cm
        self.svgHeight = 900  # cm
        self.circle_radius = 3
        self.stroke_width = 1

    def project_point_polar(self, altitude, azimuth):
        distance = 5 * (90 - altitude)
        azimuth -= 90
        x = distance * np.cos(np.deg2rad(azimuth)) + self.svgWidth / 2
        y = distance * np.sin(np.deg2rad(azimuth)) + self.svgHeight / 2
        return x, y

    def draw_polar_diagram(self, outpath):
        utc = pytz.timezone('UTC')
        # utc = pytz.timezone('Etc/GMT+4')
        now = datetime.datetime.now()

        # now = now.replace(hour=17, minute=13)

        # 31.08.2019 16:14 an der Wand 14.4°
        dwg = svgwrite.Drawing(outpath, size=[self.svgWidth, self.svgHeight])

        # First we draw a line for every month

        for month in range(1, 13):
            # 1 2 3 4 5 6 are black
            # 7 8 9 10 11 12 are red

            if month >= 7:
                stroke = "red"
            else:
                stroke = "black"

            line = svgwrite.shapes.Polyline(fill="none", stroke=stroke, stroke_width=self.stroke_width, stroke_dasharray=4)
            label_x = -1
            label_y = -1
            for hour in range(2, 23):
                for minute in range(0, 60, 15):
                    date = now.replace(month=month, day=1, hour=hour, minute=minute, second=0, tzinfo=utc)
                    sun_altitude = pysolar.solar.get_altitude(self.latitude, self.longitude, date)
                    sun_azimuth = pysolar.solar.get_azimuth(self.latitude, self.longitude, date)

                    if sun_altitude > 0:
                        x, y = self.project_point_polar(sun_altitude, sun_azimuth)

                        line.points.append([x, y])
                        label_x = x
                        label_y = y

            dwg.add(line)
            dwg.add(
                dwg.text(str(month), insert=(label_x + 2, label_y + 2), fill=stroke, font_size="4mm"))
            dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius,
                               fill=svgwrite.rgb(10, 10, 16, '%')))

        # Now over that we draw a green line for every hour.
        # As the hour doesn't change but it iterates over the course of a year it looks like an analemma.

        for hour in range(2, 23):
            # from month 1 to 6 the line is black
            line = svgwrite.shapes.Polyline(fill="none", stroke="black", stroke_width=self.stroke_width)
            label_x = -1
            label_y = -1

            for month in range(1, 13):
                for day in range(1, 31, 5):
                    try:
                        date = now.replace(month=month, day=day, hour=hour, minute=0, second=0, tzinfo=utc)

                        sun_altitude = pysolar.solar.get_altitude(self.latitude, self.longitude, date)
                        sun_azimuth = pysolar.solar.get_azimuth(self.latitude, self.longitude, date)
                        if sun_altitude > 0:
                            x, y = self.project_point_polar(sun_altitude, sun_azimuth)

                            line.points.append([x, y])
                            label_x = x
                            label_y = y

                    except ValueError:
                        # This can happen in case oh an invalid day for a month
                        pass

                    if len(line.points) > 0 and month == 7 and day == 1:
                        dwg.add(line)
                        line = svgwrite.shapes.Polyline(fill="none", stroke="red", stroke_width=self.stroke_width)
                        line.points.append([x, y])

            if len(line.points) > 0:
                dwg.add(line)
                dwg.add(
                    dwg.text(str(hour), insert=(label_x - 5, label_y - 5), fill="green", font_size="4mm"))
                dwg.add(dwg.circle(center=(label_x, label_y), r=self.circle_radius,
                                   fill="green"))

        # Now draw the current time
        date = now
        sun_azimuth, sun_altitude = pysolar.solar.get_position(self.latitude, self.longitude, date)
        if sun_altitude > 0:
            x, y = self.project_point_polar(sun_altitude, sun_azimuth)
            dwg.add(dwg.circle(center=(x, y), r=self.circle_radius, fill="red"))
        print(
            f"Now:{date} sunAltitude:{sun_altitude:.1f}° sunAzimuth:{sun_azimuth:.1f}°")

        # Draw Nodus
        dwg.add(dwg.circle(center=(self.svgWidth / 2, self.svgHeight / 2), r=self.circle_radius, fill="black"))
        dwg.save()
