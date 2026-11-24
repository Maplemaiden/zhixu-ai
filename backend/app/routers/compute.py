from fastapi import APIRouter, HTTPException

from app.solvers.expected_value import ExpectedValueInput, solve as solve_ev
from app.solvers.uncertainty import UncertaintyInput, solve as solve_unc

router = APIRouter(prefix="/compute", tags=["compute"])


@router.post("/expected_value")
def compute_expected_value(body: ExpectedValueInput):
    try:
        return solve_ev(body).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/uncertainty")
def compute_uncertainty(body: UncertaintyInput):
    try:
        return solve_unc(body).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
