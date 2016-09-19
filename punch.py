from datetime import datetime, timezone
import dateutil.parser
import json
import os.path
import requests
from requests.auth import HTTPBasicAuth
import sys
from pprint import pprint

FILENAME = 'punch.in'


def main(config):
    args = sys.argv[1:]
    if len(args) != 1:
        print('Expecting single commandline argument "in" or "out"')
        sys.exit(1)

    # punch new time (fail if there's punch-in without punch-out)
    if args[0] == 'in':
        if os.path.isfile(FILENAME):
            print('Previous punch-in exists. Remove the file first: ' + FILENAME)
            sys.exit(1)

        t = datetime.now(timezone.utc)
        file = open(FILENAME, 'w+')
        file.write(t.isoformat())
        file.close()
        print('Punched ' + str(t))

    # save time interval (fail if there isn't any previous punch-in)
    if args[0] == 'out':
        if not os.path.isfile(FILENAME):
            print('Previous punch-in not found. You need to punch in before punching out')
            sys.exit(1)

        file = open(FILENAME, 'r')
        t_start = dateutil.parser.parse(file.readline())
        t_end = datetime.now(timezone.utc)

        data = {
            'task_id': config['task_id'],
            'start_time': t_start.isoformat(),
            'end_time': t_end.isoformat()
        }
        r = requests.post('https://app.paymoapp.com/api/entries', json=data, auth=HTTPBasicAuth(config['token'], 'foo'))
        r.raise_for_status()
        os.remove(FILENAME)
        print('Punched out at ' + str(t_end) + ', last session lasted '  + format_time(t_start, t_end))


def format_time(start, end):
    h = divmod((end - start).total_seconds(), 3600)  # hours
    m = divmod(h[1], 60)  # minutes
    s = m[1]  # seconds
    return '%d hours, %d minutes, %d seconds' % (h[0], m[0], s)


def load_config(file_name):
    result = {}

    path = ".config/" + file_name + ".json"
    with open(path, "r") as file:
        result.update(json.load(file))

    local_path = ".config/" + file_name + ".local.json"
    try:
        with open(local_path, "r") as file:
            result.update(json.load(file))
    except FileNotFoundError:
        raise ValueError("Please create local config file with name {}.".format(local_path))

    return result


if __name__ == '__main__':
    # use this file dir as working dir
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    main(load_config('config'))
