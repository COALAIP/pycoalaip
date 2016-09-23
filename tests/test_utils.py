from pytest import fixture, raises


@fixture
def base_dict():
    return {'foo': 'foo', 'bar': {'baz': 'baz'}}


@fixture
def override_foo_dict():
    return {'foo': 'overridden_foo'}


@fixture
def override_bar_dict():
    return {'bar': 'overriden_bar'}


@fixture
def override_all_dict():
    return {'foo': 'overriden_both', 'bar': 'overriden_both'}


@fixture
def override_all_tuple_iter():
    return [('foo', 'tuple_overriden_foo'), ('bar', 'tuple_overriden_bar')]


def test_post_init_immutable():
    from attr.exceptions import FrozenInstanceError
    from coalaip.utils import PostInitImmutable

    class Immutable(PostInitImmutable):
        def __init__(self, attr1):
            self.attr1 = attr1
            self.attr2 = None

    immutable = Immutable('attr1')
    with raises(FrozenInstanceError):
        immutable.attr1 = 'other_attr'

    # Note that attr2 can be set only once
    immutable.attr2 = 'attr2'
    with raises(FrozenInstanceError):
        immutable.attr2 = 'other_attr'


def test_extend_dict_single_arg(base_dict):
    from coalaip.utils import extend_dict
    copy = extend_dict(base_dict)

    # Returns a copy of the original if no other arguments given
    assert copy == base_dict

    copy['foo'] = 'changed_dict'
    assert copy != base_dict


def test_extend_dict_single_override(base_dict, override_foo_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict)

    # Returns a copy of the original with the 'foo' key overriden
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict['bar'] == base_dict['bar']
    assert overriden_dict['foo'] == override_foo_dict['foo']


def test_extend_dict_multiple_override(base_dict, override_foo_dict,
                                       override_bar_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict,
                                 override_bar_dict)

    # Returns a copy of the original with the 'foo' and 'bar' keys overriden
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict != override_bar_dict
    assert overriden_dict['foo'] == override_foo_dict['foo']
    assert overriden_dict['bar'] == override_bar_dict['bar']


def test_extend_dict_last_override_kept(base_dict, override_foo_dict,
                                        override_bar_dict, override_all_dict):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict,
                                 override_bar_dict, override_all_dict)

    # Returns a copy with the last key override being kept
    assert overriden_dict != base_dict
    assert overriden_dict != override_foo_dict
    assert overriden_dict != override_bar_dict
    assert overriden_dict == override_all_dict


def test_extend_dict_tuple_override(base_dict, override_all_tuple_iter):
    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_all_tuple_iter)

    # Returns a copy that has overriden all keys from the tuple iter
    assert overriden_dict == dict(override_all_tuple_iter)


def test_extend_dict_skips_none(base_dict, override_foo_dict,
                                override_bar_dict):

    from coalaip.utils import extend_dict
    overriden_dict = extend_dict(base_dict, override_foo_dict)
    overriden_with_none_dict = extend_dict(base_dict, None, override_foo_dict,
                                           None)

    # Results in the same dict as if the `None`s weren't given
    assert overriden_dict == overriden_with_none_dict
