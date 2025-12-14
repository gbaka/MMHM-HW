import os
import sys

# Ensure project root is on sys.path so imports like `import config` work
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Flask, render_template, request, jsonify
import threading
import time
import importlib

app = Flask(__name__, template_folder='templates', static_folder='static')


def snapshot_cfg(keys):
    import config as cfg
    snap = {}
    for k in keys:
        snap[k] = getattr(cfg, k, None)
    return snap


def restore_cfg(snap):
    import config as cfg
    for k, v in snap.items():
        setattr(cfg, k, v)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/params', methods=['GET'])
def get_params():
    import config as cfg
    keys = ['R', 'n', 'V_b', 'V_emk', 'mu_f', 'm', 'rho_b_0', 'theta_b_0', 'p_emk_0', 'theta_emk_0', 't_max', 'dt', 'valve_tau', 'gas_model', 'a_vdw', 'b_vdw', 'M_molar']
    out = {k: getattr(cfg, k, None) for k in keys}
    return jsonify(out)


@app.route('/api/run', methods=['POST'])
def run_simulation_api():
    data = request.get_json() or {}
    # Allowed overrides
    allowed = ['R', 'n', 'V_b', 'V_emk', 'mu_f', 'm', 'rho_b_0', 'theta_b_0', 'p_emk_0', 'theta_emk_0', 't_max', 'dt', 'valve_tau', 'gas_model', 'a_vdw', 'b_vdw', 'M_molar']
    import config as cfg
    # snapshot
    snap = snapshot_cfg(allowed)
    # apply overrides
    for k in allowed:
        if k in data:
            try:
                val = data[k]
                # if incoming is string 'ideal' or 'vdw', keep as string
                setattr(cfg, k, val)
            except Exception:
                pass

    # run simulation
    from simulation import run_simulation
    try:
        times, results = run_simulation()
    finally:
        # restore config
        restore_cfg(snap)

    # Format data
    p_b = [r[0] for r in results]
    T_b = [r[1] for r in results]
    p_emk = [r[2] for r in results]
    T_emk = [r[3] for r in results]
    G = [r[4] if len(r) > 4 else 0.0 for r in results]

    return jsonify({
        'times': times,
        'p_b': p_b,
        'T_b': T_b,
        'p_emk': p_emk,
        'T_emk': T_emk,
        'G': G,
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
