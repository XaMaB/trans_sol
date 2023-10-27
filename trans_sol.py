#!/usr/bin/env python3

import time, os, json
import trans
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Process


pid_file = '/var/run/trans_sol.pid'

def write_pid_to_file(file_path):
    pid = os.getpid()
    with open(file_path, 'w') as file:
        file.write(str(pid))
    print(f"PID {pid} written to {file_path}")


write_pid_to_file(pid_file)

def ConfigFromJson(infile):
    global minput_file, mout_path, madb_prof, mout_file
    with open(infile, 'r') as json_conf:
        data = json.load(json_conf)
        for item in data:
            minput_file = item['filename']
            mout_file = item['out_file']
            madb_prof = item['profiles']
            mout_path = f'/content/videos/{mout_file}'
    return minput_file, mout_path, mout_file, int(madb_prof)

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        else:
            file_path = event.src_path
            _, file_extension = os.path.splitext(file_path)
            valid_extensions = {'.json'}
            if file_extension.lower() in valid_extensions:
                ConfigFromJson(file_path)
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                print(f"New File: {file_name} for video {minput_file} found.")
                process = Process(target=trans.enc_process, args=(f'{directory_to_watch}{minput_file}', mout_path, mout_file, int(madb_prof)))
                process.start()
                time.sleep(2)


if __name__ == "__main__":
    directory_to_watch = "/content/imports/"

    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



