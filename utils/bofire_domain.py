"""
BoFire domain construction.

Builds a BoFire ``Domain`` from parameter/objective/constraint definitions
produced by the Dash UI stores. Supports:

- Continuous, discrete, and categorical inputs
- Categorical inputs with numeric descriptors (solvents, bases)
- Optional discretization of continuous inputs into a fixed grid
- Categorical-exclude constraints for boiling / melting point limits
- Linear inequality and equality constraints between parameters

Creation of ``CategoricalDescriptorInput`` is delegated to a dedicated worker
thread to avoid Flask/Dash request-context interference with Pydantic
validators.
"""

import traceback
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Dict, List, Optional

import numpy as np

from bofire.data_models.api import Constraints, Domain, Inputs, Outputs
from bofire.data_models.constraints.api import (
    CategoricalExcludeConstraint,
    LinearEqualityConstraint,
    LinearInequalityConstraint,
    SelectionCondition,
    ThresholdCondition,
)
from bofire.data_models.features.api import (
    CategoricalDescriptorInput,
    CategoricalInput,
    ContinuousInput,
    ContinuousOutput,
    DiscreteInput,
)
from bofire.data_models.objectives.api import MaximizeObjective, MinimizeObjective

from utils.descriptor_data import get_descriptor_values

# Dedicated worker thread used to instantiate CategoricalDescriptorInput
# outside the Flask request context.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bofire_creator")


def check_parameter_scales(domain: Domain) -> List[str]:
    """Return human-readable recommendations about input parameter scales."""
    recommendations: List[str] = []

    ranges = [
        (f.key, f.bounds[1] - f.bounds[0], f.bounds[0], f.bounds[1])
        for f in domain.inputs.features
        if isinstance(f, ContinuousInput)
    ]
    if not ranges:
        return recommendations

    range_values = [r[1] for r in ranges]
    if len(range_values) > 1:
        if max(range_values) / (min(range_values) + 1e-10) > 100:
            recommendations.append(
                "Large scale differences detected between parameters. "
                "Consider rescaling or using log-scale."
            )

    for name, _, lb, ub in ranges:
        if lb > 0 and ub / lb > 100:
            recommendations.append(
                f"Parameter '{name}' spans multiple orders of magnitude. "
                "Consider log-transform for better GP performance."
            )

    return recommendations


def _create_categorical_descriptor_safely(name, categories, descriptors, values):
    """
    Instantiate a ``CategoricalDescriptorInput`` on a worker thread.

    Descriptors that are constant across all categories are dropped, since
    BoFire rejects them during validation.
    """
    print(f"   Thread {threading.current_thread().name}: creating CategoricalDescriptorInput")

    if values and descriptors:
        keep_indices = [
            i for i in range(len(descriptors))
            if len({row[i] for row in values}) > 1
        ]
        if len(keep_indices) < len(descriptors):
            removed = [descriptors[i] for i in range(len(descriptors)) if i not in keep_indices]
            print(f"   Removed {len(removed)} constant descriptor(s): {removed}")
            descriptors = [descriptors[i] for i in keep_indices]
            values = [[row[i] for i in keep_indices] for row in values]

    allowed_list = [True] * len(categories)

    try:
        return CategoricalDescriptorInput(
            key=name,
            categories=categories,
            allowed=allowed_list,
            descriptors=descriptors,
            values=values,
        )
    except KeyError as e:
        print(f"   Normal constructor failed ({e}), falling back to model_construct")
        return CategoricalDescriptorInput.model_construct(
            key=name,
            categories=categories,
            allowed=allowed_list,
            descriptors=descriptors,
            values=values,
        )


def _build_input_features(
    parameter_data: List[Dict],
    solvent_config: Optional[Dict],
    base_config: Optional[Dict],
    discretization_config: Optional[Dict],
) -> List:
    """Translate the UI parameter list into BoFire input features."""
    features = []

    for param in parameter_data:
        typ = param.get("type")
        name = param.get("name")
        type_info = param.get("type_info", {})

        if typ == "float":
            lb, ub = type_info.get("range", [None, None])
            if lb is None or ub is None:
                raise ValueError(f"Parameter '{name}' missing bounds.")
            unit = type_info.get("unit")

            step = (discretization_config or {}).get(name)
            if step and step > 0:
                values = [round(v, 6) for v in np.arange(lb, ub + step / 2, step)]
                print(f"   Discretizing '{name}': {len(values)} values from {lb} to {ub} (step={step})")
                features.append(DiscreteInput(key=name, values=values, unit=unit))
            else:
                features.append(ContinuousInput(key=name, bounds=[lb, ub], unit=unit))

        elif typ == "int":
            values = type_info.get("range", [])
            if not values:
                raise ValueError(f"Discrete parameter '{name}' has no values.")
            features.append(DiscreteInput(key=name, values=values, unit=type_info.get("unit")))

        elif typ == "cat":
            categories = type_info.get("values", [])
            if not categories:
                raise ValueError(f"Categorical parameter '{name}' has no values.")

            descriptor_feature = _try_build_descriptor_feature(
                name, param, solvent_config, base_config
            )
            if descriptor_feature is not None:
                features.append(descriptor_feature)
            else:
                features.append(CategoricalInput(key=name, categories=categories))

        else:
            raise ValueError(f"Unknown parameter type '{typ}' for parameter '{name}'.")

    return features


def _try_build_descriptor_feature(name, param, solvent_config, base_config):
    """
    Build a ``CategoricalDescriptorInput`` if this parameter is the configured
    solvent or base; otherwise return ``None``.
    """
    for cfg, categories_key, kind in (
        (solvent_config, "solvents", "solvent"),
        (base_config, "bases", "base"),
    ):
        if not cfg or cfg.get("param_id") != param.get("id"):
            continue

        categories = list(cfg.get(categories_key, []))
        descriptors = list(cfg.get("descriptors", []))
        if not (descriptors and categories):
            return None

        print(f"Creating CategoricalDescriptorInput for {kind.capitalize()}")
        descriptor_values = get_descriptor_values(categories, descriptors, kind)

        future = _executor.submit(
            _create_categorical_descriptor_safely,
            name, categories, descriptors, descriptor_values,
        )
        return future.result()

    return None


def _build_output_features(objective_data: Optional[List[Dict]]) -> List[ContinuousOutput]:
    outputs = []
    for obj in objective_data or []:
        obj_name = obj.get("name")
        if not obj_name:
            continue

        direction = obj.get("direction")
        bounds = (obj.get("lower_bound", 0.0), obj.get("upper_bound", 1.0))

        if direction in ("minimize", "min"):
            objective = MinimizeObjective(w=1.0, bounds=bounds)
        elif direction in ("maximize", "max"):
            objective = MaximizeObjective(w=1.0, bounds=bounds)
        else:
            raise ValueError(f"Unknown objective direction: {direction}")

        outputs.append(ContinuousOutput(key=obj_name, objective=objective))
    return outputs


def _build_phase_constraints(
    constraints_config: Dict,
    input_features: List,
    solvent_config: Optional[Dict],
) -> List:
    """Build CategoricalExclude constraints from boiling/melting point limits."""
    constraints = []
    phase_constraints = constraints_config.get("constraints") or []
    if not phase_constraints:
        return constraints

    print(f"Processing {len(phase_constraints)} phase constraint(s)...")

    if not solvent_config:
        print("No solvent_config provided, cannot create phase constraints")
        return constraints

    from utils.descriptor_data import SOLVENT_DESCRIPTORS

    solvents = solvent_config.get("solvents", [])
    solvent_param_name = solvent_config.get("param_name", "Solvent")
    bp_dict = {s: SOLVENT_DESCRIPTORS[s]["bp"] for s in solvents if s in SOLVENT_DESCRIPTORS and "bp" in SOLVENT_DESCRIPTORS[s]}
    mp_dict = {s: SOLVENT_DESCRIPTORS[s]["mp"] for s in solvents if s in SOLVENT_DESCRIPTORS and "mp" in SOLVENT_DESCRIPTORS[s]}

    solvent_feature = next((f for f in input_features if f.key == solvent_param_name), None)
    if not solvent_feature:
        print(f"Solvent parameter '{solvent_param_name}' not found in inputs, skipping phase constraints")
        return constraints
    if not bp_dict and not mp_dict:
        print("No boiling/melting points available, skipping phase constraints")
        return constraints

    safety_margin = constraints_config.get("safety_margin", 5.0)

    for constraint in phase_constraints:
        constraint_type = constraint.get("type", "less_than_bp")
        param_name = constraint["parameter_name"]
        param_feature = next((f for f in input_features if f.key == param_name), None)
        if not param_feature:
            print(f"   Parameter '{param_name}' not found in inputs, skipping constraint")
            continue

        if constraint_type == "less_than_bp":
            source, operator, sign = bp_dict, ">=", -1
        elif constraint_type == "greater_than_mp":
            source, operator, sign = mp_dict, "<=", +1
        else:
            print(f"   Unknown constraint type: {constraint_type}")
            continue

        if not source:
            print(f"   No reference temperatures for {constraint_type}, skipping")
            continue

        for solvent_name, ref_temp in source.items():
            try:
                temp_limit = ref_temp + sign * safety_margin

                if isinstance(param_feature, DiscreteInput):
                    if constraint_type == "less_than_bp":
                        invalid = [v for v in param_feature.values if v >= temp_limit]
                        if not invalid:
                            continue
                        temp_limit = min(invalid)
                    else:
                        invalid = [v for v in param_feature.values if v <= temp_limit]
                        if not invalid:
                            continue
                        temp_limit = max(invalid)

                constraints.append(
                    CategoricalExcludeConstraint(
                        features=[solvent_param_name, param_name],
                        conditions=[
                            SelectionCondition(selection=[solvent_name]),
                            ThresholdCondition(threshold=temp_limit, operator=operator),
                        ],
                    )
                )
                print(
                    f"   {constraint_type}: {solvent_name} -> {param_name} "
                    f"threshold={temp_limit} (ref={ref_temp}, margin={safety_margin})"
                )
            except Exception as e:
                print(f"   Failed to create {constraint_type} constraint for {solvent_name}: {e}")
                traceback.print_exc()

    return constraints


def _build_linear_constraints(constraints_config: Dict, input_features: List) -> List:
    """Build linear (in)equality constraints between parameter pairs."""
    constraints = []
    ineq_list = constraints_config.get("inequality_constraints") or []
    if not ineq_list:
        return constraints

    print(f"Processing {len(ineq_list)} linear constraint(s)...")
    keys = {f.key for f in input_features}

    for ineq in ineq_list:
        param_left = ineq["param_left"]
        param_right = ineq["param_right"]
        offset = ineq.get("offset", 0.0)
        relation = ineq.get("relation", "leq")

        missing = [p for p in (param_left, param_right) if p not in keys]
        if missing:
            print(f"   Linear constraint skipped: missing parameter(s) {missing}")
            continue

        try:
            # param_left (<=|=) param_right + offset  <=>  1*left - 1*right (<=|=) offset
            kwargs = dict(
                features=[param_left, param_right],
                coefficients=[1.0, -1.0],
                rhs=offset,
            )
            if relation == "eq":
                constraints.append(LinearEqualityConstraint(**kwargs))
                print(f"   Linear equality: {param_left} = {param_right} + {offset}")
            else:
                constraints.append(LinearInequalityConstraint(**kwargs))
                print(f"   Linear inequality: {param_left} <= {param_right} + {offset}")
        except Exception as e:
            print(f"   Failed to create linear constraint: {e}")
            traceback.print_exc()

    return constraints


def create_bofire_domain_from_store(
    parameter_data: List[Dict],
    objective_data: Optional[List[Dict]] = None,
    solvent_config: Optional[Dict] = None,
    base_config: Optional[Dict] = None,
    constraints_config: Optional[Dict] = None,
    discretization_config: Optional[Dict] = None,
) -> Domain:
    """
    Build a BoFire ``Domain`` from Dash store payloads.

    Args:
        parameter_data: Parameters from ``parameter-store``.
        objective_data: Objectives from ``objective-store``.
        solvent_config: Solvent parameter config (descriptors, categories).
        base_config: Base parameter config (descriptors, categories).
        constraints_config: Phase constraints (BP/MP) and linear constraints.
        discretization_config: Mapping ``{parameter_name: step}`` that turns a
            continuous parameter into a ``DiscreteInput`` grid.

    Returns:
        The assembled BoFire ``Domain``.
    """
    if not parameter_data:
        raise ValueError("No parameters provided to create domain.")

    input_features = _build_input_features(
        parameter_data, solvent_config, base_config, discretization_config
    )
    inputs = Inputs(features=input_features)
    outputs = Outputs(features=_build_output_features(objective_data))

    constraint_list: List = []
    if constraints_config:
        constraint_list.extend(
            _build_phase_constraints(constraints_config, input_features, solvent_config)
        )
        constraint_list.extend(
            _build_linear_constraints(constraints_config, input_features)
        )

    if constraint_list:
        domain = Domain(
            inputs=inputs,
            outputs=outputs,
            constraints=Constraints(constraints=constraint_list),
        )
        print(f"Created domain with {len(constraint_list)} constraint(s)")
    else:
        domain = Domain(inputs=inputs, outputs=outputs)
        print("Created domain with no constraints")

    for rec in check_parameter_scales(domain):
        print(rec)

    return domain
