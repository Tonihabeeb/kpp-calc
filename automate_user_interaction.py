import time
import requests

BASE_URL = 'http://localhost:5000'

# 1. Start the simulation
def start_simulation(params=None):
    url = f'{BASE_URL}/start'
    resp = requests.post(url, json=params or {})
    print('Start:', resp.status_code, resp.text)

def set_params(params):
    url = f'{BASE_URL}/set_params'
    resp = requests.post(url, json=params)
    print('Set params:', params, resp.status_code)

def stop_simulation():
    url = f'{BASE_URL}/stop'
    resp = requests.post(url)
    print('Stop:', resp.status_code)

def reset_simulation():
    url = f'{BASE_URL}/reset'
    resp = requests.post(url)
    print('Reset:', resp.status_code)

def download_csv():
    url = f'{BASE_URL}/download_csv'
    resp = requests.get(url)
    with open('sim_downloaded.csv', 'wb') as f:
        f.write(resp.content)
    print('Downloaded CSV to sim_downloaded.csv')

if __name__ == '__main__':
    # 1. Start simulation with default params
    start_simulation()
    print('Waiting 15 seconds to collect initial data...')
    time.sleep(15)
    # 2. Change air pressure
    set_params({'air_pressure': 4.0})
    print('Waiting 15 seconds after parameter change...')
    time.sleep(15)
    # 3. Stop simulation
    stop_simulation()
    print('Simulation stopped. Waiting 2 seconds...')
    time.sleep(2)
    # 4. Download CSV
    download_csv()
    # 5. Reset simulation
    reset_simulation()
    print('Automation complete.')
