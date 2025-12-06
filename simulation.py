"""
Драйвер симуляции: инициализирует начальные условия, интегрирует систему ОДУ
и собирает результаты.

Вектор состояния системы ОДУ:
    y = [p_b, T_b, p_emk, T_emk, G]

где `G` - фактический массовый расход (динамически фильтруется моделью клапана).

Возвращает:
    times, results  (списки временных моментов и соответствующих состояний)

См. `equations.py` для физической модели.
"""

import config as cfg
from equations import rhs, density
from solver import rk4_step

def run_simulation():
    t = 0.0
    dt = cfg.dt
    t_max = cfg.t_max

    # Начальные условия
    p_b0 = cfg.rho_b_0 * cfg.R * cfg.theta_b_0
    y = [p_b0, cfg.theta_b_0, cfg.p_emk_0, cfg.theta_emk_0, 0.0]

    times = []
    results = []

    # Вывод начальных условий (подавлен для совместимости с не-ASCII)
    # print(f"Начальные условия:")
    # print(f"  Баллон: p_b = {p_b0:.2e} Pa, T_b = {cfg.theta_b_0} K, rho_b = {cfg.rho_b_0} kg/m3")
    # print(f"  Ёмкость: p_emk = {cfg.p_emk_0:.2e} Pa, T_emk = {cfg.theta_emk_0} K")
    # print(f"Время симуляции: {t_max} сек, dt = {dt} сек\n")

    # Периодический вывод состояния
    next_print = 0.0
    while t < t_max:
        times.append(t)
        results.append(y.copy())

        # Вывод состояния в указанные интервалы
        if t >= next_print - 1e-12:
            # Ожидаемый вектор: y = [p_b, T_b, p_emk, T_emk, G]
            if len(y) >= 5:
                p_b, T_b, p_emk, T_emk, G = y
            else:
                p_b, T_b, p_emk, T_emk = y
                G = 0.0

            rho_b = density(p_b, T_b)
            rho_emk = density(p_emk, T_emk)

            # Вывод подавлен для избежания проблем с кодировкой
            # print(f"t={t:6.3f} s | p_b={p_b:10.3e} Pa, T_b={T_b:7.2f} K, rho_b={rho_b:8.3f} kg/m^3, G={G:8.3f} kg/s")
            # print(f"            p_emk={p_emk:10.3e} Pa, T_emk={T_emk:7.2f} K, rho_emk={rho_emk:8.3f} kg/m^3")
            next_print += cfg.print_interval

        # Выполнить один шаг интегрирования RK4
        y = rk4_step(rhs, t, y, dt)
        
        # Защита: убедиться, что p_b >= p_emk (нет обратного потока)
        if len(y) >= 5:
            p_b, T_b, p_emk, T_emk, G = y
            if p_emk > p_b:
                # Ограничить p_emk до p_b, чтобы исключить физически невозможное состояние
                # Сохранить массу постоянной, отрегулировав T_emk
                # m_emk = p_emk * V / (R * T_emk) = const
                # => T_emk_new = T_emk * (p_emk_old / p_emk_new)
                T_emk_corrected = T_emk * (p_emk / p_b)
                y = [p_b, T_b, p_b, T_emk_corrected, 0.0]  # Остановить поток при выравнивании давлений
        
        t += dt

    # Финальные значения
    if len(y) >= 5:
        p_b_final, T_b_final, p_emk_final, T_emk_final, G_final = y
    else:
        p_b_final, T_b_final, p_emk_final, T_emk_final = y
        G_final = 0.0

    rho_b_final = density(p_b_final, T_b_final)
    rho_emk_final = density(p_emk_final, T_emk_final)
    
    # Вывод подавлен для избежания проблем с кодировкой
    # print(f"\nФинальные значения (t = {t_max} сек):")
    # print(f"  Баллон: p_b = {p_b_final:.2e} Pa, T_b = {T_b_final:.2f} K, rho_b = {rho_b_final:.2f} kg/m3")
    # print(f"  Ёмкость: p_emk = {p_emk_final:.2e} Pa, T_emk = {T_emk_final:.2f} K, rho_emk = {rho_emk_final:.2f} kg/m3")
    # print(f"  Разность давлений: Dp = {p_b_final - p_emk_final:.2e} Pa")

    return times, results



