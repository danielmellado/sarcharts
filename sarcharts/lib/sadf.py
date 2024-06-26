import os
import re

from sarcharts.lib import util


class Sadf:

    def merge_sarfiles(self, debuglevel, sarfiles, outputpath, charts):
        showheader = ""
        notavailable = []
        util.debug(debuglevel, '', "Getting data from sar files.")
        for inputfile in sarfiles:
            for k, v in charts.items():
                csvfile = f"{outputpath}/{k}.csv"
                command = f"sadf -dt {inputfile} -- {v['arg']} {showheader}"
                [stdout, stderr] = util.exec_command(debuglevel, command)
                if stderr:
                    if "Requested activities not available" in stderr:
                        util.debug(debuglevel, 'I', stderr.strip())
                        if k not in notavailable:
                            notavailable.append(k)
                    else:
                        util.debug(debuglevel, 'W', stderr.strip())
                else:
                    util.debug(debuglevel, 'D', "Merge " + inputfile
                               + " to " + csvfile)
                    if os.path.exists(csvfile):
                        with open(csvfile, "a") as myfile:
                            myfile.write(stdout)
                    else:
                        with open(csvfile, "w") as myfile:
                            myfile.write(stdout)
            showheader = "| grep -vE '^#'"
        return notavailable

    def sar_to_chartjs(
            self, debuglevel, sarfiles, outputpath, charts, dfrom, dto):
        # convert csv to chartjs compatible data Lists
        chartinfo = {
            "notavailable": '',
            "hostnames": [],
            "firstdate": '',
            "lastdate": ''
            }
        chartinfo['notavailable'] = self.merge_sarfiles(
            debuglevel, sarfiles, outputpath, charts
            )
        util.debug(debuglevel, '', "Generating Charts.")
        for k, v in charts.items():
            if k not in chartinfo['notavailable']:
                csvfile = f"{outputpath}/{k}.csv"
                with open(csvfile) as f:
                    # set the first data field
                    datastart = 4 if charts[k]['multiple'] else 3
                    # get headers from first line
                    line = f.readline().strip()
                    headers = line.split(";")[datastart:]
                    # get first stats date
                    pos = f.tell()
                    line = f.readline().split(";")
                    chartinfo['firstdate'] = line[2]
                    # get hostname
                    if line[0] not in chartinfo['hostnames']:
                        chartinfo['hostnames'].append(line[0])
                    # seek file to first stats line
                    f.seek(pos)
                    for line in f:
                        if "LINUX-RESTART" in line or re.match(r"^#", line):
                            continue
                        fields = line.strip().split(";")
                        if util.in_date_range(
                                debuglevel, dfrom, dto, fields[2]):
                            # set fake item on non multiple charts
                            item = (
                                fields[3] if charts[k]['multiple'] else ""
                                )
                            # add date field to Chart labels
                            if fields[2] not in charts[k]['labels']:
                                charts[k]['labels'].append(fields[2])
                            if item not in charts[k]['datasets'].keys():
                                charts[k]['datasets'][item] = []
                                for h in headers:
                                    i = {"label": h, "values": []}
                                    charts[k]['datasets'][item].append(i)

                            for i in range(len(fields[datastart:])):
                                value = (
                                    {'x': fields[2], 'y': fields[i+datastart]}
                                    )
                                charts[k]['datasets'][
                                    item][i]['values'].append(value)
                    if line != "":
                        chartinfo['lastdate'] = fields[2]
        return chartinfo
