import re
from math import ceil
from datetime import datetime, date, time, timedelta
from calendar import day_name, day_abbr

def parse_time(timestr):
    hms_re = re.compile(r"(\d+)h\w*\,?(\d+)m\w*\,?(\d+)s\w*")
    ms_re = re.compile(r"(\d+)h\w*\,?(\d+)m\w*")
    hm_re = re.compile(r"(\d+)m\w*\,?(\d+)s\w*")
    hours = 0.0
    minutes = 0.0
    seconds = 0.0
    if 0 < timestr.count(':') < 2:
        #form of N:N:N
        time_pieces = timestr.split(':')
        if len(time_pieces) < 3:
            time_pieces.append('0')
    else:
        #raw number only
        try:
            no_unit = float(timestr)
            hours = True
            if no_unit > 14:
                hours = False
            if no_unit == 24:
                hours = True
            if hours:
                return round(no_unit * 60)
            else:
                return ceil(no_unit)
        except:
            #form of NhNmNs, N minutes N seconds, etc
            timestr = timestr.replace(' ','')
            hms = hms_re.search(timestr)
            if hms:
                time_pieces = hms[1:]
            else:
                hm = hm_re.search(timestr)
                if hm:
                    time_pieces = hm[1:]
                    time_pieces.append('0')
                else:
                    ms = ms.re.search(timestr)
                    if ms:
                        time_pieces = ['0']
                        time_pieces.extend(ms[1:])
                    else:
                        return None
        return round(time_pieces[0] * 60) +\
                ceil(time_pieces[1] + (time_pieces[2] / 60.0))

def parse_date(datestr):
    date_obj = None
    try:
        date_obj = date.fromordinal(int(datestr))
    except:
        try:
            date_obj = date.fromtimestamp(float(datestr))
        except:
            try:
                date_obj = date.fromisoformat(datestr)
            except:
                pass
    if date_obj is None:
        common_stamps = [
            "%x",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%m/%d",
            "%m-%d-%Y",
            "%m-%d-%y",
            "%m-%d",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%B %d",
            "%d %B %Y",
            "%d %B",
            "%d-%B-%Y",
            "%d-%B-%y",
            "%b %d, %Y",
            "%b %d",
            "%d %b %Y",
            "%d %b",
            "%d-%b-%Y",
            "%d-%b-%y",
            "%B %d",
            "%b %d",
            "%Y%m%d"]
        no_month = False
        for stamp in common_stamps:
            try:
                date_obj = datetime.strptime(datestr,stamp).date()
                break
            except:
                pass
            no_month = True
        if no_month:
            datestr = datestr.replace(" the ","").replace("the ","")
            for day in day_name:
                if datestr.strip().lower() in [f"this {day}".lower(),
                                            f"this coming {day}".lower()]:
                    pass
                    #next occurrence of day
                elif datestr.strip().lower() == f"next {day}".lower():
                    pass
                    #next occurrence on or after next monday
                elif datestr.strip().lower() == f"{day} after next".lower():
                    pass
                    #7 days after next occurrence of day

def parse_ts(timestr):
    pass

class Settings:
    def __init__(self):
        pass

#entry keys [name, duration, priority]
class Schedule:
    def __init__(self,settings):
        self.entries = []
        self.settings = settings
        self.max_priority = settings.max_priority
        self.appointments = []

    def request_and_parse(self):
        valid = False
        first_run = True
        this_entry = {}
        while not valid:
            if not first_run:
                print("Error! Please try again.")
            first_run = False
            print("New entry in the form:")
            print("  priority (1-{self.max_priority}), expected duration, name")
            raw_entry = input("What's the entry? ")
            entry_pieces = raw_entry.split(',')
            try:
                this_entry['priority'] = int(entry_pieces[0])
                if this_entry['priority'] > self.max_priority:
                    continue
            except:
                continue
            this_entry['duration'] = parse_time(entry_pieces[1])
            if this_entry['duration'] == None:
                #parser will return None for unparseable strings
                continue
            if len(entry_pieces[2].strip()) < 2:
                #too short
                continue
            this_entry['name'] = entry_pieces[2].strip()
            valid = True
        self.entries.append(this_entry)

    def add_appointment(self):
        valid = False
        first_run = True
        this_app = {}
        while not valid:
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_date = input("What is the date? ")
            parsed_date = parse_date(app_date)
            if parsed_date is None:
                continue
            if datetime.now() - parsed_date > 0:
                continue
            valid = True
        valid = False
        first_run = True
        while not valid:
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_time = input("What is the start time? ")
            parsed_time = parse_ts(app_time)
            if parsed_time is None:
                continue
            app_datetime_obj = datetime.combine(parsed_date,parsed_time)
            if datetime.now() - app_datetime_obj > 0:
                continue
            valid = True
        valid = False
        first_run = True
        while not valid:
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_duration = input("How long does this event last? ")
            parsed_dur = parse_time(app_duration)
            if parsed_dur is None:
                continue
            app_datetime_end = app_datetime_obj + timedelta(minutes=parsed_dur)
            valid = True
        self.appointments.append([app_datetime_obj,app_datetime_end])

    def prioritize(self):
        #re-order by priority AND raise issue if schedule exceeds available
        # resources
        pass
