"""Data Contracts — formal schema definitions for each government source.
Each contract defines the expected fields, types, constraints, and validation
rules for records ingested from a specific source.
"""

from runtime.data_fabric_runtime.contracts.base import BaseSourceContract
from runtime.data_fabric_runtime.contracts.balady import BaladyContract
from runtime.data_fabric_runtime.contracts.taqeem import TaqeemContract
from runtime.data_fabric_runtime.contracts.ncnp import NcnpContract
from runtime.data_fabric_runtime.contracts.najiz import NajizContract
from runtime.data_fabric_runtime.contracts.rega import RegaContract

__all__ = [
    "BaseSourceContract",
    "BaladyContract",
    "TaqeemContract",
    "NcnpContract",
    "NajizContract",
    "RegaContract",
]
