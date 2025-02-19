import pytest

@pytest.mark.parametrize(
   'val',
   [
       pytest.param(True, id='pass'),
       pytest.param(False, marks=pytest.mark.xfail(reason="xfailed"), id='fail'),
   ],
)
def test_params(val):
   assert val