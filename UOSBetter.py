#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOSBetter Wrapper Script
This script checks if the UOSBetter service is already running on port 55000.
If it is, it opens the default web browser to the service.
If not, it starts the Flask app (app.py) and then opens the browser.
"""

import socket
import subprocess
import time
import webbrowser
import sys
import os

def is_port_in_use(port):
    """Check if a port is in use on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex(('127.0.0.1', port))
        return result == 0

def main():
    port = 55000
    host = '127.0.0.1'
    url = f'http://{host}:{port}'

    if is_port_in_use(port):
        print(f"Service is already running on {url}. Opening browser...")
        webbrowser.open(url)
    else:
        print(f"Service not running on {url}. Starting Flask app...")
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, 'app.py')
        log_path = os.path.join(script_dir, 'app.log')
        
        # Start the Flask app in the background
        # Redirect output to a log file and detach the process completely
        with open(log_path, 'a') as log_file:
            proc = subprocess.Popen(
                [sys.executable, app_path],
                cwd=script_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        
        print(f"Started Flask app with PID {proc.pid}")
        
        # Wait a bit for the server to start
        max_attempts = 10
        for i in range(max_attempts):
            time.sleep(1)
            if is_port_in_use(port):
                print(f"Service started successfully on {url}.")
                break
            else:
                print(f"Waiting for service to start... (attempt {i+1}/{max_attempts})")
        else:
            print(f"Warning: Service did not start within {max_attempts} seconds.")
        
        # Open the browser
        print(f"Opening browser to {url}...")
        webbrowser.open(url)

if __name__ == '__main__':
    main()
