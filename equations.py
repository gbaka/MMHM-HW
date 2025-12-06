import config as cfg
import math

def density(p, T):
    """Плотность идеального газа: ρ = p / (RT)"""
    if T <= 0:
        return 0.0
    return p / (cfg.R * T)

def phi(v):
    """Функция φ(v) для докритического расхода."""
    n = cfg.n
    term1 = v ** (2 / (n - 1))
    term2 = v ** ((n + 1) / (n - 1))
    
    if term1 < term2:
        return 0.0
    return math.sqrt(term1 - term2)

def mass_flow(p_b, T_b, p_emk):
    """
    Массовый расход из баллона в емкость.
    Выбирает докритический или критический режим.
    """
    if p_emk >= p_b or T_b <= 0:
        return 0.0

    n = cfg.n
    R = cfg.R
    mu_f = cfg.mu_f
    m = cfg.m

    v = p_emk / p_b
    beta = (2 / (n + 1)) ** (n / (n - 1))
    p_crit = beta * p_b

    if p_emk > p_crit:
        # докритический режим
        phi_val = phi(v)
        if phi_val < 0:
            phi_val = 0
        return mu_f * phi_val * math.sqrt(2 * n / (R * (n - 1)) * (p_b / T_b))
    else:
        # критический режим (захлёст)
        return mu_f * m * p_b / math.sqrt(T_b)

def rhs(t, y):
    """
    Правая часть системы ОДУ для баллона и емкости с динамической моделью запорного
    устройства (вентили/ограничителя расхода).
    y = [p_b, T_b, p_emk, T_emk, G]

    Модель клапана: G_dot = (G_cmd - G) / tau, где G_cmd = mass_flow(...)

    Массовый баланс использует текущий (фактический) G.
    """
    # Ожидаемое состояние: p_b, T_b, p_emk, T_emk, G
    if len(y) >= 5:
        p_b, T_b, p_emk, T_emk, G = y
    else:
        # на случай вызова со старым вектором: дополняем нулевым G
        p_b, T_b, p_emk, T_emk = y
        G = 0.0

    # Параметры
    n = cfg.n
    R = cfg.R
    tau = getattr(cfg, 'valve_tau', 0.01)

    # Защита от нефизичных значений: если давления или температуры невалидны,
    # заставляем расход убывать к нулю (клапан закрывается) и возвращаем нули для dp/dt.
    if p_b <= 0 or T_b <= 0 or p_emk <= 0 or T_emk <= 0:
        dG_dt = -G / tau
        return [0.0, 0.0, 0.0, 0.0, dG_dt]

    # Командный расход, который даёт текущее соотношение давлений/температуры
    G_cmd = mass_flow(p_b, T_b, p_emk)

    # Динамика клапана (первого порядка)
    dG_dt = (G_cmd - G) / tau

    # ===== БАЛЛОН =====
    dpb_dt = -(n * R / cfg.V_b) * T_b * G
    dTb_dt = ((n - 1) / n) * (T_b / p_b) * dpb_dt if p_b != 0 else 0.0

    # ===== ЁМКОСТЬ =====
    # Mass balance: dm/dt = G, m = p*V/(R*T)
    # Energy balance (adiabatic): dU/dt = h*G, U = p*V/n = m*cv*T
    # From energy: dT_emk/dt = R*T_b*G / p_emk
    # From mass: dp_emk/dt = R*(T_emk + T_b)*G / V_emk
    dpemk_dt = (R / cfg.V_emk) * (T_emk + T_b) * G
    dTemk_dt = (R / p_emk) * T_b * G if p_emk != 0 else 0.0

    return [dpb_dt, dTb_dt, dpemk_dt, dTemk_dt, dG_dt]
