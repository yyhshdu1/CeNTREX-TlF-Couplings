import numpy as np
from centrex_tlf_hamiltonian import states
import centrex_tlf_couplings as couplings
from pathlib import Path


def test_generate_coupling_matrix():
    qn_select = states.QuantumSelector(J=1)
    ground_states = states.generate_coupled_states_X(qn_select)

    qn_select = states.QuantumSelector(
        J=1, F1=1 / 2, F=1, P=1, Ω=1, electronic=states.ElectronicState.B
    )
    excited_states = states.generate_coupled_states_B(qn_select)

    QN = list(1 * np.append(ground_states, excited_states))
    ground_states = list(1 * ground_states)
    excited_states = list(1 * excited_states)

    pol_vec = np.array([0.0, 0.0, 1.0])
    reduced = False
    normalize_pol = True

    coupling_matrix = couplings.generate_coupling_matrix(
        QN, ground_states, excited_states, pol_vec, reduced, normalize_pol
    )

    coupling_matrix_test = np.load(Path(__file__).parent / "coupling_matrix_test.npy")

    assert np.allclose(coupling_matrix, -coupling_matrix_test)


def test_generate_coupling_field_automatic():
    qn_select = states.QuantumSelector(J=1)
    ground_states = states.generate_coupled_states_X(qn_select)

    qn_select = states.QuantumSelector(
        J=1, F1=1 / 2, F=1, P=1, Ω=1, electronic=states.ElectronicState.B
    )
    excited_states = states.generate_coupled_states_B(qn_select)

    QN = list(1 * np.append(ground_states, excited_states))
    ground_states = list(1 * ground_states)
    excited_states = list(1 * excited_states)

    H_rot = np.eye(len(QN), dtype=complex) * np.arange(len(QN))
    V_ref = np.eye(len(QN))
    pol_vecs = [np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])]
    normalize_pol = True

    coupling = couplings.generate_coupling_field_automatic(
        ground_states, excited_states, QN, H_rot, QN, V_ref, pol_vecs, normalize_pol
    )
    assert coupling.main_coupling == (0.4714045207910316 + 0j)
    assert coupling.ground_main == ground_states[1]
    assert coupling.excited_main == excited_states[0]
    assert np.all(coupling.fields[0].polarization == np.array([0.0, 0.0, 1.0]))
    assert np.all(coupling.fields[1].polarization == np.array([1.0, 0.0, 0.0]))
