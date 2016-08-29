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
    EntityNotYetPersistedError
)


DEFAULT_LD_CONTEXT = [context_urls.COALAIP, context_urls.SCHEMA]


class CoalaIpEntity:
    """Base class of all COALA IP entity models.

    Provides base functionality for all COALA IP entities, including
    entity creation (:method:`~CoalaIpEntity.create`) and, if necessary,
    retrival of their status (:method:`~CoalaIpEntity.get_status`), on
    the backing persistence layer provided by the given ledger plugin.
    """

    def __init__(self, data, *, ctx=DEFAULT_LD_CONTEXT, entity_type, plugin):
        """Initialize a :class:`~coalaip.models.CoalaIpEntity` instance.

        INSTANTIATION NOTES
        """

        # FIXME: check that plugin is instance of AbstractPlugin

        if not isinstance(entity_type, str):
            raise EntityDataError(('The entity type must be provided as a '
                                   'string to the entity. '
                                   'Got {} instead.').format(entity_type))

        # FIXME: should I check that data is a dict?

        self._data = data
        self._entity_type = entity_type
        self._ld_context = ctx
        self._persist_id = None
        self._plugin = plugin

    def __repr__(self):
        return "{name}: {data}".format(name=self.__class__.__name__,
                                       data=self._data)

    @property
    def persist_id(self):
        """(str|None): the id of this entity on the persistent backing
        layer, if saved to one. Otherwise, None.
        """
        return self._persist_id

    @property
    def plugin_type(self):
        """(str): the type of the plugin used by this entity"""
        return self._plugin.type

    def create(self, user, data_format='jsonld'):
        """Create (i.e. persist) this entity to the backing persistence
        layer

        Args:
            user (any): a user based on the model specified by the
                persistence layer
            data_format (str): the data format of the created entity;
                must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        entity_data = self._to_format(data_format)
        # FIXME: catch errors
        self._persist_id = self._plugin.save(entity_data, user=user)
        return self._persist_id

    def get_status(self):
        """Get the current status of this entity, including it's state
        in the backing persistence layer

        Returns:
            the status of the entity, as defined by the persistence layer
        """

        return self._plugin.get_status(self._persist_id)

    def to_json(self):
        """Output this entity as a JSON-serializable dict.

        Returns:
            dict: a JSON-serializable dict representing this entity's
                data
        """

        json_model = copy(self._data)
        json_model['type'] = self._entity_type
        return json_model

    def to_jsonld(self):
        """Output this entity as a JSON-LD-serializable dict.

        Returns:
            dict: a JSON-LD-serializable dict representing this entity's
                data
        """

        ld_model = copy(self._data)
        ld_model['@context'] = self._ld_context
        ld_model['@type'] = self._entity_type
        ld_model['@id'] = ''  # Specifying an empty @id resolves to the current document
        return ld_model

    def to_ipld(self):
        """Output this entity's data as an IPLD string"""

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
    (:method:`~CoalaIpTransferrableEntity.transfer`)
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
        """

        if self._persist_id is None:
            raise EntityNotYetPersistedError(('Entities cannot be transferred '
                                              'until they have been persisted'))
        else:
            return self._plugin.transfer(self._persist_id, transfer_payload,
                                         from_user=from_user, to_user=to_user)


class Creation(CoalaIpEntity):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='CreativeWork', plugin, **kwargs):
        """Initialize a :class:`~coalaip.models.Creation` instance

        INSTANTIATION NOTES
        """

        creation_name = data.get('name')

        if not isinstance(creation_name, str):
            # Proper error type... is ValueError right? Or KeyError? Or both?
            raise EntityDataError(("'name' must be given as a string in the "
                                   "'data' of Creations (Works and Manifestations). "
                                   "Given '{}' instead.".format(creation_name)))

        super().__init__(data, entity_type=entity_type, plugin=plugin, **kwargs)


class Work(Creation):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, plugin, **kwargs):
        """Initialize a :class:`~coalaip.models.Work` instance

        INSTANTIATION NOTES
        """

        if 'manifestationOfWork' in data:
            raise EntityDataError(("'manifestationOfWork' must not be given "
                                   "in the 'data' of Works"))
        if data.get('isManifestation', False):
            raise EntityDataError(("'isManifestation' must not be True if "
                                   "given in the 'data' of Works"))

        super().__init__(data, plugin=plugin, **kwargs)


class Manifestation(Creation):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='CreativeWork', plugin, **kwargs):
        """Initialize a :class:`~coalaip.models.Manifestation` instance

        INSTANTIATION NOTES
        """

        manifestation_of = data.get('manifestationOfWork')

        if not isinstance(manifestation_of, str):
            raise EntityDataError(("'manifestationOfWork' must be given as a "
                                   "string in the 'data' of Copyrights. "
                                   "Given '{}' instead.".format(manifestation_of)))

        # If the entity type is already specified as part of the data, use that
        # instead of 'CreativeWork'
        for type_key in ['type', '@type']:
            if type_key in data:
                entity_type = data[type_key]
                del data[type_key]
                break

        # FIXME: apply defaults
        data['isManifestation'] = True
        super().__init__(data, entity_type=entity_type, plugin=plugin, **kwargs)


class Right(CoalaIpTransferrableEntity):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='Right', ctx=context_urls.COALAIP,
                 plugin, **kwargs):
        """Initialize a :class:`~coalaip.models.Right` instance

        INSTANTIATION NOTES
        """

        # FIXME: apply defaults
        super().__init__(data, ctx=ctx, entity_type=entity_type, plugin=plugin,
                         **kwargs)

    def transfer(self, rights_assignment_data=None, *, from_user, to_user,
                 rights_assignment_format='jsonld'):
        """Transfer this Right to another owner on the backing
        persistence layer

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

        super().transfer(self._persist_id, transfer_payload,
                         from_user=from_user, to_user=to_user)


class Copyright(Right):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='Copyright', plugin, **kwargs):
        """Initialize a :class:`~coalaip.models.Copyright` instance

        INSTANTIATION NOTES
        """

        rights_of = data.get('rightsOf')

        if not isinstance(rights_of, str):
            raise EntityDataError(("'rightsOf' must be given as a string in "
                                   "the 'data' of Copyrights. "
                                   "Given '{}' instead.".format(rights_of)))

        super().__init__(data, entity_type=entity_type, plugin=plugin, **kwargs)


class GenericDerivedRight(Right):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='GenericDerivedRight', plugin,
                 **kwargs):
        """Initialize a :class:`~coalaip.models.GenericDerivedRight`
        instance

        INSTANTIATION NOTES
        """

        super().__init__(data, entity_type=entity_type, plugin=plugin, **kwargs)


class RightsAssignment(CoalaIpEntity):
    """

    INSTANTIATION NOTES
    """

    def __init__(self, data, *, entity_type='RightsTransferAction', plugin,
                 **kwargs):
        """Initialize a :class:`~coalaip.models.RightsAssignment`
        instance

        INSTANTIATION NOTES
        """

        super().__init__(data, entity_type=entity_type, plugin=plugin, **kwargs)

    def create(self):
        raise EntityError(('RightsAssignments can only created through '
                           'transer transactions.'))
