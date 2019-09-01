#!/usr/bin/python3

import wallSunClock
import floorSunClock
import polarDiagram
from optparse import OptionParser
import sys

from dateutil import tz

# somewhere in Bochum, Germany
latitude = 51.47375
longitude = 7.32535
outpath = "test.svg"

parser = OptionParser()

parser.add_option("-w", "--wall", dest="wallclock", help="generate wallclock",action="store_true",default=False)
parser.add_option("-f", "--floor", dest="floorclock", help="generate floorclock",action="store_true",default=False)
parser.add_option("-p", "--polar", dest="polardiag", help="generate polar diagram",action="store_true",default=False)

if len(sys.argv[1:]) == 0:
    parser.print_help()
    exit(0)

(options, args) = parser.parse_args()

if options.polardiag:
    clock = polarDiagram.SunPolarDiagram(latitude, longitude)
    clock.draw_polar_diagram("polar.svg")

if options.floorclock:
    clock = floorSunClock.FloorSunClock(latitude, longitude)
    clock.draw_sun_clock("floor.svg")

if options.wallclock:
    clock = wallSunClock.WallSunClock(latitude, longitude)
    clock.draw_sun_clock("wall.svg")

