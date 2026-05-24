import pytest

from app.services.termination_service import TerminationService


@pytest.mark.parametrize(
    "deposit,total,expected",
    [
        (0, 0, (0, 0, 0)),
        (0, 100, (0, 0, 100)),
        (100, 0, (0, 100, 0)),
        (100, 50, (50, 50, 0)),
        (100, 150, (100, 0, 50)),
        (-10, 100, (0, 0, 100)),
        (100, -10, (0, 100, 0)),
    ],
)
def test_apply_deposit(deposit, total, expected):
    assert TerminationService._apply_deposit(deposit, total) == expected

