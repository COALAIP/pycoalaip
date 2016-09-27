"""High-level functions for interacting with COALA IP entities"""

from collections import namedtuple
from coalaip.exceptions import (
    EntityNotYetPersistedError,
    IncompatiblePluginError,
)
from coalaip.entities import Copyright, Right, Manifestation, Work
from coalaip.plugin import AbstractPlugin


RegistrationResult = namedtuple('RegistrationResult',
                                ['copyright', 'manifestation', 'work'])


class CoalaIp:
    """High-level, plugin-bound COALA IP functions.

    Instantiated with an subclass implementing the ledger plugin
    interface (:class:`~.AbstractPlugin`) that will automatically be
    bound to all top-level functions:

        - :func:`generate_user`
        - :func:`register_manifestation`
        - :func:`derive_right`
        - :func:`transfer_right`
    """

    def __init__(self, plugin):
        """Instantiate a new CoalaIp wrapper object.

        Args:
            plugin (Plugin, keyword): Persistence layer plugin
        """

        if not isinstance(plugin, AbstractPlugin):
            raise TypeError(('A plugin subclassing '
                             "'coalaip.plugin.AbstractPlugin' must be "
                             'provided when instantiating a CoalaIp instance. '
                             'Given a plugin of type '
                             "'{}' instead.".format(type(plugin))))
        self._plugin = plugin

    def __repr__(self):
        return 'CoalaIp bound to plugin: {}'.format(self._plugin)

    def generate_user(self, *args, **kwargs):
        """Generate a new user for the backing persistence layer.

        Args:
            *args: argument list passed to the plugin's generate_user()
            **kwargs: keyword arguments passed to the plugin's
                ``generate_user()``

        Returns:
            a representation of a user, based on the persistence layer
            plugin
        """

        return self._plugin.generate_user(*args, **kwargs)

    # TODO: could probably have a 'safe' check to make sure the entities are actually created
    def register_manifestation(self, manifestation_data, *, copyright_holder,
                               existing_work=None, work_data=None, **kwargs):
        """Register a Manifestation and automatically assign its
        corresponding Copyright to the given :attr:`user`.

        Unless specified (see :attr:`existing_work`), also registers a
        new Work for the Manifestation.

        Args:
            manifestation_data (dict): Model data for the
                :class:`.Manifestation`.
                See :class:`~.Manifestation` for requirements.
                If ``manifestationOfWork`` is provided in the dict, the
                :attr:`existing_work` and :attr:`work_data` parameters are
                ignored and no Work is registered.
            copyright_holder (any, keyword): The user to hold the
                corresponding Copyright of the registered Manifestation;
                must be specified in the format required by the
                persistence layer
            existing_work (:class:`~.Work`, keyword, optional): An
                already persisted Work that the Manifestation is derived
                from.
                Must be using the same plugin that :class:`CoalaIp` was
                instantiated with.
                If specified, the :attr:`work_data` parameter is ignored
                and no Work is registered.
            work_data (dict, keyword, optional): Model data for the Work
                that will automatically generated for the Manifestation
                if no :attr:`existing_work` was specified.
                See :class:`~.Work` for requirements.
                If not specified, the Work will be created using only
                the name of the Manifestation.
            **kwargs: Keyword arguments passed through to each model's
                :meth:`~.Entity.create` (e.g. ``data_format``).

        Returns:
            :class:`~.RegistrationResult`: A :obj:`namedtuple`
            containing the Coypright of the registered Manifestation,
            the registered Manifestation, and the Work as named fields::

                (
                    'copyright': (:class:`~.Copyright`),
                    'manifestation': (:class:`~.Manifestation`),
                    'work': (:class:`~.Work`),
                )

            If ``manifestationOfWork`` was provided in
            :attr:`manifestation_data`, None will be returned for the
            Work; otherwise, the given :attr:`existing_work` or
            automatically created Work will be returned.

        Raises:
            :exc:`~.ModelDataError`: If the :attr:`manifestation_data`
                or :attr:`work_data` contain invalid or are missing
                required properties.
            :exc:`~.EntityNotYetPersistedError`: if the
                :attr:`existing_work` is not associated with an id on the
                persistence layer (:attr:`~.Entity.persist_id`) yet
            :exc:`~.EntityCreationError`: if the manifestation, its
                copyright, or the automatically created work (if no
                existing work is given) fail to be created on the
                persistence layer
            :class:`~.IncompatiblePluginError`: If the
                :attr:`existing_work` is not using a compatible plugin
        """

        # TODO: in the future, we may want to consider blocking (or asyncing) until
        # we confirm that an entity has actually been created

        work = None
        if not manifestation_data.get('manifestationOfWork'):
            work = existing_work
            if existing_work is None:
                if work_data is None:
                    work_data = {'name': manifestation_data.get('name')}
                work = Work.from_data(work_data, plugin=self._plugin)
                work.create(copyright_holder, **kwargs)
            elif not isinstance(existing_work, Work):
                raise TypeError(("'existing_work' argument to "
                                 "'register_manifestation()' must be a Work. "
                                 'Given an instance of '
                                 "'{}'".format(type(existing_work))))
            elif existing_work.persist_id is None:
                raise EntityNotYetPersistedError(
                    ("Work given as 'existing_work' to "
                     "'register_manifestation()' must be already created on "
                     'the backing persistence layer.')
                )
            elif existing_work.plugin != self._plugin:
                raise IncompatiblePluginError([
                    self._plugin,
                    existing_work.plugin,
                ])

            manifestation_data['manifestationOfWork'] = work.persist_id

        manifestation = Manifestation.from_data(manifestation_data,
                                                plugin=self._plugin)
        manifestation.create(copyright_holder, **kwargs)

        copyright_data = {'rightsOf': manifestation.persist_id}
        manifestation_copyright = Copyright.from_data(copyright_data,
                                                      plugin=self._plugin)
        manifestation_copyright.create(copyright_holder, **kwargs)

        return RegistrationResult(manifestation_copyright, manifestation, work)

    def derive_right(self, right_data, *, current_holder, source_right=None,
                     right_entity_cls=Right, **kwargs):
        """Derive a new Right from an existing :attr:`source_right` (a
        :class:`~.Right` or subclass) for the :attr:`current_holder` of
        the :attr:`source_right`. The newly registered Right can then be
        transferred to other Parties.

        Args:
            right_data (dict): Model data for the :attr:`right_entity_cls`.
                See the given :attr:`right_entity_cls` for requirements.
                If ``allowedBy`` is provided in the dict, the
                :attr:`source_right` parameter is ignored.
            current_holder (any, keyword): The current holder of the
                :attr:`source_right`; must be specified in the format
                required by the persistence layer
            source_right (:class:`~.Right`, keyword, optional): An
                already persisted Right that the new Right is allowed by.
                Must be using the same plugin that :class:`CoalaIp` was
                instantiated with.
                Optional if ``allowedBy`` is provided in :attr:`right_data`.
            right_entity_cls (subclass of :class:`~.Right`, keyword, optional):
                The class that must be instantiated for the newly
                derived right.
                Defaults to :class:`~.Right`.
            **kwargs: Keyword arguments passed through to the
                :attr:`right_entity_cls`'s ``create`` method (e.g.
                :meth:`~.Entity.create`'s ``data_format``)

        Returns:
            A registered :attr:`right_entity_cls` Right (by default a
            :class:`~.Right`)

        Raises:
            :exc:`~.ModelDataError`: If the :attr:`right_data`
                contains invalid or is missing required properties.
            :exc:`~.EntityNotYetPersistedError`: if the
                :attr:`source_right` is not associated with an id on the
                persistence layer (:attr:`~.Entity.persist_id`) yet
            :exc:`~.EntityCreationError`: if the Right fails to be
                created on the persistence layer
        """

        if not right_data.get('allowedBy'):
            if source_right is None:
                raise ValueError(("'source_right' argument to 'derive_right() "
                                  "must be provided if 'allowedBy' is not "
                                  "given as part of 'right_data'"))
            if not isinstance(source_right, Right):
                raise TypeError(("'source_right' argument to 'derive_right()' "
                                 'must be a Right (or subclass). Given an '
                                 "instance of '{}'".format(type(source_right))))
            elif source_right.persist_id is None:
                raise EntityNotYetPersistedError(
                    ("Right given as 'source_right' to 'derive_right()' must "
                     'be already created on the backing persistence layer.')
                )
            elif source_right.plugin != self._plugin:
                raise IncompatiblePluginError([
                    self._plugin,
                    source_right.plugin,
                ])

            right_data['allowedBy'] = source_right.persist_id

        right = right_entity_cls.from_data(right_data, plugin=self._plugin)
        right.create(current_holder, **kwargs)
        return right

    def transfer_right(self, right, rights_assignment_data, *, from_user, to_user,
                       data_format=None):
        """Transfer a Right to another user.

        Args:
            right (str): Id of the Right to transfer
            rights_assignment_data (dict): Model data for the
                generated :class:`~.RightsAssignment`
            from_user (any, keyword): A user based on the format
                specified by the persistence layer
            to_user (any, keyword): A user based on the format specified
                by the persistence layer
            data_format (str, keyword, optional): Data format of the
                saved :class:`~.RightsAssignment`; must be one of:
                    - 'jsonld' (default)
                    - 'json'
                    - 'ipld'

        Returns:
        """

        raise NotImplementedError('transfer_right() has not been implemented yet')
