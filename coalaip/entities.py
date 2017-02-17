"""Entities mirroring COALA IP's entity model.

Requires usage with a persistence layer plugin (see
:class:`~.AbstractPlugin`) for the creation and transfer of entities.
JSON, JSON-LD, and IPLD data formats are supported.

.. note:: This module should not be used directly to generate entities,
          unless you are extending the built-ins for your own
          extensions. Instead, use the high-level functions
          (:mod:`.coalaip`) that return instances of these entities.

.. warning:: The immutability guarantees given in this module are
             best-effort. There is no general way to achieve
             immutability in Python, but we try our hardest to make it
             so.
"""

import attr

from abc import ABC, abstractmethod
from coalaip.data_formats import (
    DataFormat,
    _copy_context_into_mutable,
    _data_format_resolver,
    _extract_ld_data,
)
from coalaip.exceptions import (
    EntityNotYetPersistedError,
    EntityPreviouslyCreatedError,
    ModelNotYetLoadedError,
    PersistenceError,
)
from coalaip.models import (
    Model,
    LazyLoadableModel,
    work_model_factory,
    manifestation_model_factory,
    right_model_factory,
    copyright_model_factory,
    rights_assignment_model_factory,
)
from coalaip.plugin import AbstractPlugin
from coalaip.utils import PostInitImmutable


@attr.s(repr=False)
class Entity(ABC, PostInitImmutable):
    """Abstract base class of all COALA IP entity models.

    **Immutable (see :class:`~.PostInitImmutable`)**.

    Implements base functionality for all COALA IP entities, including
    entity creation (:meth:`create`) and status queries (:attr:`status`)
    on the backing persistence layer provided by ``plugin``.

    Subclasses **must** implement their own :meth:`generate_model`;
    :meth:`generate_model` determines the semantics behind
    :attr:`~Entity.model` (its creation and validation).

    Attributes:
        model (:class:`~.Model` or :class:`~.LazyLoadableModel`): Model
            of the entity. Holds the data and Linked Data (JSON-LD)
            specifics.
        plugin (subclass of :class:`~.AbstractPlugin`): Persistence
            layer plugin used by the Entity
        persist_id (str): Id of this entity on the persistence layer, if
            saved to one. Initially ``None``.
            Not initable.
            Note that this attribute is only immutable after it's been
            set once after initialization (e.g. after :meth:`create`).
    """

    model = attr.ib(validator=attr.validators.instance_of((Model,
                                                           LazyLoadableModel)))
    plugin = attr.ib(validator=attr.validators.instance_of(AbstractPlugin))
    persist_id = attr.ib(init=False, default=None)

    def __repr__(self):
        persist_str = ', {plugin}@{persist_id}'.format(
            plugin=self.plugin.type,
            persist_id=self.persist_id
        ) if self.persist_id is not None else ''

        try:
            data_str = dict(self.model.data)
        except ModelNotYetLoadedError:
            data_str = 'Not loaded'

        return '{name}{persist}: {data}'.format(name=self.__class__.__name__,
                                                persist=persist_str,
                                                data=data_str)

    @property
    def current_owner(self):
        """any: A user based on the model specified by the persistence
        layer if a current owner exists, otherwise None.
        In the case where the user model contains secret information,
        the returned user may omit this information.

        Raises:
            :exc:`~.EntityNotFoundError`: If the entity is persisted,
                but could not be found on the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """

        history = self.history
        return history[-1]['user'] if history else None

    @property
    def data(self):
        """dict: A copy of the basic data held by this entity model.
        Does not include any JSON-LD or IPLD specific information.

        If the entity was generated through :meth:`from_persist_id`, the
        first access of this property may also load the entity's data
        from the persistence layer (see :meth:`load` for potentially
        raised exceptions)
        """

        try:
            data = self.model.data
        except ModelNotYetLoadedError:
            self.load()
            data = self.model.data
        return dict(data)

    @property
    def history(self):
        """list of dict: A list containing the ownership history of this
        entity. Each item in the list is a dict containing a user based
        on the model specified by the persistence layer and a reference
        id for the event (e.g. transfer). The ownership events are
        sorted starting from the beginning of the entity's history
        (i.e. creation).
        In the case where the user model contains secret information,
        the returned user may omit this information.

        Raises:
            :exc:`~.EntityNotFoundError`: If the entity is persisted,
                but could not be found on the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """

        if self.persist_id is None:
            return []
        return self.plugin.get_history(self.persist_id)

    @property
    def status(self):
        """The current status of this entity in the backing persistence
        layer, as defined by :attr:`Entity.plugin`. Initially ``None``.

        Raises:
            :exc:`~.EntityNotFoundError`: If the entity is persisted,
                but could not be found on the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """

        if self.persist_id is None:
            return None
        return self.plugin.get_status(self.persist_id)

    @classmethod
    @abstractmethod
    def generate_model(cls, *, data, ld_type, ld_context, model_cls):
        """Generate a model instance for use with the current
        :attr:`cls`.

        **Must** be implemented by subclasses of :class:`~.Entity`.

        Args:
            data (dict, keyword): Model data
            ld_type (str, keyword): @type of the entity.
            ld_context (str or dict or [str|dict], keyword): "@context"
                for the entity as either a string URL or array of string
                URLs or dictionaries. See the `JSON-LD spec on contexts
                <https://www.w3.org/TR/json-ld/#the-context>`_ for more
                information.
            model_cls (class, keyword): Model class to use the
                generated model. See :mod:`.models`.

        Returns:
            A model instance

        Raises:
            :exc:`~.ModelDataError`: if :attr:`data` fails model
                validation
        """

    @classmethod
    def from_data(cls, data, *, data_format=DataFormat.jsonld, plugin):
        """Generic factory for instantiating :attr:`cls` entities
        from their model data. Entities instantiated from this factory
        have yet to be created on the backing persistence layer; see
        :meth:`create` on persisting an entity.

        Based on the :attr:`data_format`, the following are considered
        special keys in :attr:`data` and will have different behaviour
        depending on the ``data_type`` requested in later methods (e.g.
        :meth:`create`):

            - jsonld:
                - '@type' denotes the Linked Data type of the entity
                - '@context' denotes the JSON-LD context of the entity
                - '@id' denotes the JSON-LD identity of the entity
            - Otherwise:
                - 'type' denotes the Linked Data type of the entity

        Args:
            data (dict): Model data for the entity
            data_format (:class:`~.DataFormat` or str): Data format of
                :attr:`data`; must be a member of :class:`~.DataFormat`
                or a string equivalent.
                Defaults to jsonld.
            plugin (subclass of :class:`~.AbstractPlugin`, keyword):
                Persistence layer plugin used by generated :attr:`cls`

        Returns:
            :attr:`cls`: A generated :attr:`cls` entity from
            :attr:`data`

        Raises:
            :exc:`~.ModelDataError`: if :attr:`data` fails model
                validation
        """

        def bind_get_model_kwargs(data_format):
            def get_model_kwargs(data):
                result = _extract_ld_data(data, data_format)
                model_kwargs = {k: v for (k, v) in result._asdict().items()
                                if v is not None}
                return model_kwargs
            return get_model_kwargs

        def get_model_kwargs_from_ipld(data):
            raise NotImplementedError(('Creating entities from IPLD has not '
                                       'been implemented yet.'))

        get_model_kwargs = _data_format_resolver(data_format, {
            'jsonld': bind_get_model_kwargs('jsonld'),
            'json': bind_get_model_kwargs('json'),
            'ipld': get_model_kwargs_from_ipld,
        })
        model = cls.generate_model(**get_model_kwargs(data))

        return cls(model, plugin)

    @classmethod
    def from_persist_id(cls, persist_id, *, force_load=False, plugin):
        """Generic factory for creating :attr:`cls` entity instances
        from their persisted ids.

        **Note**: by default, instances generated from this factory
        lazily load their data upon first access (accessing
        :meth:`data`), which may throw under various conditions. In
        general, most usages of ``Entity`` and its subclasses do not
        require access to their data (including internal methods), and
        thus the data does not usually need to be loaded unless you
        expect to explicitly use :meth:`data` or one of the
        transformation methods, e.g. :meth:`to_json`. If you know you
        will be using the data and want to avoid raising unexpected
        exceptions upon access, make sure to set :attr:`force_load` or
        use :meth:`load` on the returned entity before accessing
        :meth:`data`.

        Args:
            persist_id (str): Id of the entity on the persistence
                layer (see :attr:`Entity.plugin`)
            force_load (bool, keyword, optional): Whether to load the
                entity's data immediately from the persistence layer
                after instantiation.
                Defaults to false.
            plugin (subclass of :class:`~.AbstractPlugin`, keyword):
                Persistence layer plugin used by generated :attr:`cls`

        Returns:
            :attr:`cls`: A generated entity based on :attr:`persist_id`

        Raises:
            If :attr:`force_load` is ``True``, see :meth:`load` for the
            list of possible exceptions.
        """

        model = cls.generate_model(model_cls=LazyLoadableModel)
        entity = cls(model, plugin=plugin)
        entity.persist_id = persist_id
        if force_load:
            entity.load()
        return entity

    def create(self, user, data_format=DataFormat.jsonld):
        """Create (i.e. persist) this entity to the backing persistence
        layer.

        Args:
            user (any): A user based on the model specified by the
                persistence layer
            data_format (:class:`~.DataFormat` or str): Data format used
                in persisting the entity; must be a member of
                :class:`~.DataFormat` or a string equivalent.
                Defaults to jsonld.

        Returns:
            str: Id of this entity on the persistence layer

        Raises:
            :exc:`~.EntityCreationError`: If an error occurred during
                the creation of this entity that caused it to
                **NOT** be persisted. Contains the original error from
                the persistence layer, if available.
            :exc:`~.EntityPreviouslyCreatedError`: If the entity has
                already been persisted. Contains the existing id of the
                entity on the persistence layer.
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """

        if self.persist_id is not None:
            raise EntityPreviouslyCreatedError(self.persist_id)

        entity_data = self._to_format(data_format)
        create_id = self.plugin.save(entity_data, user=user)
        self.persist_id = create_id
        return create_id

    def load(self):
        """Load this entity from the backing persistence layer, if
        possible.

        When used by itself, this method is most useful in ensuring that
        an entity generated from :meth:`from_persist_id` is actually
        available on the persistence layer to avoid errors later.

        Raises:
            :exc:`~.EntityNotYetPersistedError`: If the entity is not
                associated with an id on the persistence layer
                (:attr:`~Entity.persist_id`) yet
            :exc:`~.EntityNotFoundError`: If the entity has a
                :attr:`~Entity.persist_id` but could not be found on
                the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
            :exc:`~.ModelDataError`: If the loaded entity's data fails
                validation or its type or context differs from their
                expected values
        """

        if hasattr(self.model, 'load'):
            if self.persist_id is None:
                raise EntityNotYetPersistedError(('Entities cannot be loaded '
                                                  'until they have been '
                                                  'persisted'))

            self.model.load(self.persist_id, plugin=self.plugin)

    def to_json(self):
        """Output this entity as a JSON-serializable dict.

        The entity's @type is represented as 'type' and the @context is
        ignored.
        """

        json_model = self.data
        json_model['type'] = self.model.ld_type
        return json_model

    def to_jsonld(self):
        """Output this entity as a JSON-LD-serializable dict.

        Adds the @type, @context, and @id as-is. If no @id was given, an
        empty @id is used by default to refer to the current
        :attr:`~.Entity.persist_id` document.
        """

        ld_model = self.data
        ld_model['@context'] = _copy_context_into_mutable(self.model.ld_context)
        ld_model['@type'] = self.model.ld_type
        ld_model['@id'] = self.model.ld_id
        return ld_model

    def to_ipld(self):
        """Output this entity's data as an IPLD-serializable dict.

        The entity's @type is represented as 'type' and the @context is
        ignored.
        """

        raise NotImplementedError('to_ipld() has not been implemented yet')

    def _to_format(self, data_format):
        to_format = _data_format_resolver(data_format, {
            'jsonld': self.to_jsonld,
            'json': self.to_json,
            'ipld': self.to_ipld,
        })
        return to_format()


class TransferrableEntity(Entity):
    """Base class for transferable COALA IP entity models.

    Provides functionality for transferrable entities through
    :meth:`transfer`
    """

    def transfer(self, transfer_payload=None, *, from_user, to_user):
        """Transfer this entity to another owner on the backing
        persistence layer

        Args:
            transfer_payload (dict): Payload for the transfer
            from_user (any): A user based on the model specified by the
                persistence layer
            to_user (any): A user based on the model specified by the
                persistence layer

        Returns:
            str: Id of the resulting transfer action on the persistence
            layer

        Raises:
            :exc:`~.EntityNotYetPersistedError`: If the entity being
                transferred is not associated with an id on the
                persistence layer (:attr:`~Entity.persist_id`) yet
            :exc:`~.EntityNotFoundError`: If the entity could not be
                found on the persistence layer
            :exc:`~.EntityTransferError`: If the entity fails to be
                transferred on the persistence layer
            :exc:`~.PersistenceError`: If any other unhandled error
                in the plugin occurred
        """

        if self.persist_id is None:
            raise EntityNotYetPersistedError(('Entities cannot be transferred '
                                              'until they have been '
                                              'persisted'))

        return self.plugin.transfer(self.persist_id, transfer_payload,
                                    from_user=from_user, to_user=to_user)


class Work(Entity):
    """COALA IP's Work entity.

    A distinct, abstract Creation whose existence is revealed through
    one or more :class:`~.Manifestation` entities.

    :class:`~.Work` entities are always of @type 'AbstractWork'.
    """

    @classmethod
    def generate_model(cls, *args, **kwargs):
        """Generate a Work model.

        See :meth:`~.Entity.generate_model` for more details.

        Ignores the given ``ld_type`` as :class:`~.Work` entities
        always have @type 'AbstractWork'.
        """
        return work_model_factory(*args, **kwargs)


class Manifestation(Entity):
    """COALA IP's Manifestation entity.

    A perceivable manifestation of a :class:`~.Work`.

    :class:`~.Manifestation` entities are by default of @type
    'CreativeWork'.
    """

    @classmethod
    def generate_model(cls, *args, **kwargs):
        """Generate a Manifestation model.

        See :meth:`~.Entity.generate_model` for more details.
        """
        return manifestation_model_factory(*args, **kwargs)


class Right(TransferrableEntity):
    """COALA IP's Right entity. Transferrable.

    A statement of entitlement (i.e. "right") to do something in
    relation to a :class:`~.Work` or :class:`~.Manifestation`.

    More specific rights, such as ``PlaybackRights``, ``StreamRights``,
    etc should be implemented as subclasses of this class.

    By default, :class:`~.Rights` entities are of @type 'Right' and
    only include the COALA IP context, as Rights are not dependent on
    schema.org.
    """

    @classmethod
    def generate_model(cls, *args, **kwargs):
        """Generate a Work model.

        See :meth:`~.Entity.generate_model` for more details.
        """
        return right_model_factory(*args, **kwargs)

    def transfer(self, rights_assignment_data=None, *, from_user, to_user,
                 rights_assignment_format='jsonld'):
        """Transfer this Right to another owner on the backing
        persistence layer.

        Args:
            rights_assignment_data (dict): Model data for the resulting
                :class:`~.RightsAssignment`
            from_user (any, keyword): A user based on the model specified
                by the persistence layer
            to_user (any, keyword): A user based on the model specified
                by the persistence layer
            rights_assignment_format (str, keyword, optional): Data
                format of the created entity; must be one of:

                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
            :class:`~.RightsAssignment`: The RightsAssignment entity
            created from this transfer

        Raises:
            See :meth:`~.TransferrableEntity.transfer`
        """

        rights_assignment = RightsAssignment.from_data(
            rights_assignment_data or {},
            plugin=self.plugin)
        transfer_payload = rights_assignment._to_format(
            data_format=rights_assignment_format)
        transfer_id = super().transfer(transfer_payload, from_user=from_user,
                                       to_user=to_user)

        rights_assignment.persist_id = transfer_id
        return rights_assignment


class Copyright(Right):
    """COALA IP's Copyright entity. Transferrable.

    The full entitlement of Copyright to a :class:`~.Work` or
    :class:`~.Manifestation`.

    :class:`~.Copyright` entities are always of @type 'Copyright' and by
    default only include the COALA IP context, they are not dependent on
    schema.org.
    """

    @classmethod
    def generate_model(cls, *args, **kwargs):
        """Generate a Work model.

        See :meth:`~.Entity.generate_model` for more details.

        Ignores the given ``ld_type`` as :class:`~.Copyright` are
        always 'Copyright's.
        """
        return copyright_model_factory(*args, **kwargs)


class RightsAssignment(Entity):
    """COALA IP's RightsAssignment entity.

    The assignment (e.g. transfer) of a :class:`~.Right` to someone.

    :class:`.RightsAssignment` entities may only be persisted in the
    underlying persistence layer through transfer operations, and hence
    cannot be created normally through :meth:`.create`.

    :class:`~.RightsAssignment` entities are always of @type
    'RightsAssignment' and by default only include the COALA IP context,
    as Copyrights are not dependent on schema.org.
    """

    def create(self, *args, **kwargs):
        """Removes the ability to persist a :class:`~.RightsAssignment`
        normally. Raises :exc:`~.PersistenceError` if called.
        """
        raise PersistenceError(('RightsAssignments can only be created '
                                ' through transer transactions.'))

    @classmethod
    def generate_model(cls, *args, **kwargs):
        """Generate a Work model.

        See :meth:`~.Entity.generate_model` for more details.

        Ignores the given ``ld_type`` as :class:`~.RightsAssignment`
        entities always have @type 'RightsTransferAction's.
        """
        return rights_assignment_model_factory(*args, **kwargs)
