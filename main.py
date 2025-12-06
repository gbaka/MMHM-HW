"""
Точка входа для моделирования нестационарного дросселирования.

Скрипт вызывает интегратор (симуляцию) и функции построения графиков.
Обычно используется для восстановления результатов задания:
- моделирование выпуска газа из баллона в ёмкость;
- идеальный газ с опциональной моделью клапана 1-го порядка для сглаживания
  командного расхода.

Запуск:
    python main.py

Используемые файлы: `config.py`, `simulation.py`, `plots.py`, `equations.py`, `solver.py`.
"""

from simulation import run_simulation
from plots import plot_results


if __name__ == "__main__":
    times, results = run_simulation()
    plot_results(times, results)
