from typing import Any, Literal

from .abstract.rsc_input import RscInput
from .abstract.rsc_output import RscOutput
from .rsc_aib import RscAib
from .rsc_aif import RscAif
from .rsc_aii import RscAii
from .rsc_aob import RscAob
from .rsc_aob_pulse import RscAobPulse
from .rsc_aoi import RscAoi
from .rsc_aoi_pulse import RscAoiPulse
from .rsc_di import RscDi
from .rsc_do import RscDo
from .rsc_do_pulse import RscDoPulse


def create_rsc_input(io_config: dict[str, Any]) -> RscInput:
    """
    Create appropriate input instance based on io_config.

    Args:
        io_config: Dictionary containing input configuration

    Returns:
        An instance of appropriate RscInput subclass
    """
    input_id = io_config.get("id")
    input_type = io_config.get("type", "").lower()
    input_title = io_config.get("title", f"Input {input_id}")
    input_unit = io_config.get("unit", "")

    match input_type:
        case "aif" | "float":
            return RscAif(input_id, input_title, input_unit)
        case "aii" | "integer":
            return RscAii(input_id, input_title, input_unit)
        case "aib" | "byte":
            return RscAib(input_id, input_title, input_unit)
        case "di" | "binary":
            return RscDi(input_id, input_title)
        case _:
            raise ValueError(f"Unknown input type: {input_type}")


def create_rsc_output(io_config: dict[str, Any]) -> RscOutput:
    """
    Create appropriate output instance based on io_config.

    Args:
        io_config: Dictionary containing output configuration

    Returns:
        An instance of appropriate RscOutput subclass
    """
    output_id = io_config.get("id")
    output_type = io_config.get("type", "").lower()
    output_title = io_config.get("title", f"Output {output_id}")
    output_unit = io_config.get("unit", "")

    match output_type:
        case "aob" | "byte":
            return RscAob(output_id, output_title, output_unit)
        case "aob_pulse" | "byte_pulse":
            return RscAobPulse(output_id, output_title, output_unit)
        case "aoi" | "integer":
            return RscAoi(output_id, output_title, output_unit)
        case "aoi_pulse" | "integer_pulse":
            return RscAoiPulse(output_id, output_title, output_unit)
        case "do" | "binary":
            return RscDo(output_id, output_title)
        case "do_pulse" | "binary_pulse":
            return RscDoPulse(output_id, output_title)
        case _:
            raise ValueError(f"Unknown output type: {output_type}")
