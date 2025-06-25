#!/usr/bin/env python3

from simulation.grid_services.frequency.secondary_frequency_controller import create_standard_secondary_frequency_controller

controller = create_standard_secondary_frequency_controller()
print('Ramp rate:', controller.config.ramp_rate, 'per minute')
print('Ramp rate per 0.1s:', controller.config.ramp_rate / 60.0 * 0.1)

# Test multiple steps
for i in range(25):
    response = controller.update(0.5, 0.1, 500.0)
    if i % 5 == 0:
        print(f'Step {i}: current={controller.current_response:.4f}, target={controller.target_response:.4f}, power={response["power_command_mw"]:.2f} MW')

print(f'Final: current={controller.current_response:.4f}, target={controller.target_response:.4f}')
print(f'Final power: {response["power_command_mw"]:.2f} MW')
