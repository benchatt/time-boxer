from datetime import date, time, datetime, timedelta
from copy import deepcopy as copy
import yaml
import random

WORK_STYLE_DEFAULTS = {
    "week_start": 0,
    "week_end": 5,
    "weekend_blocks": [[1000,1400]],
    "work_blocks": [[900,1700]],
    "afterhours_blocks":[[600,800],[2000,2200]],
    "timebox_dur": 25,
    "break_dur": 5,
    "hi_priorities": [1],
    "hipri_cutoff": 17,
    "sameness": 0.75,
    "randomness": 0.1
}

class Schedule:
    def __init__(self,workstyle={}):
        self.workstyle = workstyle
        self.variances = {}
        self.all_entries = {}
        for k in WORK_STYLE_DEFAULTS.keys():
            if k not in self.workstyle.keys():
                self.workstyle[k] = WORK_STYLE_DEFAULTS[k]
        try:
            with open('newtasks.yaml') as stream:
                task_list = yaml.safe_load(stream)
        except:
            pass
        self.insert_appointments(task_list['appointments'])
        self.insert_tasks(task_list['tasks'])

    def entry_can_fit(self,start=None,end=None):
        if start is None or end is None:
            return False
        for entry_start, entry in self.all_entries.items():
            if entry_start < start < entry['end']:
                return False
            if entry_start < end < entry['end']:
                return False
        return True 

    def change_per_day_of_week(self,weekday,**kwargs):
        self.variances[f'w{weekday}'] = kwargs

    def change_per_day_of_month(self,monthday,**kwargs):
        self.variances[f'm{monthday}'] = kwargs
    
    def change_per_date(self,isodate,**kwargs):
        self.variances[f'd{isodate}'] = kwargs
    
    def out_of_variance(self,start_time: datetime,end_time: datetime):
        now = datetime.now()
        for varkey,variance in self.variances.items():
            hit = False
            if varkey.startswith('w'):
                if int(varkey[1:]) in (start_time.weekday,end_time.weekday):
                    hit = True
            elif varkey.startswith('m'):
                if int(varkey[1:]) in (start_time.day,end_time.day):
                    hit = True
            elif varkey.startswith('d'):
                if start_time < datetime.fromisoformat(varkey[1:]) < end_time:
                    hit = True
            if hit:
                if 'busy' in variance.keys():
                    busy_start = datetime.combine(now.date,variance['busy'][0])
                    busy_end = datetime.combine(now.date,variance['busy'][1])
                    if busy_start < start_time < busy_end or \
                        busy_start < end_time < busy_end:
                        return False
        return True

    def get_variance_adds(self):
        pass
        #return list of blocks added by additive variances

    def get_freeblocks(self,secondary=False):
        break_time = timedelta(minutes=self.workstyle['break_dur'])
        box_time = timedelta(minutes=self.workstyle['timebox_dur'])
        cycle_time = box_time+break_time
        rn = datetime.now()
        is_weekday = rn.weekday() in range(self.workstyle['week_start'],self.workstyle['week_end']+1)
        if secondary:
            if is_weekday:
                block_ranges = self.workstyle['afterhours_blocks']
            else:
                return None
                #shouldn't have secondaries on the weekend
        else:
            if is_weekday:
                block_ranges = self.workstyle['work_blocks']
            else:
                block_ranges = self.workstyle['weekend_blocks']
        accepted_blocks = []
        for block_range in block_ranges:
            for start_time_num in range(*block_range,cycle_time.seconds//60):
                start_time_obj = datetime.strptime(str(start_time_num),'%H%M').time()
                start_time = datetime.combine(date.today(),start_time_obj)
                end_time = start_time + cycle_time
                break_spot = end_time - break_time
                if not self.entry_can_fit(start_time,end_time) or not self.out_of_variance(start_time,end_time):
                    sweep_range = range(start_time_num,start_time_num+cycle_time.seconds//60,10)
                    for sweep_start_num in sweep_range:
                        start_time_obj = datetime.strptime(str(sweep_start_num),'%H%M').time()
                        start_time = datetime.combine(date.today(),start_time_obj)
                        end_time = start_time + cycle_time
                        if self.entry_can_fit(start_time,end_time):
                            accepted_blocks.append({'start':start_time.isoformat(),
                                                    'break':break_spot.isoformat(),
                                                    'end':end_time.isoformat()})
                            break
                else:
                    accepted_blocks.append({'start':start_time.isoformat(),
                                            'break':break_spot.isoformat(),
                                            'end':end_time.isoformat()})
        return accepted_blocks
    
    def assign_block(self, task, block):
        self.all_entries[block['start']] = {
            'name': task['name'],
            'break': block['break'],
            'end': block['end'],
            'type': 'work_block'
        }

    def insert_appointments(self,appointments):
        #appointments don't care about your silly variances
        for appt in appointments:
            appt_dt_obj = datetime.fromisoformat(appt['start'])
            appt_dt_end = datetime.fromisoformat(appt['end'])
            if appt_dt_obj < datetime.now():
                print(f"Entry {appt['name']} is expired.")
            if not self.entry_can_fit(appt_dt_obj,appt_dt_end):
                print(f"Entry {appt['name']} doesn't fit.")
            self.all_entries[appt['start']] = {
                'name':appt['name'],
                'end': appt['end'],
                'type':'appt'}

    def insert_tasks(self,tasks):
        tasks = sorted(tasks,key = lambda x: x['priority'])
        freeblocks = self.get_freeblocks()
        tasks = self.break_tasks(tasks)
        tasks = self.gap_tasks(tasks)
        tasks = self.randomize_tasks(tasks)
        remaining = len(freeblocks)
        got_secondary = False
        for task in tasks:
            if remaining < 1 and not got_secondary:
                freeblocks = self.get_freeblocks(secondary=True)
                remaining = len(freeblocks)
                got_secondary = True
            elif remaining < 1:
                #return note that there's too much taskage
                pass
            self.assign_block(task,freeblocks[len(freeblocks)-remaining])
            remaining += -1

    def break_tasks(self,tasks):
        outtasks = []
        for task in tasks:
            remaining_min = task['duration']
            while remaining_min > 0:
                if remaining_min < self.workstyle['timebox_dur']:
                    this_min = remaining_min
                    remaining_min = 0
                else:
                    this_min = self.workstyle['timebox_dur']
                    remaining_min -= self.workstyle['timebox_dur']
                outtask = copy(task)
                outtask['duration'] = this_min
                outtasks.append(outtask)
        return outtasks              

    def gap_tasks(self,tasks):
        indices = range(len(tasks))[1:-1]
        random.shuffle(indices)
        gapped = 0
        moves = []
        for i in indices:
            if (gapped + 1) < len(tasks) * (1 - self.workstyle['sameness']):
                break
            if tasks[i]['name'] in [tasks[i-1]['name'],tasks[i+1]['name']]:
                moves.append(i)
                gapped += 1
        for m in moves:
            outtask = tasks.pop(m)
            tasks.insert(m+1,outtask)
        return tasks

    def randomize_tasks(self,tasks):
        from_indices = range(len(tasks))[:-1]
        to_indices = range(len(tasks))[1:]
        random.shuffle(from_indices)
        random.shuffle(to_indices)
        moves = []
        for i in range(round(len(tasks) * self.workstyle['randomness'])):
            moves.append((from_indices[i],to_indices[i]))
        for m in moves:
            outtask = tasks.pop(m[0])
            tasks.insert(m[1],outtask)
        return tasks