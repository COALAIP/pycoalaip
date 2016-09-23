"""Validators for COALA IP models (:mod:`coalaip.models`)"""

from coalaip.exceptions import ModelDataError


def is_callable(instance, attribute, value):
    """Raises a :exc:`TypeError` if the value is not a callable"""

    if not callable(value):
        raise TypeError("'{}' must be callable".format(attribute.name))


def use_model_attr(attr):
    """Use the validator set on a separate attribute on the class"""

    def use_model_validator(instance, attribute, value):
        getattr(instance, attr)(instance, attribute, value)
    return use_model_validator


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


def is_work_model(instance, attribute, value):
    """Must not include keys that indicate the model is a
    :class:`~.Manifestation` (e.g. ``manifestationOfWork`` or
    ``isManifestation == True``).
    """

    instance_name = instance.__class__.__name__
    is_creation_model(instance, attribute, value)

    if 'manifestationOfWork' in value:
        err_str = ("'manifestationOfWork' must not be given in the '{attr}' "
                   "parameter of a '{cls}'").format(attr=attribute.name,
                                                    cls=instance_name)
        raise ModelDataError(err_str)

    is_manifestation = value.get('isManifestation', False)
    if is_manifestation is not False:
        err_str = ("'isManifestation' must be False if given in the "
                   "'{attr}' parameter of a '{cls}'. Given "
                   "'{value}").format(attr=attribute.name,
                                      cls=instance_name,
                                      value=is_manifestation)
        raise ModelDataError(err_str)


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
        raise ModelDataError(err_str)

    is_manifestation = value.get('isManifestation', True)
    if is_manifestation is not True:
        err_str = ("'isManifestation' must be True if given in the "
                   "'{attr}' parameter of a '{cls}'. Given "
                   "'{value}'").format(attr=attribute.name,
                                       cls=instance_name,
                                       value=is_manifestation)
        raise ModelDataError(err_str)


def is_right_model(instance, attribute, value):
    """Must include either a ``rightsOf`` or ``allowedBy`` key (but not
    both):

        - ``rightsOf`` indicates that the Right contains full rights to
            an existing Manifestation or Work
        - ``allowedBy`` indicates that the Right is derived from and
            allowed by a source Right.
    """

    instance_name = instance.__class__.__name__
    rights_of = value.get('rightsOf')
    allowed_by = value.get('allowedBy')
    if rights_of is not None and not isinstance(rights_of, str):
        raise ModelDataError(("'rightsOf' must be given as a string in "
                              "the '{attr}' parameter of a '{cls}'. Given "
                              "'{value}'").format(attr=attribute.name,
                                                  cls=instance_name,
                                                  value=rights_of))
    if allowed_by is not None and not isinstance(allowed_by, str):
        raise ModelDataError(("'allowedBy' must be given as a string in "
                              "the '{attr}' parameter of a '{cls}'. Given "
                              "'{value}'").format(attr=attribute.name,
                                                  cls=instance_name,
                                                  value=rights_of))
    if not (bool(rights_of) ^ bool(allowed_by)):
        raise ModelDataError(("One and only one of 'rightsOf' or "
                              "'allowedBy' can be given in the '{}' of "
                              "a '{cls}'.").format(attribute.name,
                                                   cls=instance_name))


def is_copyright_model(instance, attribute, value):
    """Must include at least a ``rightsOf`` key."""
    is_right_model(instance, attribute, value)

    if 'allowedBy' in value:
        instance_name = instance.__class__.__name__
        err_str = ("'allowedBy' must not be given in the '{attr}' parameter "
                   "of a '{cls}'").format(attr=attribute.name,
                                          cls=instance_name)
        raise ModelDataError(err_str)
