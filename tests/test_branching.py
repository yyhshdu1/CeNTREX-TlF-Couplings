import numpy as np
from centrex_TlF_hamiltonian import states
import centrex_TlF_couplings as couplings


def test_calculate_br():
    excited_state = states.CoupledBasisState(
        J=1, F1=1 / 2, F=1, mF=0, I1=1 / 2, I2=1 / 2, Omega=1, P=1
    )
    qn_select = states.QuantumSelector(J=1)
    ground_states = states.generate_coupled_states_X(qn_select)
    br = couplings.calculate_br(1 * excited_state, 1 * ground_states)
    assert np.allclose(
        br,
        [
            0.22222222,
            0.22222222,
            0.0,
            0.22222222,
            0.02777778,
            0.0,
            0.02777778,
            0.0,
            0.08333333,
            0.11111111,
            0.08333333,
            0.0,
        ],
    )
    assert br.sum() == 1.0
