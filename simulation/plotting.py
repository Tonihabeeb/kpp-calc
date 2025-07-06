import logging
import os

import matplotlib.pyplot as plt


class PlottingUtility:
    """
    A utility class for generating and saving simulation result plots.
    """

    def __init__(self, output_dir="static/plots"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"PlottingUtility initialized. Output directory: {self.output_dir}")

    def plot_time_series(self, data, title, xlabel, ylabel, filename):
        """
        Generate and save a time-series plot.

        Args:
            data (dict): A dictionary with 'time' as keys and corresponding values as lists.
            title (str): The title of the plot.
            xlabel (str): Label for the x-axis.
            ylabel (str): Label for the y-axis.
            filename (str): The filename to save the plot as.
        """
        try:
            plt.figure()
            for label, values in data.items():
                if label != "time":
                    plt.plot(data["time"], values, label=label)

            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid(True)

            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path)
            plt.close()

            self.logger.info(f"Plot saved: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to generate plot: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Example data
    results_log = {
        "time": [0, 1, 2, 3, 4, 5],
        "torque": [10, 20, 15, 25, 30, 35],
        "power": [5, 10, 7, 12, 15, 18],
    }

    plotter = PlottingUtility()
    plotter.plot_time_series(
        data=results_log,
        title="Simulation Results",
        xlabel="Time (s)",
        ylabel="Values",
        filename="simulation_results.png",
    )
