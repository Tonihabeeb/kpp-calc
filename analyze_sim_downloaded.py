import pandas as pd
import matplotlib.pyplot as plt

# Load the simulation data CSV (update the filename if needed)
data = pd.read_csv('sim_downloaded.csv')

# Plot key metrics over time
def plot_metric(metric, ylabel, color='b'):
    plt.figure(figsize=(10, 4))
    plt.plot(data['time'], data[metric], color)
    plt.xlabel('Time (s)')
    plt.ylabel(ylabel)
    plt.title(f'{ylabel} vs Time')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Plot all main metrics
if 'torque' in data.columns:
    plot_metric('torque', 'Generator Torque (Nm)', 'r')
if 'power' in data.columns:
    plot_metric('power', 'Generator Power (W)', 'g')
if 'efficiency' in data.columns:
    plot_metric('efficiency', 'Efficiency (%)', 'b')
if 'clutch_engaged' in data.columns:
    plt.figure(figsize=(10, 2))
    plt.plot(data['time'], data['clutch_engaged'], 'm')
    plt.xlabel('Time (s)')
    plt.ylabel('Clutch Engaged')
    plt.title('Clutch Engagement vs Time')
    plt.yticks([0, 1], ['Disengaged', 'Engaged'])
    plt.grid(True)
    plt.tight_layout()
    plt.show()
if 'tank_pressure' in data.columns:
    plot_metric('tank_pressure', 'Tank Pressure (bar)', 'c')

# Print summary statistics
print('--- Summary Statistics ---')
for col in data.columns:
    if data[col].dtype in ['float64', 'int64'] and col != 'time':
        print(f'{col}: mean={data[col].mean():.2f}, min={data[col].min():.2f}, max={data[col].max():.2f}, std={data[col].std():.2f}')

# Show first and last few rows for inspection
print('\nFirst 5 rows:')
print(data.head())
print('\nLast 5 rows:')
print(data.tail())
