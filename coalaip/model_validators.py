"""Validators for COALA IP models (:mod:`coalaip.models`)"""

from coalaip.exceptions import ModelDataError


def is_callable(instance, attribute, value):
    """Raises a :exc:`TypeError` if the value is not a callable."""

    if not callable(value):
        raise TypeError("'{}' must be callable".format(attribute.name))


def use_model_attr(attr):
    """Use the validator set on a separate attribute on the class."""

    def use_model_validator(instance, attribute, value):
        getattr(instance, attr)(instance, attribute, value)
    return use_model_validator


def does_not_contain(*avoid_keys, error_cls=ValueError):
    """Decorator: value must not contain any of the :attr:`avoid_keys`.
    """

    def decorator(func):
        def not_contains(instance, attribute, value):
            instance_name = instance.__class__.__name__

            num_matched_keys = len(set(avoid_keys) & value.keys())
            if num_matched_keys > 0:
                avoid_keys_str = ', '.join(avoid_keys)
                err_str = ("Given keys ({num_matched} of {{avoid_keys}} "
                           "that must not be given in the '{attr}' of a "
                           "'{cls}'").format(num_matched=num_matched_keys,
                                             avoid_keys=avoid_keys_str,
                                             attr=attribute.name,
                                             cls=instance_name)
                raise error_cls(err_str)

            return func(instance, attribute, value)
        return not_contains
    return decorator


def is_creation_model(instance, attribute, value):
    """Must include at least a ``name`` key."""

    creation_name = value.get('name')
    if not isinstance(creation_name, str):
        instance_name = instance.__class__.__name__
        err_str = ("'name' must be given as a string in the '{attr}' "
                   "parameter of a '{cls}'. Given "
                   "'{value}'").format(attr=attribute.name,
                                       cls=instance_name,
                                       value=creation_name)
        raise ModelDataError(err_str)


@does_not_contain('manifestationOfWork', error_cls=ModelDataError)
def is_work_model(instance, attribute, value):
    """Must not include keys that indicate the model is a
    :class:`~.Manifestation` (e.g. ``manifestationOfWork``).
    """

    is_creation_model(instance, attribute, value)


def is_manifestation_model(instance, attribute, value):
    """Must include a ``manifestationOfWork`` key."""

    instance_name = instance.__class__.__name__
    is_creation_model(instance, attribute, value)

    manifestation_of = value.get('manifestationOfWork')
    if not isinstance(manifestation_of, str):
        err_str = ("'manifestationOfWork' must be given as a string in the "
                   "'{attr}' parameter of a '{cls}'. Given "
                   "'{value}'").format(attr=attribute.name,
                                       cls=instance_name,
                                       value=manifestation_of)
        print(err_str)


@does_not_contain('rightsOf', error_cls=ModelDataError)
def is_right_model(instance, attribute, value):
    """Must include at least the ``source`` and ``license`` keys, but
    not a ``rightsOf`` key (``source`` indicates that the Right is
    derived from and allowed by a source Right; it cannot contain the
    full rights to a Creation).
    """

    for key in ['source', 'license']:
        key_value = value.get(key)
        if not isinstance(key_value, str):
            instance_name = instance.__class__.__name__
            raise ModelDataError(("'{key}' must be given as a string in "
                                  "the '{attr}' parameter of a '{cls}'. Given "
                                  "'{value}'").format(key=key,
                                                      attr=attribute.name,
                                                      cls=instance_name,
                                                      value=key_value))


@does_not_contain('source', error_cls=ModelDataError)
def is_copyright_model(instance, attribute, value):
    """Must include at least a ``rightsOf`` key, but not a ``source``
    key (``rightsOf`` indicates that the Right contains full rights to
    an existing Manifestation or Work; i.e. is a Copyright).
    """

    rights_of = value.get('rightsOf')
    if not isinstance(rights_of, str):
        instance_name = instance.__class__.__name__
        raise ModelDataError(("'rightsOf' must be given as a string in "
                              "the '{attr}' parameter of a '{cls}'. Given "
                              "'{value}'").format(attr=attribute.name,
                                                  cls=instance_name,
                                                  value=rights_of))
