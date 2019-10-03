#!/usr/bin/python
#
# reference rstats.c TomatoUsb source code
#
#
#    Copyright (C) 2010 - 2015 VREM Software Development <VREMSoftwareDevelopment@gmail.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

from datetime import date
from optparse import OptionParser
from os.path import isfile, exists
from collections import namedtuple
import traceback
import gzip
import struct
import sys

from charts import get_size
from charts import create_daily_bar_chart
from charts import create_monthly_usage_chart


# rstats supports version ID_V1
class RStats:
    # expected file size in bytes
    EXPECTED_SIZE = 2112
    # version 0 has 12 entries per month
    ID_V0 = 0x30305352
    # version1 has 25 entries per month
    ID_V1 = 0x31305352

    MONTH_COUNT = 25
    DAY_COUNT = 62

    RESULTS = {'MONTHS': [], 'DAYS': []}

    def __init__(self, filename):
        try:
            print(">>>>>>>>>> Tomato USB RSTATS <<<<<<<<<<")
            with gzip.open(filename, 'rb') as fileHandle:
                self.file_content = fileHandle.read()
            if len(self.file_content) != self.EXPECTED_SIZE:
                print("Unsupported File Format. Require unzip file size: {0}.".format(self.EXPECTED_SIZE))
                sys.exit(2)
            print("Supported File Format Version: {0}".format(self.ID_V1))
            self.index = 0
        except IOError:
            sys.stderr.write("Can NOT read file: "+filename)
            traceback.print_exc()

    def dump(self):
        version = self.unpack_value("Q", 8)
        print("Version: {0}".format(version))
        if version != RStats.ID_V1:
            sys.stderr.write("Unknown version number: {0}\n".format(version))
            sys.exit(2)

        print("---------- Daily ----------")
        self.RESULTS['DAYS'] = self.dump_stats(self.DAY_COUNT)
        print("dailyp: {0}".format(self.unpack_value("q", 8)))

        print("---------- Monthly ----------")
        self.RESULTS['MONTHS'] = self.dump_stats(self.MONTH_COUNT)
        print("monthlyp: {0}".format(self.unpack_value("q", 8)))
        # check if all bytes are read
        if self.index != self.EXPECTED_SIZE:
            print(">>> Warning!")
            print("Read {0} bytes.".format(self.index))
            print("Expected to read {0} bytes.".format(self.EXPECTED_SIZE))
            print("Left to read {0} bytes".format(self.EXPECTED_SIZE - self.index))
        return self.RESULTS

    def dump_stats(self, size):
        # highlight download usage with a horizontal bar chart
        output = {"x_labels": [], "y_labels": [], "y": []}
        for i in range(size):
            time = self.get_date(self.unpack_value("Q", 8)).strftime("%Y/%m/%d")
            down_val = self.unpack_value("Q", 8)
            up_val = self.unpack_value("Q", 8)
            down = get_size(num=down_val)
            up = get_size(num=up_val)
            # by default limit to the last 30 days
            if not str(time).startswith('1900'):
                print("Date: {0}, Down: {1}, Up: {2}".format(time, down, up))
                output["y_labels"].append(time)
                output["x_labels"].append(down)
                output["y"].append(down_val)
        return output

    def unpack_value(self, unpack_type, size):
        current = self.index
        self.index += size
        if self.index > self.EXPECTED_SIZE:
            sys.stderr.write("Reached end of the buffer. {0}/{1}".format(self.index, self.EXPECTED_SIZE))
            exit(3)
        value, = struct.unpack(unpack_type, self.file_content[current:self.index])
        return value

    @staticmethod
    def get_date(time):
        year = ((time >> 16) & 0xFF) + 1900
        month = ((time >> 8) & 0xFF) + 1
        day = time & 0xFF
        return date(year, month, 1 if day == 0 else day)


def main():
    usage = "./rstats.py <-i|--input=filename> [-c|--chart=filename]"
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--input", dest="input", action="store",
                      help="input rstats/cstats gzip", metavar="filename")
    parser.add_option("-c", "--chart", action="store_true", dest="chart", default=False,
                      help="export to .png usage chart [optional]")
    options, args = parser.parse_args()

    if options.input is not None and isfile(options.input) and options.chart is True:
        dump = RStats(options.input).dump()
        create_daily_bar_chart(dump)
        create_monthly_usage_chart(dump)
    elif options.input is not None and isfile(options.input):
        dump = RStats(options.input).dump()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
