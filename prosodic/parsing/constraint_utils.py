from ..imports import *
from .constraints import *


def get_all_constraints():
    return {
        name: obj for name, obj in globals().items()
        if callable(obj) and hasattr(obj, 'scope')
    }

def get_default_constraint_names():
    return DEFAULT_CONSTRAINT_NAMES

def get_default_constraints():
    all_constraints = get_all_constraints()
    default_names = get_default_constraint_names()
    return [all_constraints[name] for name in default_names]



def get_constraint_descriptions():
    return {name: func.desc for name, func in get_all_constraints().items()}

def get_constraint_scope(constraint):
    if callable(constraint):
        return getattr(constraint, 'scope', 'unknown')
    elif isinstance(constraint, str):
        all_constraints = get_all_constraints()
        if constraint in all_constraints:
            return all_constraints[constraint].scope
    return 'unknown'

def get_constraints(constraint_names=None, scope=None):
    """
    Get constraints with 'parse' scope, optionally filtered by names.

    Args:
        constraint_strings (list, optional): List of constraint names to filter by.

    Returns:
        dict: A dictionary of constraint functions with 'parse' scope.
    """
    all_constraints = {
        name: func for name, func in get_all_constraints().items()
        if scope is None or func.scope == scope
    }
    if constraint_names is None:
        return all_constraints
    else:
        return {
            name: func for name, func in all_constraints.items()
            if name in constraint_names
        }
    


def get_parse_constraints(constraint_names=None):
    return get_constraints(constraint_names, scope='parse')

def get_position_constraints(constraint_names=None):
    return get_constraints(constraint_names, scope='position')

def parse_constraint_string(constraint_string):
    parts = constraint_string.split('/')
    constraint_name = parts[0].strip()
    weight = float(parts[1]) if len(parts) > 1 else 1.0
    return constraint_name, weight

def parse_constraint_weights(constraint_list):
    if isinstance(constraint_list, str):
        constraint_list = constraint_list.split()
    return {name:weight for name, weight in [parse_constraint_string(c) for c in constraint_list]}

