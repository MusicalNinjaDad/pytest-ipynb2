import pytest

pytest_plugins = ["pytester", "pytest_ipynb2._pytester_helpers"]


def pytest_configure(config: pytest.Config) -> None:
    """Register custom xfail mark."""
    config.addinivalue_line("markers", "xfail_for: xfail specified tests dynamically")


def pytest_collection_modifyitems(items: list[pytest.Function]) -> None:
    """xfail on presence of a custom marker: `xfail_for(tests:list[str], reasons:list[str])`."""  # noqa: D403
    for item in items:
        test_name = item.originalname.removeprefix("test_")
        if xfail_for := item.get_closest_marker("xfail_for"):
            for xfail_test, reason in zip(xfail_for.kwargs.get("tests"), xfail_for.kwargs.get("reasons")):
                if xfail_test == test_name:
                    item.add_marker(pytest.mark.xfail(reason=reason, strict=True))
