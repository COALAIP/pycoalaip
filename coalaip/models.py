"""Low level models mirroring COALA IP's entity model

Supports transformations of the entity into JSON, JSON-LD, and IPLD data
formats, as well as creation and transferring through persistence layer
plugin.
"""

from abc import ABC, abstractmethod
from copy import copy
from coalaip import context_urls
from coalaip.exceptions import (
    EntityError,
    EntityDataError,
    EntityNotYetPersistedError,
    EntityPreviouslyCreatedError,
)
from coalaip.plugin import AbstractPlugin
from coalaip.utils import data_format_resolver


DEFAULT_LD_CONTEXT = [context_urls.COALAIP, context_urls.SCHEMA]


class CoalaIpEntity(ABC):
    """Abstract base class of all COALA IP entity models.

    Provides base functionality for all COALA IP entities, including
    entity creation (:meth:`~CoalaIpEntity.create`) and, if necessary,
    retrival of their status (:meth:`~CoalaIpEntity.get_status`), on
    the backing persistence layer provided by the given ledger plugin.

    Subclasses \*must\* implement their own :meth:`from_data`
    classmethod.
    """

    def __init__(self, data, *, ld_type, ld_context=DEFAULT_LD_CONTEXT, plugin):
        """Initialize a :class:`~coalaip.models.CoalaIpEntity` instance.

        Args:
            data (dict): a dict holding the model data for the entity.
            ld_type (str, keyword): the "@type" of the entity. Will be
                inserted into the JSON-LD representation as-is, and as
                "type" in JSON and IPLD representations.
            ld_context (str|[str|dict], keyword, optional): the context
                for the entity as either a string URL or array of string
                URLs or dictionaries. See the `JSON-LD spec on contexts
                <https://www.w3.org/TR/json-ld/#the-context>`_ for more
                information. Only added as "@context" to JSON-LD
                representation.
                Defaults to adding COALA IP and schema.org to the
                context.
            plugin (Plugin, keyword): the persistence layer plugin

        Raises:
            :class:`TypeError`: if the given 'plugin' does not subclass
                :class:`~coalaip.plugin.AbstractPlugin`
        """

        if not isinstance(plugin, AbstractPlugin):
            raise TypeError(('A plugin subclassing '
                             "'coalaip.plugin.AbstractPlugin' must be "
                             'provided when instantiating a CoalaIp entity '
                             'instance. Given a plugin of type '
                             "'{}' instead.".format(type(plugin))))

        self._data = data
        self._ld_type = ld_type
        self._ld_context = ld_context
        self._persist_id = None
        self._plugin = plugin

    def __repr__(self):
        persist_str = ', {plugin}@{persist_id}'.format(
            plugin=self.plugin_type,
            persist_id=self.persist_id
        ) if self.persist_id is not None else ''

        return '{name}{persist}: {data}'.format(name=self.__class__.__name__,
                                                persist=persist_str,
                                                data=self.data)

    @classmethod
    @abstractmethod
    def from_data(cls, data, *, data_format='jsonld', plugin):
        """Generic factory for instantiating :attr:`cls` entities
        from their model data. Entities instantiated from this factory
        have yet to be created on the backing persistence layer; see
        :meth:`create` on persisting an entity.

        Based on the :attr:`data_format`, the following are considered
        special keys in :attr:`data` and will have different behaviour
        depending on the ``data_type`` requested in later methods (e.g.
        :meth:`~coalaip.models.CoalaIpEntity.create`):
            - :attr:`data_format` == 'jsonld':
                - '@type' denotes the Linked Data type of the entity
                - '@context' denotes the JSON-LD context of the entity
            - Otherwise:
                - 'type' denotes the Linked Data type of the entity
                - 'context' denotes the JSON-LD context of the entity

        Args:
            data (dict): a dict holding the model data for the entity.
            data_format (str): the data format of :attr:`data`; must be
                one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'
            plugin (Plugin, keyword): the persistence layer plugin

        Returns:
            :attr:`cls`: an instance of :attr:`cls` holding the
            :attr:`data`
        """

        cls_from_format = data_format_resolver(data_format, {
            'jsonld': cls._from_jsonld,
            'json': cls._from_json,
            'ipld': cls._from_ipld,
        })

        return cls_from_format(copy(data), plugin=plugin)

    @classmethod
    def from_persist_id(cls, persist_id, *, force_load=False, plugin):
        """Generic factory for creating :attr:`cls` entity instances
        from their persisted ids.

        \*Note\*: by default, instances generated from this factory
        lazily load their data upon first access (see :meth:`data`),
        which may throw under various conditions. In general, most
        usages of the entities do not require access to their data
        (including internal methods), and thus the data does not usually
        need to be loaded unless :meth:`data` or one of the
        transformation methods, e.g. :meth:`to_json`, are explicitly
        used. If you know you will be using the data and want to avoid
        raising unexpected exceptions upon access, make sure to set
        :attr:`force_load` or use :meth:`load` on the returned entity
        beforehand.

        Args:
            persist_id (str): the id of the entity on the persistence
                layer (see :attr:`plugin`)
            force_load (bool, keyword, optional): whether to load the
                entity's data immediately from the persistence layer
                after instantiation.
                Defaults to false.
            plugin (Plugin, keyword): the persistence layer plugin

        Returns:
            :attr:`cls`: a generated entity based on :attr:`persist_id`

        Raises:
            if :attr:`force_load` is True, see :meth:`load`'s
            potentially raised exceptions
        """

        entity = cls(None, plugin=plugin)
        entity._persist_id = persist_id
        if force_load:
            entity.load()
        return entity

    @property
    def data(self):
        """dict: the basic data held by this entity model. Does not
        include any JSON-LD or IPLD specific information.

        If the entity was generated through :meth:`from_persist_id`, the
        first access of this property will also load the entity's data
        from the persistence layer (see :meth:`load` for potentially
        raised exceptions)
        """

        if self.persist_id is not None and self._data is None:
            self.load()

        return self._data

    @property
    def persist_id(self):
        """str: the id of this entity on the persistence layer,
        if saved to one. Otherwise, None.
        """
        return self._persist_id

    @property
    def plugin_type(self):
        """str: the type of the plugin used by this entity"""
        return self._plugin.type

    def create(self, user, data_format='jsonld'):
        """Create (i.e. persist) this entity to the backing persistence
        layer.

        Args:
            user (any): a user based on the model specified by the
                persistence layer
            data_format (str): the data format of the created entity;
                must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
            str: the id of this entity on the persistence layer

        Raises:
            :class:`~coalaip.exceptions.EntityCreationError`: if an
                error occurred during the creation of this entity that
                caused it to \*NOT\* be persisted. Contains the original
                error from the persistence layer, if available.
            :class:`~coalaip.exceptions.EntityPreviouslyCreatedError`:
                if the entity has already been persisted. Should contain
                the existing id of the entity on the persistence layer.
        """

        if self.persist_id is not None:
            raise EntityPreviouslyCreatedError(self._persist_id)

        entity_data = self._to_format(data_format)
        create_id = self._plugin.save(entity_data, user=user)
        self._persist_id = create_id
        return create_id

    def get_status(self):
        """Get the current status of this entity, including it's state
        in the backing persistence layer.

        Returns:
            the status of the entity, as defined by the persistence
            layer, or None if the entity is not yet persisted.

        Raises:
            :class:`~coalaip.exceptions.EntityNotFoundError`: if the
                entity is persisted, but could not be found on the
                persistence layer
        """

        if self.persist_id is None:
            return None
        return self._plugin.get_status(self.persist_id)

    def load(self):
        """Load this entity from the backing persistence layer.

        When used by itself, this method is most useful in ensuring that
        an entity generated from :meth:`from_persist_id` is actually
        available on the persistence layer to avoid errors later.

        Raises:
            :class:`~coalaip.exceptions.EntityNotYetPersistedError`: if
                the entity has not been persisted yet
            :class:`~coalaip.exceptions.EntityNotFoundError`: if the
                entity is persisted, but could not be found on the
                persistence layer
            :class:`~coalaip.exceptions.EntityDataError`: if the loaded
                entity's type or context differ from their initialized
                values
        """

        if self.persist_id is None:
            raise EntityNotYetPersistedError(('Entities cannot be loaded '
                                              'until they have been persisted'))

        persist_data = self._plugin.load(self.persist_id)
        model_data = copy(persist_data)

        # Check the type, context, and id, if available, and remove them from
        # the data before saving
        for type_key in ['@type', 'type']:
            if type_key in persist_data:
                loaded_type = persist_data[type_key]

                if loaded_type and loaded_type != self._ld_type:
                    raise EntityDataError(
                        ('Loaded entity type ({loaded_type}) of entity '
                         'differs from existing entity type '
                         '({self_type})').format(loaded_type=loaded_type,
                                                 self_type=self._ld_type)
                    )

                del model_data[type_key]

        if '@context' in persist_data:
            loaded_ctx = persist_data['@context']

            if loaded_ctx and loaded_ctx != self._ld_context:
                raise EntityDataError(
                    ('Loaded context ({loaded_ctx}) of entity differs from '
                     'existing context ({self_ctx})').format(
                         loaded_ctx=loaded_ctx, self_ctx=self._ld_context)
                )

            del model_data['@context']

        if '@id' in persist_data:
            del model_data['@id']

        self._data = model_data

    def to_json(self):
        """Output this entity as a JSON-serializable dict.

        Returns:
            dict: a JSON-serializable dict representing this entity's
            data
        """

        json_model = copy(self.data)
        json_model['type'] = self._ld_type
        return json_model

    def to_jsonld(self):
        """Output this entity as a JSON-LD-serializable dict.

        Returns:
            dict: a JSON-LD-serializable dict representing this entity's
            data
        """

        ld_model = copy(self.data)
        ld_model['@context'] = self._ld_context
        ld_model['@type'] = self._ld_type
        ld_model['@id'] = ''  # Specifying an empty @id resolves to the current document
        return ld_model

    def to_ipld(self):
        """Output this entity's data as an IPLD string."""

        raise NotImplementedError('to_ipld() has not been implemented yet')

    @classmethod
    def _from_jsonld(cls, data, *, plugin):
        init_kwargs = {}
        if '@type' in data:
            init_kwargs['ld_type'] = data['@type']
            del data['@type']
        if '@context' in data:
            init_kwargs['ld_context'] = data['@context']
            del data['@context']
        return cls(data, plugin=plugin, **init_kwargs)

    @classmethod
    def _from_json(cls, data, *, plugin):
        init_kwargs = {}
        if 'type' in data:
            init_kwargs['ld_type'] = data['type']
            del data['type']
        if 'context' in data:
            init_kwargs['ld_context'] = data['context']
            del data['context']
        return cls(data, plugin=plugin, **init_kwargs)

    @classmethod
    def _from_ipld(cls, data, *, plugin):
        raise NotImplementedError(('Creating entities from IPLD has not been '
                                   'implemented yet.'))

    def _to_format(self, data_format):
        to_format = data_format_resolver(data_format, {
            'jsonld': self.to_jsonld,
            'json': self.to_json,
            'ipld': self.to_ipld,
        })
        return to_format()


class CoalaIpTransferrableEntity(CoalaIpEntity):
    """Base class for transferable COALA IP entity models.

    Provides functionality for transferrable entities through
    (:meth:`~CoalaIpTransferrableEntity.transfer`)
    """

    def transfer(self, transfer_payload=None, *, from_user, to_user):
        """Transfer this entity to another owner on the backing
        persistence layer

        Args:
            transfer_payload (dict): a dict holding the transfer's payload
            from_user (any): a user based on the model specified by the
                persistence layer
            to_user (any): a user based on the model specified by the
                persistence layer

        Returns:

        Raises:
            :class:`~coalaip.exceptions.EntityNotYetPersistedError`:
                if the entity being transferred has not yet been
                persisted to the backing persistence layer
        """

        if self.persist_id is None:
            raise EntityNotYetPersistedError(('Entities cannot be transferred '
                                              'until they have been persisted'))

        return self._plugin.transfer(self.persist_id, transfer_payload,
                                     from_user=from_user, to_user=to_user)


class Creation(CoalaIpEntity):
    """COALA IP's Creation entity.

    Base class for :class:`coalaip.models.Work`s and
    :class:`coalaip.models.Manifestation`s.

    :class:`~coalaip.models.Creations`s are by default of ``@type``
    'CreativeWork'.
    """

    def __init__(self, data, *args, ld_type='CreativeWork', **kwargs):
        super().__init__(data, ld_type=ld_type, *args, **kwargs)

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.Creation` (or subclass)
        entity from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the
                Creation. Must include at least a ``name`` key.

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if
                :attr:`data` does not pass validation
        """

        creation_name = data.get('name')
        if not isinstance(creation_name, str):
            raise EntityDataError(("'name' must be given as a string in the "
                                   "'data' of a Creation. Given "
                                   "'{}'".format(creation_name)))
        return super().from_data(data, *args, **kwargs)


class Work(Creation):
    """COALA IP's Work entity.

    A distinct, abstract Creation whose existence is revealed through
    one or more :class:`~coalaip.models.Manifestation`s.

    :class:`~coalaip.models.Work`s are always of ``@type``
    'CreativeWork'
    """

    def __init__(self, *args, **kwargs):
        super().__init__(ld_type='CreativeWork', *args, **kwargs)

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.Work` (or subclass) entity
        from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the Work.
                Must not include keys that indicate the model is a
                :class:`~coalaip.models.Manifestation` (e.g.
                ``manifestationOfWork`` or ``isManifestation == True``).
                Ignores any given ``type`` or ``@type`` values.

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if
                :attr:`data` does not pass validation
        """

        if 'manifestationOfWork' in data:
            raise EntityDataError(("'manifestationOfWork' must not be given "
                                   "in the 'data' of Works"))
        if data.get('isManifestation', False):
            raise EntityDataError(("'isManifestation' must not be True if "
                                   "given in the 'data' of Works"))

        return super().from_data(data, *args, **kwargs)


class Manifestation(Creation):
    """COALA IP's Manifestation entity.

    A perceivable manifestation of a :class:`~coalaip.models.Work`.

    :class:`~coalaip.models.Manifestation`s are by default of
    ``@type`` 'CreativeWork'.
    """

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.Manifestation` (or
        subclass) entity from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the
                Manifestation. Must include a ``manifestationOfWork``
                key.
                See :class:`~pycoalaip.models.Creation` for other model
                requirements.

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if
                :attr:`data` does not pass validation
        """
        manifestation_of = data.get('manifestationOfWork')
        if not isinstance(manifestation_of, str):
            raise EntityDataError(("'manifestationOfWork' must be given as a "
                                   "string in the 'data' of a Manifestation. "
                                   "Given '{}'".format(manifestation_of)))


        data['isManifestation'] = True
        return super().from_data(data, *args, **kwargs)


class Right(CoalaIpTransferrableEntity):
    """COALA IP's Right entity. Transferrable.

    A statement of entitlement (i.e. "right") to do something in
    relation to a :class:`~coalaip.models.Work` or
    :class:`~coalaip.models.Manifestation`.

    More specific rights, such as PlaybackRights, StreamRights, etc
    should be implemented as subclasses of this class.

    By default, :class:`~coalaip.models.Rights`s are of ``@type``
    'Right' and only include the COALA IP context, as Rights are not
    dependent on schema.org.
    """

    def __init__(self, *args, ld_type='Right', ld_context=context_urls.COALAIP,
                 **kwargs):
        super().__init__(ld_type='CreativeWork', ld_context=ld_context,
                         *args, **kwargs)

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.Right` (or subclass) entity
        from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the Right.
                Must include either a ``rightsOf`` or ``allowedBy`` key
                (but not both): ``rightsOf`` indicates that the Right
                contains full rights to an existing Manifestation or
                Work while ``allowedBy`` indicates that the Right is
                derived from and allowed by a source Right.

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if
                :attr:`data` does not pass validation
        """

        rights_of = data.get('rightsOf')
        allowed_by = data.get('allowedBy')
        if rights_of is not None and not isinstance(rights_of, str):
            raise EntityDataError(("'rightsOf' must be given as a string in "
                                   "the 'data' of a Right. Given "
                                   "'{}'".format(rights_of)))
        if allowed_by is not None and not isinstance(allowed_by, str):
            raise EntityDataError(("'allowedBy' must be given as a string in "
                                   "the 'data' of a Right. Given "
                                   "'{}'".format(rights_of)))
        if not (bool(rights_of) ^ bool(allowed_by)):
            raise EntityDataError(("One and only one of 'rightsOf' or "
                                   "'allowedBy' can be given in the 'data' of "
                                   'a Right.'))

        return super().from_data(data, *args, **kwargs)

    def transfer(self, rights_assignment_data=None, *, from_user, to_user,
                 rights_assignment_format='jsonld'):
        """Transfer this Right to another owner on the backing
        persistence layer.

        Args:
            rights_assignment_data (dict): a dict holding the model data
                for the RightsAssignment
            from_user (any, keyword): a user based on the model specified
                by the persistence layer
            to_user (any, keyword): a user based on the model specified
                by the persistence layer
            rights_assignment_format (str, keyword, optional): the data
                format of the created entity; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        transfer_payload = None
        if rights_assignment_data is not None:
            rights_assignment = RightsAssignment(rights_assignment_data,
                                                 plugin=self._plugin)
            transfer_payload = rights_assignment._to_format(
                rights_assignment_format)

        return super().transfer(transfer_payload, from_user=from_user,
                                to_user=to_user)


class Copyright(Right):
    """COALA IP's Copyright entity. Transferrable.

    The full entitlement of Copyright to a :class:`~coalaip.models.Work`
    or :class:`~coalaip.models.Manifestation`.

    :class:`~coalaip.models.Copyright`s are always of ``@type``
    'Copyright' and by default only include the COALA IP context, as
    Copyrights are not dependent on schema.org.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(ld_type='Copyright', *args, **kwargs)

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.Copyright` (or subclass)
        entity from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the
                Copyright. Must include at least a ``rightsOf`` key.
                See :class:`~pycoalaip.models.Right` for other model
                requirements.
                Ignores any given ``type`` or ``@type`` values.

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if
                :attr:`data` does not pass validation
        """

        if 'allowedBy' in data:
            raise EntityDataError(("'allowedBy' must not be given in the "
                                   "'data' of Copyrights"))

        return super().from_data(data, *args, **kwargs)


class RightsAssignment(CoalaIpEntity):
    """COALA IP's RightsAssignment entity.

    The assignment (e.g. transfer) of a :class:`~coalaip.models.Right`
    to someone.

    RightsAssignments may only be persisted in the underlying
    persistence layer through transfer operations, and hence cannot be
    created normally through ``.create()``.

    :class:`~coalaip.models.RightsAssignment`s are always of ``@type``
    'RightsAssignment' and by default only include the COALA IP
    context, as Copyrights are not dependent on schema.org.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(ld_type='RightsTransferAction', *args, **kwargs)

    @classmethod
    def from_data(cls, data, *args, **kwargs):
        """Generate a :class:`~coalaip.models.RightsAssignment` (or subclass)
        entity from its model data, with schema validation.

        See :meth:`~coalaip.models.CoalaIpEntity.from_data` for additional
        parameters.

        Args:
            data (dict): a dict holding the model data for the
                RightsAssignment.
                Ignores any given ``type`` or ``@type`` values.
        """

        return super().from_data(data, *args, **kwargs)

    def create(self, *args, **kwargs):
        """Removes the ability to persist RightsAssignments normally.
        Raises :class:`~coalaip.exceptions.EntityError` if called.
        """
        raise EntityError(('RightsAssignments can only created through '
                           'transer transactions.'))
