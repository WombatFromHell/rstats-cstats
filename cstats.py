#!/usr/bin/python
#
# reference cstats.h and cstats.c TomatoUsb source code
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
import traceback
import gzip
import struct
import sys


class CStats(object):
    ID_V0 = 0x30305352
    ID_V1 = 0x31305352
    ID_V2 = 0x32305352
    MONTH_COUNT = 25
    DAY_COUNT = 62
    # expected record size in bytes
    RECORD_SIZE = 13688
    # collect RX and TX every 2 minutes per day
    PER_MINUTE = 2
    HOURS = 24
    MINUTES = 60
    MAX_SPEED = HOURS * MINUTES / PER_MINUTE

    def __init__(self, filename):
        try:
            print(">>>>>>>>>> Tomato USB CSTATS <<<<<<<<<<")
            with gzip.open(filename, 'rb') as fileHandle:
                self.fileContent = fileHandle.read()
            self.index = 0
            self.size = len(self.fileContent)
            self.records = self.size / CStats.RECORD_SIZE
            print("File size: {0}".format(self.size))
            print("Number of records: {0}".format(self.records))
        except IOError:
            sys.stderr.write("Can NOT read file: "+filename)
            traceback.print_exc()

    def dump(self):
        for i in range(self.records):
            print("Record Number:{0}".format(i))
            self.dump_record()

        # check if all bytes are read
        if self.index == self.size:
            print("All bytes read")
        else:
            print(">>> Warning!")
            print("Read {0} bytes.".format(self.index))
            print("Expected to read {0} bytes.".format(self.size))
            print("Left to read {0} bytes".format(self.size - self.index))

    def dump_record(self):
        current = self.index

        print("========== IP Address: {0} ==========".format(self.get_value(16)))
        version = self.unpack_value("Q", 8)
        print("Version {0}".format(version))
        if version == CStats.ID_V0:
            print("Version ID_V0")
        elif version == CStats.ID_V1:
            print("Version ID_V1")
        elif version == CStats.ID_V2:
            print("Version ID_V2")
        else:
            print("Version UNKNOWN")

        print("---------- Daily ----------")
        self.dump_stats(CStats.DAY_COUNT)
        print("dailyp: {0}".format(self.unpack_value("q", 8)))

        print("---------- Monthly ----------")
        self.dump_stats(CStats.MONTH_COUNT)
        print("monthlyp: {0}".format(self.unpack_value("q", 8)))

        print("utime: {0}".format(self.unpack_value("q", 8)))
        print("tail: {0}".format(self.unpack_value("q", 8)))

        print("---------- RX/TX Speed ----------")
        self.dump_speed(CStats.MAX_SPEED)
        print("last1: {0}".format(self.unpack_value("Q", 8)))
        print("last2: {0}".format(self.unpack_value("Q", 8)))
        print("sync: {0}".format(self.unpack_value("q", 8)))

        # check if all record bytes are read
        if current + CStats.RECORD_SIZE == self.index:
            print("All record bytes read")
        else:
            print(">>> Warning!")
            print("Read {0} bytes.".format(self.index - current))
            print("Expected to read {0} bytes.".format(CStats.RECORD_SIZE))
            print("Left to read {0} bytes".format(self.index - current - CStats.RECORD_SIZE))

    def dump_speed(self, size):
        print("Time,RX bytes,TX bytes")
        for i in range(size):
            rx = self.unpack_value("Q", 8)
            tx = self.unpack_value("Q", 8)
            time = i * CStats.PER_MINUTE
            print("{0:02d}:{1:02d},{2},{3}".format(time / CStats.MINUTES, time % CStats.MINUTES, rx, tx))

    def dump_stats(self, size):
        for i in range(size):
            time = self.get_date(self.unpack_value("Q", 8)).strftime("%Y/%m/%d")
            down = self.get_size(self.unpack_value("Q", 8))
            up = self.get_size(self.unpack_value("Q", 8))
            if not str(time).startswith('1900'):
                print("Date: {0}, Down: {1}, Up: {2}".format(time, down, up))

    def get_size(self, num, suffix='B'):
        # https://stackoverflow.com/a/1094933
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def unpack_value(self, unpack_type, size):
        value, = struct.unpack(unpack_type, self.get_value(size))
        return value

    def get_value(self, size):
        current = self.index
        self.index += size
        if self.index > self.size:
            sys.stderr.write("Reached end of the buffer. Calculated:{0} Maximum:{1}".format(self.index, self.size))
            exit(3)
        value = self.fileContent[current:self.index]
        return value

    @staticmethod
    def get_date(time):
        year = ((time >> 16) & 0xFF) + 1900
        month = ((time >> 8) & 0xFF) + 1
        day = time & 0xFF
        return date(year, month, 1 if day == 0 else day)


def main():
    import optparse
    from os.path import isfile

    usage = "usage: %prog <filename>"
    parser = optparse.OptionParser(usage)

    options, args = parser.parse_args()

    if len(args) == 1 and isfile(args[0]):
        CStats(args[0]).dump()
    else:
        print(usage)
        sys.exit(1)

if __name__ == "__main__":
    main()
