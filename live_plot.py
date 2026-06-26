"""Real-time training dashboard for the evolutionary-algorithm platformer.

This is a standalone monitor. It does NOT import pygame, Model, Entities, or
data -- it only reads the CSV log that the training process appends to.

The training process writes 'training_log.csv' in the same directory as this
script, with EXACTLY this header and one row per generation:

    generation,best_fitness,avg_fitness,best_progress,best_checkpoints,solved

Usage:
    python live_plot.py

The window updates roughly once per second by re-reading the whole CSV (it is
small). It tolerates the file not existing yet, being empty, or having a
partially-written last line. Close the window or press Ctrl-C to stop.
"""

import csv
import os

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# CSV lives in the same directory as this script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "training_log.csv")

EXPECTED_HEADER = [
    "generation",
    "best_fitness",
    "avg_fitness",
    "best_progress",
    "best_checkpoints",
    "solved",
]

POLL_INTERVAL_MS = 1000  # redraw roughly once per second


def read_log():
    """Read the whole CSV and return a dict of column-name -> list of values.

    Returns None if the file does not exist or has no usable data rows.
    Robust to the file growing while we read it and to a partially-written
    final line (bad rows are skipped).
    """
    if not os.path.exists(CSV_PATH):
        return None

    generations = []
    best_fitness = []
    avg_fitness = []
    best_progress = []
    solved_any = False

    try:
        # newline="" is the csv module's recommended way to open files.
        with open(CSV_PATH, "r", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return None  # empty file

            # Be lenient: accept the file even if header has extra whitespace.
            header = [h.strip() for h in header]
            if header != EXPECTED_HEADER:
                # Header not (yet) what we expect -- treat as not-ready.
                return None

            for row in reader:
                # Skip short/partial rows (e.g. a half-written last line).
                if len(row) < len(EXPECTED_HEADER):
                    continue
                try:
                    gen = int(row[0])
                    bf = float(row[1])
                    af = float(row[2])
                    bp = float(row[3])
                    sv = int(float(row[5]))
                except (ValueError, IndexError):
                    # Bad / partial row -- skip it.
                    continue

                generations.append(gen)
                best_fitness.append(bf)
                avg_fitness.append(af)
                best_progress.append(bp)
                if sv == 1:
                    solved_any = True
    except OSError:
        # File vanished or could not be read this tick; try again next time.
        return None

    if not generations:
        return None

    return {
        "generation": generations,
        "best_fitness": best_fitness,
        "avg_fitness": avg_fitness,
        "best_progress": best_progress,
        "solved": solved_any,
    }


def main():
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()  # secondary axis for best_progress

    # Primary axis lines.
    (line_best,) = ax1.plot([], [], color="tab:blue", lw=2, label="best fitness")
    (line_avg,) = ax1.plot([], [], color="tab:orange", lw=2, label="avg fitness")

    # Secondary axis line (distinct dashed style, semi-transparent).
    (line_prog,) = ax2.plot(
        [],
        [],
        color="tab:green",
        lw=1.5,
        ls="--",
        alpha=0.7,
        label="best progress",
    )

    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Fitness")
    ax2.set_ylabel("Best progress", color="tab:green")
    ax2.tick_params(axis="y", labelcolor="tab:green")

    # Combined legend covering both axes.
    ax1.legend(
        [line_best, line_avg, line_prog],
        [line_best.get_label(), line_avg.get_label(), line_prog.get_label()],
        loc="upper left",
    )

    ax1.grid(True, alpha=0.3)

    def update(_frame):
        data = read_log()

        if data is None:
            ax1.set_title("waiting for training_log.csv…")
            line_best.set_data([], [])
            line_avg.set_data([], [])
            line_prog.set_data([], [])
            return line_best, line_avg, line_prog

        gens = data["generation"]
        line_best.set_data(gens, data["best_fitness"])
        line_avg.set_data(gens, data["avg_fitness"])
        line_prog.set_data(gens, data["best_progress"])

        # Rescale axes to fit the (possibly grown) data.
        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()

        latest_gen = gens[-1]
        latest_best = data["best_fitness"][-1]
        title = "Generation {}  |  best fitness {:.3f}".format(latest_gen, latest_best)
        if data["solved"]:
            title += "  |  ✅ SOLVED"
        ax1.set_title(title)

        return line_best, line_avg, line_prog

    # Keep a reference so the animation is not garbage-collected.
    anim = FuncAnimation(  # noqa: F841
        fig,
        update,
        interval=POLL_INTERVAL_MS,
        cache_frame_data=False,
    )

    fig.tight_layout()
    try:
        plt.show()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
