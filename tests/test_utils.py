from pytest import raises


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
