import re
import yaml
from math import ceil
from datetime import datetime, date, time, timedelta
from calendar import day_name, day_abbr

def parse_time(timestr):
    hms_re = re.compile(r"(\d+)h\,?(\d+)m\,?(\d+)s")
    hm_re = re.compile(r"(\d+)h\,?(\d+)m")
    ms_re = re.compile(r"(\d+)m\,?(\d+)s")
    hours = 0.0
    minutes = 0.0
    seconds = 0.0
    time_pieces = []
    timestr = timestr.replace('hours','h').replace('hour','h')
    timestr = timestr.replace('hrs','h').replace('hr','h')
    timestr = timestr.replace('minutes','m').replace('minute','m')
    timestr = timestr.replace('mins','m').replace('min','m')
    timestr = timestr.replace('seconds','s').replace('second','s')
    timestr = timestr.replace('secs','s').replace('sec','s')
    timestr = timestr.replace(' ','')
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
            print(timestr)
            hms = hms_re.search(timestr)
            if hms:
                time_pieces = hms[1:]
            else:
                print("hm")
                hm = hm_re.search(timestr)
                print(hm)
                if hm and len(hm.groups()) > 1:
                    print(hm.groups())
                    time_pieces = list(hm.groups())
                    time_pieces.append('0')
                else:
                    print("ms")
                    ms = ms_re.search(timestr)
                    if ms and len(ms.groups()) > 1:
                        time_pieces = ['0']
                        time_pieces.extend(list(ms.groups()))
            if not time_pieces:
                print('notp')
                hrsplit = timestr.split('h',1)
                if len(hrsplit) == 2:
                    time_pieces.append(int(hrsplit[0]))
                    rest = hrsplit[1]
                else:
                    time_pieces.append(0)
                    rest = hrsplit[0]
                minsplit = rest.split('m',1)
                if len(minsplit) == 2:
                    time_pieces.append(int(minsplit[0]))
                    rest = minsplit[1]
                else:
                    time_pieces.append(0)
                    rest = minsplit[0]
                if rest.endswith('s'):
                    time_pieces.append(int(rest[:-1]))
                else:
                    time_pieces.append(0)
        time_pieces = [int(t) for t in time_pieces]
        print('tp',time_pieces)
        return round(time_pieces[0] * 60) +\
                ceil(time_pieces[1] + (time_pieces[2] / 60.0))

def parse_date(datestr):
    date_obj = None
    try:
        date_obj = date.fromordinal(int(datestr))
        print('a')
    except:
        try:
            date_obj = date.fromtimestamp(float(datestr))
            print('b')
        except:
            try:
                date_obj = date.fromisoformat(datestr)
                print('c')
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
            print(stamp)
            try:
                date_obj = datetime.strptime(datestr,stamp).date()
                break
            except:
                pass
            no_month = True
        if no_month:
            print('d')
            if datestr == 'today':
                return datetime.now().date()
            elif datestr == 'tomorrow' or datestr == 'tmrw':
                return (datetime.now() + timedelta(days=1)).date()
            elif datestr == 'day after tomorrow' or \
                    datestr == 'day after tmrw':
                return (datetime.now() + timedelta(days=2)).date()
            datestr = datestr.replace(" the ","").replace("the ","")
            weekday_today = datetime.now().weekday()
            for i in range(len(day_name)):
                for day in [day_name[i],day_abbr[i]]:
                    if datestr.strip().lower() in [f"this {day}".lower(),
                                                f"this coming {day}".lower()]:
                        #next occurrence of day
                        if i > weekday_today:
                            t_delta = timedelta(days=(i-weekday_today))
                        else:
                            t_delta = timedelta(days=(7+i-weekday_today))
                        date_obj = (datetime.now() + t_delta).date()
                        break
                    elif datestr.strip().lower() == f"next {day}".lower():
                        #next occurrence on or after next monday
                        coming_monday = datetime.now() + timedelta(days=(7-weekday_today))
                        date_obj = (coming_monday + timedelta(days=i)).date()
                        break
                    elif datestr.strip().lower() == f"{day} after next".lower():
                        #occurrence after (next occurrence on or after next mo)
                        coming_monday = datetime.now() + timedelta(days=(7-weekday_today))
                        date_obj = (coming_monday + timedelta(days=7+i)).date()
                        break
    print('return',date_obj)
    return date_obj

def parse_ts(timestr):
    time_obj = None
    try:
        time_obj = time.fromisoformat(int(timestr))
    except:
        timestr = timestr.lower()
        timestr = timestr.replace('.m.','m')
        if timestr.endswith('p') or timestr.endswith('a'):
            timestr = timestr.replace(' ','')+'m'
        common_stamps = [
            "%H%M%S",
            "%H%M",
            "%I%p",
            "%I %p",
            "%I:%M%p",
            "%I:%M %p",
        ]
        for stamp in common_stamps:
            try:
                time_obj = datetime.strptime(timestr,stamp).time()
                break
            except:
                pass
    return time_obj

class Settings:
    def __init__(self):
        self.max_priority = 3
        pass

#entry keys [name, duration, priority]
class TaskList:
    def __init__(self,settings):
        self.settings = settings
        self.max_priority = settings.max_priority
        self.entries = []
        self.appointments = []

    def add_task_item(self):
        valid = False
        first_run = True
        this_entry = {}
        while not valid:
            if not first_run:
                print("Error! Please try again.")
            first_run = False
            task_name = input("What is the task? ")
            ex_duration = input("What is the expected duration? ")
            priority = input(f"What is the priority (1-{self.max_priority})? ")
            try:
                this_entry['priority'] = int(priority)
                if this_entry['priority'] > self.max_priority:
                    continue
            except:
                continue
            this_entry['duration'] = parse_time(ex_duration)
            if this_entry['duration'] == None:
                #parser will return None for unparseable strings
                continue
            if len(task_name.strip()) < 2:
                #too short
                continue
            this_entry['name'] = task_name.strip()
            valid = True
        self.entries.append(this_entry)

    def add_appointment(self):
        appt_name = input("What is the appointment? ").strip()
        valid = False
        first_run = True
        this_app = {}
        while not valid:
            print("date")
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_date = input("What is the date? ")
            parsed_date = parse_date(app_date)
            print('aaaaaaaugh')
            if parsed_date is None:
                print('nooooone')
                continue
            if datetime.now() > datetime.combine(parsed_date,time(23,59,59)):
                print('negative')
                continue
            print(valid)
            valid = True
        print(parsed_date)
        valid = False
        first_run = True
        while not valid:
            print("time")
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_time = input("What is the start time? ")
            parsed_time = parse_ts(app_time)
            if parsed_time is None:
                continue
            app_datetime_obj = datetime.combine(parsed_date,parsed_time)
            if datetime.now() > app_datetime_obj:
                continue
            valid = True
        valid = False
        first_run = True
        while not valid:
            print("dur")
            if not first_run:
                print("Error! Please try again!")
            first_run = False
            app_duration = input("How long does this event last? ")
            parsed_dur = parse_time(app_duration)
            if parsed_dur is None:
                continue
            app_datetime_end = app_datetime_obj + timedelta(minutes=parsed_dur)
            valid = True
        self.appointments.append(
            {
                "name": appt_name,
                "start": app_datetime_obj.isoformat(),
                "end": app_datetime_end.isoformat()
            })

    def prioritize(self):
        #re-order by priority AND raise issue if schedule exceeds available
        # resources
        pass

if __name__ == '__main__':
    sch = TaskList(Settings())
    resp = -1
    while resp != 0:
        try:
            resp = int(input("Enter 1 for tasks, 2 for appointments: "))
            if resp == 1:
                sch.add_task_item()
            elif resp == 2:
                sch.add_appointment()
        except Exception as e:
            #raise e
            print('exception',e)
            continue
    print('entries',sch.entries)
    print('appts',sch.appointments)
    out_dict = {"tasks": sch.entries, "appointments":sch.appointments}
    with open('newtasks.yaml','w') as stream:
        yaml.safe_dump(out_dict,stream)