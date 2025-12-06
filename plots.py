"""
Вспомогательные функции для построения графиков результатов моделирования.

Модуль рисует 4-панельную фигуру: давления, температуры, плотности и
массовый расход G(t). Если в результате интеграции хранится динамический
G в векторе состояния (5-й элемент), используется он; иначе пересчитывается
командный массовый расход.
"""

import matplotlib.pyplot as plt
import config as cfg
from equations import density, mass_flow

def plot_results(times, results):
    p_b = [r[0] for r in results]
    T_b = [r[1] for r in results]
    p_emk = [r[2] for r in results]
    T_emk = [r[3] for r in results]
    
    # compute densities and mass flow
    rho_b = [density(p_b[i], T_b[i]) for i in range(len(times))]
    rho_emk = [density(p_emk[i], T_emk[i]) for i in range(len(times))]
    # If simulation stores dynamic G in the state vector, use it. Otherwise compute commanded mass_flow.
    if len(results) > 0 and len(results[0]) >= 5:
        G = [r[4] for r in results]
    else:
        G = [mass_flow(p_b[i], T_b[i], p_emk[i]) for i in range(len(times))]

    # Create figure with 4 subplots
    fig = plt.figure(figsize=(14, 10))
    
    # График 1: Давления
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(times, p_b, label='p_b (баллон)', linewidth=2)
    ax1.plot(times, p_emk, label='p_emk (ёмкость)', linewidth=2)
    ax1.set_xlabel("Время (с)")
    ax1.set_ylabel("Давление (Па)")
    ax1.set_title("Давления в баллоне и ёмкости")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # График 2: Температуры
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(times, T_b, label='T_b (баллон)', linewidth=2)
    ax2.plot(times, T_emk, label='T_emk (ёмкость)', linewidth=2)
    ax2.set_xlabel("Время (с)")
    ax2.set_ylabel("Температура (К)")
    ax2.set_title("Температуры в баллоне и ёмкости")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # График 3: Плотности
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(times, rho_b, label='rho_b (баллон)', linewidth=2)
    ax3.plot(times, rho_emk, label='rho_emk (ёмкость)', linewidth=2)
    ax3.set_xlabel("Время (с)")
    ax3.set_ylabel("Плотность (кг/м^3)")
    ax3.set_title("Плотности в баллоне и ёмкости")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # График 4: Массовый расход
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(times, G, label='G (массовый расход)', linewidth=2, color='red')
    ax4.set_xlabel("Время (с)")
    ax4.set_ylabel("Массовый расход (кг/с)")
    ax4.set_title("Массовый расход из баллона в ёмкость")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save and show
    filename = "results_ideal_gas.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"График сохранён в: {filename}")
    plt.show()
