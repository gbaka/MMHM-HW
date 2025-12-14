import config as cfg
import math


def density(p, T):
    """
    Универсальная функция плотности: выбирает модель по `cfg.gas_model`.
    Возвращает плотность rho [kg/m^3].
    """
    model = getattr(cfg, 'gas_model', 'ideal')
    if T <= 0 or p <= 0:
        return 0.0
    if model == 'ideal':
        return p / (cfg.R * T)
    elif model == 'vdw':
        # Van-der-Waals in molar form: p = R_u T / (V_m - b) - a / V_m^2
        # Solve for molar volume V_m, then rho = M / V_m
        R_u = cfg.R * cfg.M_molar  # J/(mol K)
        a = cfg.a_vdw
        b = cfg.b_vdw
        M = cfg.M_molar

        # initial guess: ideal molar volume
        V_m = R_u * T / p
        if V_m <= b:
            V_m = b * 1.1

        # Newton iteration to solve f(V_m)=0
        for _ in range(50):
            denom = V_m - b
            if denom == 0:
                denom = 1e-12
            f = R_u * T / denom - a / (V_m ** 2) - p
            # derivative df/dV = -R_u*T/(V_m-b)^2 + 2a/V_m^3
            df = -R_u * T / (denom ** 2) + 2.0 * a / (V_m ** 3)
            if df == 0:
                break
            V_m_new = V_m - f / df
            if V_m_new <= b:
                V_m_new = b * 1.0001
            if abs(V_m_new - V_m) / V_m < 1e-9:
                V_m = V_m_new
                break
            V_m = V_m_new

        # rho = mass per mol / molar volume
        rho = M / V_m
        return rho
    else:
        # fallback to ideal
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
    gas_model = getattr(cfg, 'gas_model', 'ideal')

    def density_and_derivs(p, T):
        """
        Вернуть rho, dρ/dp, dρ/dT. Для сложных EOS используем центральные разности.
        """
        rho = density(p, T)
        # finite differences
        dp = max(1e-6 * p, 1e-6)
        dT = max(1e-6 * T, 1e-6)
        rho_p = (density(p + dp, T) - density(p - dp, T)) / (2 * dp)
        rho_T = (density(p, T + dT) - density(p, T - dT)) / (2 * dT)
        return rho, rho_p, rho_T

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
    # Общий подход для любой EOS:
    # m = rho(p,T) * V
    # dm/dt = -G (баллон) = V*(rho_p * dpb_dt + rho_T * dTb_dt)
    # Энергия: U = m * cv * T, dU/dt = -h_out * G ~ -cp * T_b * G
    # Решаем сначала dT/dt из энергетического уравнения, затем dp/dt из массового
    # cv и cp (используем идеальные выражения как приближение)
    cv = R / (n - 1)
    cp = cv + R

    # Cylinder
    rho_b, rho_bp, rho_bT = density_and_derivs(p_b, T_b)
    m_b = rho_b * cfg.V_b
    # avoid zero mass
    if m_b <= 0:
        dTb_dt = 0.0
    else:
        # from energy balance: cv * (m_b * dT + T_b * dm/dt) = -cp * T_b * G
        # dm/dt = -G
        # cv * m_b * dT - cv * T_b * G = -cp * T_b * G
        # => cv * m_b * dT = (cv - cp) * T_b * G = -R * T_b * G
        dTb_dt = -(R * T_b * G) / (cv * m_b)

    # mass eq -> dpb_dt
    denom = rho_bp if rho_bp != 0 else 1e-12
    dpb_dt = (-G / cfg.V_b - rho_bT * dTb_dt) / denom

    # ===== ЁМКОСТЬ =====
    rho_emk, rho_ep, rho_eT = density_and_derivs(p_emk, T_emk)
    m_emk = rho_emk * cfg.V_emk
    if m_emk <= 0:
        dTemk_dt = 0.0
    else:
        # energy balance: cv*(m_emk*dT + T_emk*dm/dt) = cp * T_b * G
        # dm/dt = +G
        # cv*m_emk*dT + cv*T_emk*G = cp*T_b*G
        # => cv*m_emk*dT = (cp*T_b - cv*T_emk) * G
        dTemk_dt = (cp * T_b - cv * T_emk) * G / (cv * m_emk)

    denom_e = rho_ep if rho_ep != 0 else 1e-12
    dpemk_dt = (G / cfg.V_emk - rho_eT * dTemk_dt) / denom_e

    return [dpb_dt, dTb_dt, dpemk_dt, dTemk_dt, dG_dt]
