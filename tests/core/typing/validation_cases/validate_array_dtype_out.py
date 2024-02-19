from typing import TYPE_CHECKING

import numpy as np

from pyvista.core._validation import validate_array

if TYPE_CHECKING:
    # scalars
    reveal_type(validate_array(1.0, dtype_out=int))     # EXPECTED_TYPE: "int"
    reveal_type(validate_array(1, dtype_out=bool))      # EXPECTED_TYPE: "bool"
    reveal_type(validate_array(True, dtype_out=float))  # EXPECTED_TYPE: "float"

    # numpy arrays
    reveal_type(validate_array(np.array(1.0, dtype=float), dtype_out=int))    # EXPECTED_TYPE: "ndarray[Any, dtype[int]]"
    reveal_type(validate_array(np.array(1, dtype=int), dtype_out=bool))       # EXPECTED_TYPE: "ndarray[Any, dtype[bool]]"
    reveal_type(validate_array(np.array(True, dtype=bool), dtype_out=float))  # EXPECTED_TYPE: "ndarray[Any, dtype[float]]"

    # lists
    reveal_type(validate_array([1.0], dtype_out=int))           # EXPECTED_TYPE: "list[int]"
    reveal_type(validate_array([1], dtype_out=bool))            # EXPECTED_TYPE: "list[bool]"
    reveal_type(validate_array([True], dtype_out=float))        # EXPECTED_TYPE: "list[float]"
    reveal_type(validate_array([[1.0]], dtype_out=int))         # EXPECTED_TYPE: "list[list[int]]"
    reveal_type(validate_array([[1]], dtype_out=bool))          # EXPECTED_TYPE: "list[list[bool]]"
    reveal_type(validate_array([[True]], dtype_out=float))      # EXPECTED_TYPE: "list[list[float]]"
    reveal_type(validate_array([[[1.0]]], dtype_out=int))       # EXPECTED_TYPE: "ndarray[Any, dtype[int]]"
    reveal_type(validate_array([[[1]]], dtype_out=bool))        # EXPECTED_TYPE: "ndarray[Any, dtype[bool]]"
    reveal_type(validate_array([[[True]]], dtype_out=float))    # EXPECTED_TYPE: "ndarray[Any, dtype[float]]"
    reveal_type(validate_array([[[[1.0]]]], dtype_out=int))     # EXPECTED_TYPE: "ndarray[Any, dtype[int]]"
    reveal_type(validate_array([[[[1]]]], dtype_out=bool))      # EXPECTED_TYPE: "ndarray[Any, dtype[bool]]"
    reveal_type(validate_array([[[[True]]]], dtype_out=float))  # EXPECTED_TYPE: "ndarray[Any, dtype[float]]"

    # tuples
    reveal_type(validate_array((1.0,), dtype_out=int))              # EXPECTED_TYPE: "tuple[int]"
    reveal_type(validate_array((1,), dtype_out=bool))               # EXPECTED_TYPE: "tuple[bool]"
    reveal_type(validate_array((True,), dtype_out=float))           # EXPECTED_TYPE: "tuple[float]"
    reveal_type(validate_array(((1.0,),), dtype_out=int))           # EXPECTED_TYPE: "tuple[tuple[int]]"
    reveal_type(validate_array(((1,),), dtype_out=bool))            # EXPECTED_TYPE: "tuple[tuple[bool]]"
    reveal_type(validate_array(((True,),), dtype_out=float))        # EXPECTED_TYPE: "tuple[tuple[float]]"
    reveal_type(validate_array((((1.0,),),), dtype_out=int))        # EXPECTED_TYPE: "ndarray[Any, dtype[int]]"
    reveal_type(validate_array((((1,),),), dtype_out=bool))         # EXPECTED_TYPE: "ndarray[Any, dtype[bool]]"
    reveal_type(validate_array((((True,),),), dtype_out=float))     # EXPECTED_TYPE: "ndarray[Any, dtype[float]]"
    reveal_type(validate_array(((((1.0,),),),), dtype_out=int))     # EXPECTED_TYPE: "ndarray[Any, dtype[int]]"
    reveal_type(validate_array(((((1,),),),), dtype_out=bool))      # EXPECTED_TYPE: "ndarray[Any, dtype[bool]]"
    reveal_type(validate_array(((((True,),),),), dtype_out=float))  # EXPECTED_TYPE: "ndarray[Any, dtype[float]]"