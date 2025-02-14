# ruff: noqa
# This cell sets some global variables

x = 1
y = 2

x + y

# Define a function


def adder(a, b):
    return a + b


def test_adder():
    assert adder(1, 2) == 3


def test_globals():
    assert x == 1


def another_function(*args):
    return args
