"""Low level models mirroring COALA IP's entity model

Supports transformations of the entity into JSON, JSON-LD, and IPLD data
formats, as well as creation and transferring through persistence layer
plugin.
"""

from copy import copy
from coalaip import context_urls
from coalaip.exceptions import (
    EntityError,
    EntityDataError,
    EntityNotYetPersistedError,
    EntityPreviouslyCreatedError,
)
from coalaip.plugin import AbstractPlugin


DEFAULT_LD_CONTEXT = [context_urls.COALAIP, context_urls.SCHEMA]


class CoalaIpEntity:
    """Base class of all COALA IP entity models.

    Provides base functionality for all COALA IP entities, including
    entity creation (:meth:`~CoalaIpEntity.create`) and, if necessary,
    retrival of their status (:meth:`~CoalaIpEntity.get_status`), on
    the backing persistence layer provided by the given ledger plugin.
    """

    def __init__(self, data, *, entity_type, ctx=DEFAULT_LD_CONTEXT, plugin):
        """Initialize a :class:`~coalaip.models.CoalaIpEntity` instance.

        Args:
            data (dict): a dict holding the model data for the entity
            entity_type (str, keyword): the "@type" of the entity. Will
                be inserted into the JSON-LD and IPLD representations
                as-is, and as "type" in JSON representations.
            ctx (str|[str]|[dict], keyword, optional): the context for
                the entity as either a string URL or array of string
                URLs or dictionaries. See the `JSON-LD spec on contexts
                <https://www.w3.org/TR/json-ld/#the-context>`_ for more
                information.
                Defaults to adding COALA IP and schema.org to the
                context.
            plugin (Plugin, keyword): the persistence layer plugin

        Raises:
            :class:`TypeError`: if the given 'plugin' does not subclass
                :class:`~coalaip.plugin.AbstractPlugin`
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' is not a dict or the given 'entity_type' is not
                a string.
        """

        if not isinstance(plugin, AbstractPlugin):
            raise TypeError(('A plugin subclassing '
                             "'coalaip.plugin.AbstractPlugin' must be "
                             'provided when instantiating a CoalaIp entity '
                             'instance. Given a plugin of type '
                             "'{}' instead.".format(type(plugin))))

        if not isinstance(entity_type, str):
            raise EntityDataError(("'entity_type' must be provided as a "
                                   'string to CoalaIpEntities. '
                                   "Given '{}'".format(entity_type)))

        if not isinstance(data, dict):
            raise EntityDataError(("'data' must be provided as a dict"
                                   'to CoalaIpEntities. Given '
                                   "'{}'".format(data)))

        self._data = data
        self._entity_type = entity_type
        self._ld_context = ctx
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
    def from_persist_id(cls, persist_id, *, force_load=False, plugin):
        """Generic factory for creating :attr:`cls` entity instances
        from their persisted ids.

        \*Note\*: by default, instances generated from this factory
        lazily load their data upon first access (see :meth:`data`),
        which may throw under various conditions. In general, most
        usages of the models do not require access to their data
        (including internal methods), and thus the data does not usually
        need to be loaded unless :meth:`data` or one of the
        transformation methods, e.g. :meth:`to_json`, are explicitly
        used. If you know you will be using the data and want to avoid
        raising unexpected exceptions upon access, make sure to set
        :attr:`force_load` or use :meth:`load` on the returned model
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
            :attr:`cls`: a generated model based on :attr:`persist_id`

        Raises:
            if :attr:`force_load` is True, see :meth:`load`'s
            potentially raised exceptions
        """

        entity = cls({}, plugin=plugin)  # Trick validation with empty dict
        entity._data = None
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
        """str|None: the id of this entity on the persistence layer,
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

                if loaded_type and loaded_type != self._entity_type:
                    raise EntityDataError(
                        ('Loaded entity type ({loaded_type}) of entity '
                         'differs from existing entity type '
                         '({self_type})').format(loaded_type=loaded_type,
                                                 self_type=self._entity_type)
                    )

                del model_data[type_key]

        if '@context' in persist_data:
            loaded_ctx = persist_data['@context']

            if loaded_ctx and loaded_ctx != self._ctx:
                raise EntityDataError(
                    ('Loaded context ({loaded_ctx}) of entity differs from '
                     'existing context ({self_ctx})').format(
                         loaded_ctx=loaded_ctx, self_ctx=self._ctx)
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
        json_model['type'] = self._entity_type
        return json_model

    def to_jsonld(self):
        """Output this entity as a JSON-LD-serializable dict.

        Returns:
            dict: a JSON-LD-serializable dict representing this entity's
            data
        """

        ld_model = copy(self.data)
        ld_model['@context'] = self._ld_context
        ld_model['@type'] = self._entity_type
        ld_model['@id'] = ''  # Specifying an empty @id resolves to the current document
        return ld_model

    def to_ipld(self):
        """Output this entity's data as an IPLD string."""

        raise NotImplementedError('to_ipld() has not been implemented yet')

    def _to_format(self, data_format):
        if data_format == 'jsonld':
            return self.to_jsonld()
        elif data_format == 'json':
            return self.to_json()
        elif data_format == 'ipld':
            raise NotImplementedError(('Saving entities as IPLD has not been '
                                       'implemented yet.'))
        else:
            raise ValueError(("'data_format' argument should be one of "
                              "'json', 'jsonld', or 'ipld'. "
                              "Given '{}'.").format(data_format))


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
    """

    def __init__(self, data, *args, **kwargs):
        """Initialize a :class:`~coalaip.models.Creation` instance

        Args:
            data (dict): a dict holding the model data for the
                Creation. Must include at least a ``name`` key.
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' dict does not contain a string value for ``name``
        """

        creation_name = data.get('name')

        if not isinstance(creation_name, str):
            raise EntityDataError(("'name' must be given as a string in the "
                                   "'data' of a Creation. Given "
                                   "'{}'".format(creation_name)))

        super().__init__(data, *args, **kwargs)


class Work(Creation):
    """COALA IP's Work entity.

    A distinct, abstract Creation whose existence is revealed through
    one or more :class:`~coalaip.models.Manifestation`s.
    """

    def __init__(self, data, *args, **kwargs):
        """Initialize a :class:`~coalaip.models.Work` instance.

        :class:`~coalaip.models.Work`s are always of ``entity_type``
        'CreativeWork'.

        See also :class:`~coalaip.models.Creation`.

        Args:
            data (dict): a dict holding the model data for the Work.
                Must not include keys that indicate the model is a
                :class:`~coalaip.models.Manifestation` (e.g.
                ``manifestationOfWork`` or ``isManifestation == True``).
                See :class:`~pycoalaip.models.Creation` for other model
                requirements.
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' dict contains ``manifestationOfWork`` or a True
                value for ``isManifestation``.
        """

        if 'manifestationOfWork' in data:
            raise EntityDataError(("'manifestationOfWork' must not be given "
                                   "in the 'data' of Works"))
        if data.get('isManifestation', False):
            raise EntityDataError(("'isManifestation' must not be True if "
                                   "given in the 'data' of Works"))

        super().__init__(data, entity_type='CreativeWork', *args, **kwargs)


class Manifestation(Creation):
    """COALA IP's Manifestation entity.

    A perceivable manifestation of a :class:`~coalaip.models.Work`.
    """

    def __init__(self, data, *args, entity_type='CreativeWork', **kwargs):
        """Initialize a :class:`~coalaip.models.Manifestation` instance

        See also :class:`~coalaip.models.Creation`.

        Args:
            data (dict): a dict holding the model data for the
                Manifestation. Must include a ``manifestationOfWork``
                key.
                If an ``type`` or ``@type`` key is provided in the
                'data', this type will be used as the ``entity_type``
                rather than the 'entity_type' keyword argument.
                See :class:`~pycoalaip.models.Creation` for other model
                requirements.
            entity_type (str, keyword, optional): the "@type" of the
                Manifestation.
                Defaults to 'CreativeWork'.
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' dict does not contain a string value for
                ``manifestationOfWork``
        """

        manifestation_of = data.get('manifestationOfWork')

        if not isinstance(manifestation_of, str):
            raise EntityDataError(("'manifestationOfWork' must be given as a "
                                   "string in the 'data' of a Manifestation. "
                                   "Given '{}'".format(manifestation_of)))

        # If the entity type is already specified as part of the data, use that
        # instead of 'CreativeWork'
        for type_key in ['type', '@type']:
            if type_key in data:
                entity_type = data[type_key]
                del data[type_key]
                break

        data['isManifestation'] = True
        super().__init__(data, entity_type=entity_type, *args, **kwargs)


class Right(CoalaIpTransferrableEntity):
    """COALA IP's Right entity. Transferrable.

    A statement of entitlement (i.e. "right") to do something in
    relation to a :class:`~coalaip.models.Work` or
    :class:`~coalaip.models.Manifestation`.

    More specific rights, such as PlaybackRights, StreamRights, etc
    should be implemented as subclasses of this class.
    """

    def __init__(self, data, *args, entity_type='Right',
                 ctx=context_urls.COALAIP, **kwargs):
        """Initialize a :class:`~coalaip.models.Right` instance

        Args:
            data (dict): a dict holding the model data for the Right.
                Must include either a ``rightsOf`` or ``allowedBy`` key:
                ``rightsOf`` indicates that the Right contains full
                rights to an existing Manifestation or Work while
                ``allowedBy`` indicates that the Right is derived from
                and allowed by a source Right (note that the two
                \*must not\* be provided together).
            entity_type (str, keyword, optional): the "@type" of the
                Manifestation.
                Defaults to 'Right'.
            ctx (str|str[]|dict[], keyword, optional): the context for
                the Right.
                Defaults to only only COALA IP, as Rights are not
                dependent on schema.org.
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' dict does not contain exactly one of ``rightsOf``
                or ``allowedBy`` as a string value.
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

        super().__init__(data, entity_type=entity_type, ctx=ctx, *args,
                         **kwargs)

    def transfer(self, rights_assignment_data=None, *, from_user, to_user,
                 rights_assignment_format='jsonld'):
        """Transfer this Right to another owner on the backing
        persistence layer.

        Args:
            rights_assignment_data (dict): a dict holding the model data for
                the RightsAssignment
            from_user (any): a user based on the model specified by the
                persistence layer
            to_user (any): a user based on the model specified by the
                persistence layer
            rights_assignment_format (str): the data format of the
                created entity; must be one of:
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
    """

    def __init__(self, data, *args, **kwargs):
        """Initialize a :class:`~coalaip.models.Copyright` instance

        :class:`~coalaip.models.Copyright`s are always of
        ``entity_type`` 'Copyright'.

        Args:
            data (dict): a dict holding the model data for the
                Copyright. Must include at least a ``rightsOf`` key.
                See :class:`~pycoalaip.models.Right` for other model
                requirements.
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`

        Raises:
            :class:`~coalaip.exceptions.EntityDataError`: if the given
                'data' does not contain a string value for ``rightsOf``
        """

        if 'allowedBy' in data:
            raise EntityDataError(("'allowedBy' must not be given in the "
                                   "'data' of Copyrights"))

        super().__init__(data, entity_type='Copyright', *args, **kwargs)


class RightsAssignment(CoalaIpEntity):
    """COALA IP's RightsAssignment entity.

    The assignment (e.g. transfer) of a :class:`~coalaip.models.Right`
    to someone.

    RightsAssignments may only be persisted in the underlying
    persistence layer through transfer operations, and hence cannot be
    created normally through ``.create()``.
    """

    def __init__(self, data, *args, **kwargs):
        """Initialize a :class:`~coalaip.models.RightsAssignment`
        instance

        Args:
            data (dict): a dict holding the model data for the
                RightsAssignment
            *args: see :class:`~coalaip.models.CoalaIpEntity`
            **kwargs: see :class:`~coalaip.models.CoalaIpEntity`
        """

        super().__init__(data, entity_type='RightsTransferAction', *args,
                         **kwargs)

    def create(self, *args, **kwargs):
        """Removes the ability to persist RightsAssignments normally.
        Raises :class:`~coalaip.exceptions.EntityError` if called.
        """
        raise EntityError(('RightsAssignments can only created through '
                           'transer transactions.'))
