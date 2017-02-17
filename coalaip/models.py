"""Low level data models for COALA IP entities.

Encapsulates the data modelling of COALA IP entities. Supports
model validation and the loading of data from a backing persistence
layer.

.. note:: This module should not be used directly to generate models,
          unless you are extending the built-ins for your own
          extensions. Instead, use the models that are contained in the
          entities (:mod:`.entities`) returned from the high-level
          functions (:mod:`.coalaip`).

.. warning:: The immutability guarantees given in this module are
             best-effort. There is no general way to achieve
             immutability in Python, but we try our hardest to make it
             so.
"""

import attr
import coalaip.model_validators as validators

from copy import copy
from functools import wraps
from types import MappingProxyType
from coalaip import context_urls
from coalaip.data_formats import _extract_ld_data, _make_context_immutable
from coalaip.exceptions import (
    ModelError,
    ModelDataError,
    ModelNotYetLoadedError,
)
from coalaip.utils import PostInitImmutable


def get_default_ld_context():
    return [context_urls.COALAIP, context_urls.SCHEMA]


DEFAULT_DATA_VALIDATOR = attr.validators.instance_of(MappingProxyType)


@attr.s(frozen=True, repr=False)
class Model:
    """Basic data model class for COALA IP entities. Includes Linked
    Data (JSON-LD) specifics.

    **Immutable (see :class:`~.PostInitImmutable` and attributes)**.

    Initialization may throw if attribute validation fails.

    Attributes:
        data (dict): Model data. Uses :attr:`validator` for validation.
        ld_type (str): @type of the entity
        ld_id (str): @id of the entity
        ld_context (str or dict or [str|dict], keyword): "@context" for
            the entity as either a string URL or array of string URLs or
            dictionaries. See the `JSON-LD spec on contexts
            <https://www.w3.org/TR/json-ld/#the-context>`_ for more
            information.
        validator (callable): A validator complying to :mod:`attr`'s
            `validator API <https://attrs.readthedocs.io/en/stable/examples.html#validators>`_
            that will validate :attr:`data`
    """
    data = attr.ib(convert=lambda data: MappingProxyType(copy(data)),
                   validator=validators.use_model_attr('validator'))
    ld_type = attr.ib(validator=attr.validators.instance_of(str))
    ld_id = attr.ib(default='', validator=attr.validators.instance_of(str))
    ld_context = attr.ib(default=attr.Factory(get_default_ld_context),
                         convert=_make_context_immutable)
    validator = attr.ib(default=DEFAULT_DATA_VALIDATOR,
                        validator=validators.is_callable)

    def __repr__(self):
        return '{name}(type={type}, context={context}, data={data})'.format(
            name=self.__class__.__name__,
            type=self.ld_type,
            context=self.ld_context,
            data=self.data,
        )


@attr.s(init=False, repr=False)
class LazyLoadableModel(PostInitImmutable):
    """Lazy loadable data model class for COALA IP entities.

    **Immutable (see :class:`.PostInitImmutable` and attributes)**.

    Similar to :class:`~.Model`, except it allows the model data to be
    lazily loaded afterwards from a backing persistence layer through a
    plugin.

    Attributes:
        loaded_model (:class:`~.Model`): Loaded model from a backing
            persistence layer. Initially ``None``.
            Not initable.
            Note that this attribute is only immutable after it's been
            set once after initialization (e.g. after :meth:`load`).
        ld_type: See :attr:`~.Model.ld_type`
        ld_context: See :attr:`~.Model.ld_context`
        validator: See :attr:`~.Model.validator`
    """

    # See __init__() for defaults
    ld_type = attr.ib(validator=attr.validators.instance_of(str))
    ld_context = attr.ib()
    validator = attr.ib(validator=validators.is_callable)
    loaded_model = attr.ib(init=False)

    def __init__(self, ld_type, ld_id=None, ld_context=None,
                 validator=DEFAULT_DATA_VALIDATOR, data=None):
        """Initialize a :class:`~.LazyLoadableModel` instance.

        If a :attr:`data` is provided, a :class:`Model` is generated
        as the instance's :attr:`~.LazyLoadableModel.loaded_model` using
        the given arguments.

        Ignores :attr:`ld_id`, see the :meth:`ld_id` property instead.
        """

        self.ld_type = ld_type
        self.ld_context = _make_context_immutable(ld_context or
                                                  get_default_ld_context())
        self.validator = validator
        self.loaded_model = None

        attr.validate(self)
        if data:
            self.loaded_model = Model(data=data, ld_type=self.ld_type,
                                      ld_context=self.ld_context,
                                      validator=self.validator)

    def __repr__(self):
        return '{name}(type={type}, context={context}, data={data})'.format(
            name=self.__class__.__name__,
            type=self.ld_type,
            context=self.ld_context,
            data=self.loaded_model.data if self.loaded_model else 'Not loaded',
        )

    @property
    def data(self):
        """dict: Model data.

        Raises :exc:`~.ModelNotYetLoadedError` if the data has not been
        loaded yet.
        """

        if self.loaded_model is None:
            raise ModelNotYetLoadedError()
        return self.loaded_model.data

    @property
    def ld_id(self):
        """str: @id of the entity.

        Raises :exc:`~.ModelNotYetLoadedError` if the data has not been
        loaded yet.
        """

        if self.loaded_model is None:
            raise ModelNotYetLoadedError()
        return self.loaded_model.ld_id

    def load(self, persist_id, *, plugin):
        """Load the :attr:`~.LazyLoadableModel.loaded_model` of this
        instance. Noop if model was already loaded.

        Args:
            persist_id (str): Id of this model on the persistence layer
            plugin (subclass of :class:`~.AbstractPlugin`): Persistence
                layer plugin to load from

        Raises:
            :exc:`~.ModelDataError`: If the loaded entity's data fails
                validation from :attr:`~.LazyLoadableEntity.validator`
                or its type or context differs from their expected
                values
            :exc:`~.EntityNotFoundError`: If the entity could not be
                found on the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """
        if self.loaded_model:
            return

        persist_data = plugin.load(persist_id)

        extracted_ld_result = _extract_ld_data(persist_data)
        loaded_data = extracted_ld_result.data
        loaded_type = extracted_ld_result.ld_type
        loaded_id = extracted_ld_result.ld_id
        loaded_context = extracted_ld_result.ld_context

        # Sanity check the loaded type and context
        if loaded_type and loaded_type != self.ld_type:
            raise ModelDataError(
                ("Loaded @type ('{loaded_type}') differs from entity's "
                 "@type ('{self_type})'").format(loaded_type=loaded_type,
                                                 self_type=self.ld_type)
            )
        if loaded_context and list(loaded_context) != list(self.ld_context):
            raise ModelDataError(
                ("Loaded context ('{loaded_ctx}') differs from entity's "
                 "context ('{self_ctx}')").format(loaded_ctx=loaded_context,
                                                  self_ctx=self.ld_context)
            )

        kwargs = {
            'data': loaded_data,
            'validator': self.validator,
            'ld_type': self.ld_type,
            'ld_context': self.ld_context,
        }
        if loaded_id:
            kwargs['ld_id'] = loaded_id

        self.loaded_model = Model(**kwargs)


def _model_factory(*, data=None, model_cls=Model, **kwargs):
    return model_cls(data=data, **kwargs)


def _raise_if_not_given_ld_type(strict_ld_type, *, for_model):
    def decorator(func):
        @wraps(func)
        def raise_if_not_given_type(*args, **kwargs):
            ld_type = kwargs.get('ld_type')
            if ld_type is not None and ld_type != strict_ld_type:
                raise ModelError("{model_name} models must be of '@type' "
                                 "'{strict_type}. Given '{given_type}'"
                                 .format(model_name=for_model,
                                         strict_type=strict_ld_type,
                                         given_type=ld_type))
            return func(*args, **kwargs)
        return raise_if_not_given_type
    return decorator


@_raise_if_not_given_ld_type('AbstractWork', for_model='Work')
def work_model_factory(*, validator=validators.is_work_model, **kwargs):
    """Generate a Work model.

    Expects ``data``, ``validator``, ``model_cls``, and ``ld_context``
    as keyword arguments.

    Raises:
        :exc:`ModelError`: If a non-'AbstractWork' ``ld_type`` keyword
            argument is given.
    """
    kwargs['ld_type'] = 'AbstractWork'
    return _model_factory(validator=validator, **kwargs)


def manifestation_model_factory(*, validator=validators.is_manifestation_model,
                                ld_type='CreativeWork', **kwargs):
    """Generate a Manifestation model.

    Expects ``data``, ``validator``, ``model_cls``, ``ld_type``, and
    ``ld_context`` as keyword arguments.
    """
    return _model_factory(validator=validator, ld_type=ld_type, **kwargs)


def right_model_factory(*, validator=validators.is_right_model,
                        ld_type='Right', **kwargs):
    """Generate a Right model.

    Expects ``data``, ``validator``, ``model_cls``, ``ld_type``, and
    ``ld_context`` as keyword arguments.
    """
    return _model_factory(validator=validator, ld_type=ld_type, **kwargs)


@_raise_if_not_given_ld_type('Copyright', for_model='Copyright')
def copyright_model_factory(*, validator=validators.is_copyright_model,
                            **kwargs):
    """Generate a Copyright model.

    Expects ``data``, ``validator``, ``model_cls``, and ``ld_context``
    as keyword arguments.

    Raises:
        :exc:`ModelError`: If a non-'Copyright' ``ld_type`` keyword
            argument is given.
    """
    kwargs['ld_type'] = 'Copyright'
    return _model_factory(validator=validator, **kwargs)


@_raise_if_not_given_ld_type('RightsTransferAction',
                             for_model='RightsAssignment')
def rights_assignment_model_factory(**kwargs):
    """Generate a RightsAssignment model.

    Expects ``data``, ``validator``, ``model_cls``, and ``ld_context``
    as keyword arguments.

    Raises:
        :exc:`ModelError`: If a non-'RightsTransferAction' ``ld_type``
            keyword argument is given.
    """
    kwargs['ld_type'] = 'RightsTransferAction'
    return _model_factory(**kwargs)
