from dataclasses import dataclass
from typing import List, Sequence, Union
from centrex_tlf_hamiltonian.states.states import CoupledBasisState

import numpy as np
import numpy.typing as npt
from centrex_tlf_hamiltonian import states

from .matrix_elements import generate_ED_ME_mixed_state
from .utils import assert_transition_coupled_allowed, select_main_states

__all__ = [
    "generate_coupling_matrix",
    "generate_coupling_field",
    "generate_coupling_field_automatic",
    "CouplingFields",
    "CouplingField",
]


def generate_coupling_matrix(
    QN: Sequence[states.State],
    ground_states: Sequence[states.State],
    excited_states: Sequence[states.State],
    pol_vec: npt.NDArray[np.complex_] = np.array([0.0, 0.0, 1.0], dtype=np.complex_),
    reduced: bool = False,
    normalize_pol: bool = True,
) -> npt.NDArray[np.complex_]:
    """generate optical coupling matrix for given ground and excited states
    Checks if couplings are already pre-cached, otherwise falls back to
    calculate_coupling_matrix.

    Args:
        QN (list): list of basis states
        ground_states (list): list of ground states coupling to excited states
        excited_states (list): list of excited states
        pol_vec (np.ndarray): polarization vector. Defaults to
                                        np.array([0,0,1]).
        reduced (bool, optional): [description]. Defaults to False.
        normalize_pol (bool, optional): Normalize the polarization vector.
                                        Defaults to True.

    Returns:
        np.ndarray: optical coupling matrix
    """
    assert isinstance(QN, list), "QN required to be of type list"

    H = np.zeros((len(QN), len(QN)), dtype=complex)

    # start looping over ground and excited states
    for ground_state in ground_states:
        i = QN.index(ground_state)
        for excited_state in excited_states:
            j = QN.index(excited_state)

            # calculate matrix element and add it to the Hamiltonian
            H[i, j] = generate_ED_ME_mixed_state(
                excited_state,
                ground_state,
                pol_vec=pol_vec,
                reduced=reduced,
                normalize_pol=normalize_pol,
            )

            # make H hermitian
    H = H + H.conj().T

    return H


@dataclass
class CouplingField:
    polarization: npt.NDArray[np.complex_]
    field: npt.NDArray[np.complex_]


@dataclass
class CouplingFields:
    ground_main: states.State
    excited_main: states.State
    main_coupling: complex
    ground_states: Sequence[states.State]
    excited_states: Sequence[states.State]
    fields: Sequence[CouplingField]

    def __repr__(self):
        gs = self.ground_main.largest
        es = self.excited_main.largest
        return (
            f"CouplingFields(ground_main={gs.state_string_custom(['electronic', 'J', 'F1', 'F', 'mF', 'P', 'Ω'])}, "
            f"excited_main={es.state_string_custom(['electronic', 'J', 'F1', 'F', 'mF', 'P', 'Ω'])}, "
            f"main_coupling={self.main_coupling:.2e}"
        )


def generate_coupling_field(
    ground_main_approx: states.State,
    excited_main_approx: states.State,
    ground_states_approx: Sequence[states.State],
    excited_states_approx: Sequence[states.State],
    QN_basis: Sequence[states.State],
    H_rot: npt.NDArray[np.complex_],
    QN: Sequence[states.State],
    V_ref: npt.NDArray[np.complex_],
    pol_main: npt.NDArray[np.complex_] = np.array([0, 0, 1], dtype=np.complex_),
    pol_vecs: Sequence[npt.NDArray[np.complex_]] = [],
    relative_coupling: float = 1e-3,
    absolute_coupling: float = 1e-6,
    normalize_pol: bool = True,
) -> CouplingFields:
    assert isinstance(pol_main, np.ndarray), (
        "supply a Sequence of np.ndarrays with " "dtype np.complex_ for pol_vecs"
    )
    assert isinstance(pol_vecs[0], np.ndarray), (
        "supply a Sequence of np.ndarrays with " "dtype np.complex_ for pol_vecs"
    )
    if not np.issubdtype(pol_main.dtype, np.complex_):
        pol_main.astype(np.complex_)
    if not np.issubdtype(pol_vecs[0].dtype, np.complex_):
        pol_vecs = [pol.astype(np.complex_) for pol in pol_vecs]

    ground_states = states.find_exact_states(
        ground_states_approx, QN_basis, QN, H_rot, V_ref=V_ref
    )
    excited_states = states.find_exact_states(
        excited_states_approx, QN_basis, QN, H_rot, V_ref=V_ref
    )
    ground_main = states.find_exact_states(
        [ground_main_approx], QN_basis, QN, H_rot, V_ref=V_ref
    )[0]
    excited_main = states.find_exact_states(
        [excited_main_approx], QN_basis, QN, H_rot, V_ref=V_ref
    )[0]

    states.check_approx_state_exact_state(ground_main_approx, ground_main)
    states.check_approx_state_exact_state(excited_main_approx, excited_main)
    ME_main = generate_ED_ME_mixed_state(
        excited_main,
        ground_main,
        pol_vec=np.asarray(pol_main, dtype=np.complex_),
        normalize_pol=normalize_pol,
    )

    _ground_main: CoupledBasisState = ground_main.largest  # type: ignore
    _excited_main: CoupledBasisState = excited_main.largest  # type: ignore

    assert_transition_coupled_allowed(
        _ground_main, _excited_main, ΔmF_allowed=0 if pol_main[2] != 0 else 1
    )

    couplings = []
    for pol in pol_vecs:
        coupling = generate_coupling_matrix(
            QN,
            ground_states,
            excited_states,
            pol_vec=pol,
            reduced=False,
            normalize_pol=normalize_pol,
        )
        if normalize_pol:
            pol = pol.copy() / np.linalg.norm(pol)

        coupling[np.abs(coupling) < relative_coupling * np.max(np.abs(coupling))] = 0
        coupling[np.abs(coupling) < absolute_coupling] = 0
        couplings.append(CouplingField(polarization=pol, field=coupling))
    return CouplingFields(
        ground_main, excited_main, ME_main, ground_states, excited_states, couplings
    )


def generate_coupling_field_automatic(
    ground_states_approx: Sequence[states.State],
    excited_states_approx: Sequence[states.State],
    QN_basis: Sequence[states.State],
    H_rot: npt.NDArray[np.complex_],
    QN: Sequence[states.State],
    V_ref: npt.NDArray[np.complex_],
    pol_vecs: Sequence[npt.NDArray[np.complex_]],
    relative_coupling: float = 1e-3,
    absolute_coupling: float = 1e-6,
    normalize_pol: bool = True,
) -> CouplingFields:
    """Calculate the coupling fields for a transition for one or multiple
    polarizations.

    Args:
        ground_states_approx (list): list of approximate ground states
        excited_states_approx (list): list of approximate excited states
        QN_basis (Sequence[states.State]): Sequence of States the H_rot was constructed
                                            from
        H_rot (np.ndarray): System hamiltonian in the rotational frame
        QN (list): list of states in the system
        V_ref ([type]): [description]
        pol_vec (list): list of polarizations.
        relative_coupling (float): minimum relative coupling, set
                                            smaller coupling to zero.
                                            Defaults to 1e-3.
        absolute_coupling (float): minimum absolute coupling, set
                                            smaller couplings to zero.
                                            Defaults to 1e-6.

    Returns:
        dictionary: CouplingFields dataclass with the coupling information.
                    Attributes:
                        ground_main: main ground state
                        excited_main: main excited state
                        main_coupling: coupling strenght between main_ground
                                        and main_excited
                        ground_states: ground states in coupling
                        excited_states: excited_states in coupling
                        fields: list of CouplingField dataclasses, one for each
                                polarization, containing the polarization and coupling
                                field
    """
    assert isinstance(pol_vecs[0], np.ndarray), (
        "supply a Sequence of np.ndarrays with " "dtype np.float_ for pol_vecs"
    )
    pol_main = pol_vecs[0]
    ground_main_approx, excited_main_approx = select_main_states(
        ground_states_approx, excited_states_approx, pol_main
    )
    return generate_coupling_field(
        ground_main_approx=ground_main_approx,
        excited_main_approx=excited_main_approx,
        ground_states_approx=ground_states_approx,
        excited_states_approx=excited_states_approx,
        QN_basis=QN_basis,
        H_rot=H_rot,
        QN=QN,
        V_ref=V_ref,
        pol_main=pol_main,
        pol_vecs=pol_vecs,
        relative_coupling=relative_coupling,
        absolute_coupling=absolute_coupling,
        normalize_pol=normalize_pol,
    )
