import sys
import shutil
import datetime

for arg in sys.argv[1:]:
    print(arg)

today = datetime.date.today()
yesterday = datetime.date.fromordinal(today.toordinal() - 1)
tomorrow = datetime.date.fromordinal(today.toordinal() + 1)

print(today)
print(yesterday)
print(tomorrow)

# TODO: TEMP
tmp = input('Please enter "XY"')
# "Y" for Yesterday
# "T" for Today
# "M" for Tomorrow

# "C" for Contents
# "F" for Ford BoL
# "M" for Maple BoL
# "I" for Invoice