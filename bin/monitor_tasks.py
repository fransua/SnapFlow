#! /usr/bin/env python

import argparse
import psutil
import time


def get_all_children_pids(parent_pid):
    """
    Get all child processes recursively
    """
    try:
        parent_process = psutil.Process(parent_pid)
        children = parent_process.children(recursive=True)  # Get all children recursively
        return children
    except psutil.NoSuchProcess:
        return []

def monitor_ps_children(parent_pid):
    """
    To monitor CPU and memory usage of a process and its children
    """
    peak_mem = 0
    peak_cpu = 0
    total_cpu = 0
    total_mem = 0
    loops = 0

    to_Gb = 1024 * 1024 * 1024

    try:
        # Loop until the parent process finishes
        while psutil.pid_exists(parent_pid):
            try:
                parent_process = psutil.Process(parent_pid)

                # Get all child processes recursively
                children = get_all_children_pids(parent_pid)

                # Include the parent process in the list of processes to monitor
                all_processes = [parent_process] + children

                # Sum the CPU and memory usage of all processes (parent + children)
                current_cpu = sum(p.cpu_percent(interval=0.1) for p in all_processes)
                current_mem = sum(p.memory_info().rss for p in all_processes)  # Memory in bytes

                # Convert memory from bytes to megabytes
                current_mem_mb = current_mem / to_Gb

                # Track peak CPU and memory usage
                if current_cpu > peak_cpu:
                    peak_cpu = current_cpu
                if current_mem_mb > peak_mem:
                    peak_mem = current_mem_mb

                loops += 1
                total_mem += current_mem_mb
                total_cpu += current_cpu

                time.sleep(0.5)
            except psutil.NoSuchProcess:
                continue
    except KeyboardInterrupt:
        print("Monitoring interrupted by user.")
    return peak_cpu, peak_mem, total_cpu / loops, total_mem / loops


def main():
    opts = get_options()
    parent_pid = opts.pid
    peak_cpu, peak_mem, average_cpu, average_mem = monitor_ps_children(parent_pid)

    out = open(opts.outfile, 'w', encoding='utf-8')
    out.write(f"Peak CPU: {peak_cpu}\n")
    out.write(f"Peak MEM: {peak_mem}\n")
    out.write(f"Average CPU: {average_cpu}\n")
    out.write(f"Average MEM: {average_mem}\n")
    out.close()


class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        # Only show default if it's not None
        if action.default is not None and action.default != argparse.SUPPRESS:
            return super()._get_help_string(action)
        return action.help


def get_options():
    parser = argparse.ArgumentParser(
        description='Description of your script',
        formatter_class=CustomHelpFormatter)

    parser.add_argument('-p', dest='pid', metavar='PID', type=int,
                        required=True,
                        help='PID of the process to monitor')
    parser.add_argument('-o', metavar='PATH', dest='outfile',
                        help='Path to output file to store measurements.')

    return parser.parse_args()


if __name__ == "__main__":
    main()
