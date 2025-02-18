import pytest

pytest_plugins = ["pytester", "pytest_ipynb2.pytester_helpers"]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Function]) -> None:  # noqa: ARG001
    """xfail on presence of a custom marker: "xfail_testname" where testname is "one" for `test_one`."""  # noqa: D403
    for item in items:
        test_name = item.originalname.removeprefix("test_")
        xfail_marker_name = f"xfail_{test_name}"

        marker_present = item.get_closest_marker(xfail_marker_name)

        if marker_present:
            reason = marker_present.kwargs.get("reason", f"Test {item.name} is expected to fail.")
            strict = marker_present.kwargs.get("strict", True)
            item.add_marker(pytest.mark.xfail(reason=reason, strict=strict))
