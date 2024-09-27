import os
from subprocess import Popen, PIPE
import argparse
from time import sleep


def clear_console():
    # Clear the console screen (works on both Windows and UNIX)
    os.system('cls' if os.name == 'nt' else 'clear')


def print_status(status_info):
    clear_console()
    print("============ Simple Job Scheduller ============")
    for value in status_info.values():
        status = value['status']
        # Set color based on status
        if status == 'error':
            status = "error ✗"
            color = '\033[31m'  # Red
        elif status == 'done':
            status = "done ✔"
            color = '\033[32m'  # Green
        elif status == 'running':
            color = '\033[93m'  # Orange (Yellow)
        elif status == 'pending':
            color = '\033[37m'  # light Gray
        elif status == 'unsatisfiable':
            status = "dependency ✗"
            color = '\033[93m'  # Red
        else:
            color = '\033[0m'   # Default color (reset)
        print(f"{value['name']:<30}: {color}{status:>15}""\033[0m")
    print("=" * (30 + 15 + 2))


class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        # Only show default if it's not None
        if action.default is not None and action.default != argparse.SUPPRESS:
            return super()._get_help_string(action)
        return action.help


def parse_jobs(fname):
    jobs = {}
    for jid, cmd in enumerate(open(fname, encoding='utf-8'), 1):
        jobs[jid] = {
            'cpu'   : 1,
            'mem'   : 1,
            'time'  : '2h',
            'qos'   : 'local',
            'name'  : f'job_{jid}',
            'depe'  : None,
            'status': 'pending',
            }

        if cmd.startswith('['):
            inargs = dict(c.split(' ')
                          for c in cmd[1:].split('] ')[0].strip().split(';'))
            if 'depe' in inargs:
                inargs['depe'] = [int(d) for d in inargs['depe'].split(',')]
            jobs[jid].update(inargs)
            jobs[jid]['cmd'] = cmd.split(']')[1].strip()
            jobs[jid]['cpu'] = int(jobs[jid]['cpu'])
            jobs[jid]['mem'] = int(jobs[jid]['mem'])
        else:
            jobs[jid]['cmd'] = cmd.strip()
    return jobs


def all_satisfied(jid, jobs, pending_jobs):
    """
    checks if all dependencies are satisfied
    """
    dependencies = jobs[jid]['depe']
    if dependencies is None:
        return True
    if all(jobs[dep]['status'] == 'done' for dep in dependencies):
        return True
    if any(jobs[dep]['status'] in ['error', 'unsatisfiable'] for dep in dependencies):
        del pending_jobs[jid]
        jobs[jid]['status'] = 'unsatisfiable'
    return False
        

def main():
    opts = get_options()
    total_cpu = opts.cpus
    total_mem = opts.mem

    jobs = parse_jobs(opts.job_list)

    available_cpu = total_cpu
    available_mem = total_mem

    procs = {}
    pending_jobs = dict((jid, None) for jid in jobs)

    while pending_jobs:
        for jid in list(pending_jobs.keys()):
            # can run the job?
            if (jobs[jid]['cpu'] <= available_cpu and
                jobs[jid]['mem'] <= available_mem and
                jobs[jid]['status'] == 'pending' and
                all_satisfied(jid, jobs, pending_jobs)):
                available_cpu -= jobs[jid]['cpu']
                available_mem -= jobs[jid]['mem']
                procs[jid] = Popen(jobs[jid]['cmd'], shell=True,
                                   stdout=PIPE, stderr=PIPE)
                jobs[jid]['status'] = 'running'
        for jid, proc in procs.items():
            return_code = proc.poll()
            if return_code is not None:
                if return_code != 0:
                    jobs[jid]['status'] = 'error'
                else:                    
                    jobs[jid]['status'] = 'done'
                available_cpu += jobs[jid]['cpu']
                available_mem += jobs[jid]['mem']
                del procs[jid]
                del pending_jobs[jid]
                break
        print_status(jobs)
        sleep(0.1)


def get_options():
    parser = argparse.ArgumentParser(
        description='Simple job scheduller to be used in local.',
        formatter_class=CustomHelpFormatter)
    parser.add_argument('-i', dest='job_list', type=str, metavar='FILE', required=True,
                        help=('Input file containing the list of jobs to run with'
                              ' number of CPUs and MEM to dedicate to each'))
    parser.add_argument('--cpus', type=int, default=os.cpu_count(), metavar='',
                        help='Number of CPUs to be used in total by scheduller')
    parser.add_argument('--mem', type=int, metavar='',
                        default=round(get_total_memory_linux(), 1) - 0.1,
                        help='Amount of memory (Gb) to be used in total by scheduller')

    return parser.parse_args()


def get_total_memory_linux() -> float:
    """
    get total memory of the system (linux only!)
    """
    with open('/proc/meminfo', 'r') as meminfo:
        for line in meminfo:
            if line.startswith('MemTotal'):
                # Extract value in KB, convert to GB
                total_memory_kb = int(line.split()[1])
                total_memory_gb = total_memory_kb / (1024 ** 2)
                return total_memory_gb
    raise NotImplementedError('ERROR: can not find total memory on this system')


if __name__ == '__main__':
    main()