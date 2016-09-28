import attr

from pytest import fixture, mark, raises


@fixture
def test_is_callable_cls():
    from coalaip.model_validators import is_callable

    @attr.s
    class TestCallable:
        fn = attr.ib(validator=is_callable)

    return TestCallable


@fixture
def test_use_model_attr_cls():
    from coalaip.model_validators import use_model_attr

    @attr.s
    class TestUseModelAttr:
        validator = attr.ib()
        test = attr.ib(validator=use_model_attr('validator'))

    return TestUseModelAttr


@fixture
def create_test_does_not_contain_cls():
    from coalaip.model_validators import does_not_contain

    def create_cls(*avoid_keys):
        @does_not_contain(*avoid_keys)
        def validator(*args, **kwargs):
            pass

        @attr.s
        class TestDoesNotContain:
            data = attr.ib(validator=validator)

        return TestDoesNotContain

    return create_cls


def test_is_callable_passes_on_callable(test_is_callable_cls):
    test_is_callable_cls(lambda: True)


def test_is_callable_raises_on_non_callable(test_is_callable_cls):
    with raises(TypeError):
        test_is_callable_cls('fn')


def test_use_model_attr(mocker, test_use_model_attr_cls):
    validator_mock = mocker.Mock()
    test_val = 'test'

    test_use_model_attr_cls(validator=validator_mock, test=test_val)
    assert validator_mock.call_count == 1
    # Check positional 'value' arg of validator
    assert validator_mock.call_args[0][-1] == test_val


def test_use_model_attr_raises_if_validator_raises(mocker,
                                                   test_use_model_attr_cls):
    validator_mock = mocker.Mock()
    validator_mock.side_effect = TypeError()
    test_val = 'test'

    with raises(TypeError):
        test_use_model_attr_cls(validator=validator_mock, test=test_val)


def test_does_not_contain(create_test_does_not_contain_cls):
    cls = create_test_does_not_contain_cls('avoid', 'at', 'all', 'costs')
    cls(data={'no': 'bad', 'keys': 'here!'})


@mark.parametrize('data', [
    {'avoid': 'oops'},
    {'avoid': 'more', 'at': 'than', 'all': 'one'}
])
def test_does_not_contain_raises_on_bad_key(create_test_does_not_contain_cls,
                                            data):
    cls = create_test_does_not_contain_cls('avoid', 'at', 'all', 'costs')
    with raises(ValueError):
        cls(data)
