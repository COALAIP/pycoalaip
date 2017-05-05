"""High-level functions for interacting with COALA IP entities"""

import attr

from collections import namedtuple
from coalaip.exceptions import (
    EntityNotYetPersistedError,
    IncompatiblePluginError,
    ModelDataError,
)
from coalaip.entities import Copyright, Right, Manifestation, Work
from coalaip.plugin import AbstractPlugin


RegistrationResult = namedtuple('RegistrationResult',
                                ['copyright', 'manifestation', 'work'])


@attr.s(frozen=True, repr=False)
class CoalaIp:
    """High-level, plugin-bound COALA IP functions.

    Instantiated with an subclass implementing the ledger plugin
    interface (:class:`~.AbstractPlugin`) that will automatically be
    bound to all top-level functions:

        - :func:`generate_user`
        - :func:`register_manifestation`
        - :func:`derive_right`
        - :func:`transfer_right`

    Attributes:
        plugin (Plugin): Bound persistence layer plugin.
    """
    plugin = attr.ib(validator=attr.validators.instance_of(AbstractPlugin))

    def __repr__(self):
        return 'CoalaIp bound to plugin: {}'.format(self.plugin)

    def generate_user(self, *args, **kwargs):
        """Generate a new user for the backing persistence layer.

        Args:
            *args: Argument list passed to the plugin's
                ``generate_user()``
            **kwargs: Keyword arguments passed to the plugin's
                ``generate_user()``

        Returns:
            A representation of a user, based on the persistence layer
            plugin

        Raises:
            :exc:`~.PersistenceError`: If a user couldn't be generated
                on the persistence layer
        """

        return self.plugin.generate_user(*args, **kwargs)

    def register_work(self, work_data, *, copyright_holder, **kwargs):
        """Register a work"""

        work = Work.from_data(work_data, plugin=self.plugin)
        work.create(copyright_holder, **kwargs)
        return work

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
            :class:`~.IncompatiblePluginError`: If the
                :attr:`existing_work` is not using a compatible plugin
            :exc:`~.EntityNotYetPersistedError`: If the
                :attr:`existing_work` is not associated with an id on the
                persistence layer (:attr:`~.Entity.persist_id`) yet
            :exc:`~.EntityCreationError`: If the manifestation, its
                copyright, or the automatically created work (if no
                existing work is given) fail to be created on the
                persistence layer
            :exc:`~.PersistenceError`: If any other error occurred with
                the persistence layer
        """

        # TODO: in the future, we may want to consider blocking (or asyncing) until
        # we confirm that an entity has actually been created

        work = None
        if not manifestation_data.get('manifestationOfWork'):
            if existing_work is None:
                if work_data is None:
                    work_data = {'name': manifestation_data.get('name')}
                work = Work.from_data(work_data, plugin=self.plugin)
                work.create(copyright_holder, **kwargs)
            else:
                if not isinstance(existing_work, Work):
                    raise TypeError(
                        ("'existing_work' argument to "
                         "'register_manifestation()' must be a Work. Given an "
                         "instance of '{}'".format(type(existing_work))))
                elif existing_work.persist_id is None:
                    raise EntityNotYetPersistedError(
                        ("Work given as 'existing_work' to "
                         "'register_manifestation()' must be already created "
                         'on the backing persistence layer.'))
                elif existing_work.plugin != self.plugin:
                    raise IncompatiblePluginError([
                        self.plugin,
                        existing_work.plugin,
                    ])
                work = existing_work
            manifestation_data['manifestationOfWork'] = work.persist_id

        manifestation = Manifestation.from_data(manifestation_data,
                                                plugin=self.plugin)
        manifestation.create(copyright_holder, **kwargs)

        copyright_data = {'rightsOf': manifestation.persist_id}
        manifestation_copyright = Copyright.from_data(copyright_data,
                                                      plugin=self.plugin)
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
                If ``source`` is provided in the dict, the
                :attr:`source_right` parameter is ignored.
            current_holder (any, keyword): The current holder of the
                :attr:`source_right`; must be specified in the format
                required by the persistence layer
            source_right (:class:`~.Right`, keyword, optional): An
                already persisted Right that the new Right is allowed by.
                Must be using the same plugin that :class:`CoalaIp` was
                instantiated with.
                Ignored if ``source`` is provided in :attr:`right_data`.
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
            :exc:`~.EntityNotYetPersistedError`: If the
                :attr:`source_right` is not associated with an id on the
                persistence layer (:attr:`~.Entity.persist_id`) yet
            :exc:`~.EntityCreationError`: If the Right fails to be
                created on the persistence layer
            :exc:`~.PersistenceError`: If any other error occurred with
                the persistence layer
        """

        if right_data.get('source'):
            # Try to load the given `source` as either a Copyright or Right
            try:
                try:
                    source_right = Copyright.from_persist_id(
                        right_data['source'], plugin=self.plugin,
                        force_load=True)
                except ModelDataError:
                    source_right = Right.from_persist_id(
                        right_data['source'], plugin=self.plugin,
                        force_load=True)
            except ModelDataError as ex:
                raise ModelDataError(
                    ("Entity loaded for 'source' ('{source}') given in "
                     "'right_data' was not a Right or Copyright").format(
                         source=right_data['source'])) from ex
        else:
            if source_right is None:
                raise ValueError(("'source_right' argument to 'derive_right() "
                                  "must be provided if 'source' is not "
                                  "given as part of 'right_data'"))
            elif not isinstance(source_right, Right):
                raise TypeError(("'source_right' argument to 'derive_right()' "
                                 'must be a Right (or subclass). Given an '
                                 "instance of '{}'".format(type(source_right))))
            elif source_right.persist_id is None:
                raise EntityNotYetPersistedError(
                    ("Right given as 'source_right' to 'derive_right()' must "
                     'be already created on the backing persistence layer.')
                )
            elif source_right.plugin != self.plugin:
                raise IncompatiblePluginError([
                    self.plugin,
                    source_right.plugin,
                ])

            right_data['source'] = source_right.persist_id

        if not self.plugin.is_same_user(source_right.current_owner,
                                        current_holder):
            raise ModelDataError(
                ("The given source Right (either as a 'source' property of "
                 "'right_data' or as 'source_right') is not currently held by "
                 "the given 'current_holder'"))

        right = right_entity_cls.from_data(right_data, plugin=self.plugin)
        right.create(current_holder, **kwargs)
        return right

    def transfer_right(self, right, rights_assignment_data=None, *,
                       current_holder, to, **kwargs):
        """Transfer a Right to another user.

        Args:
            right (:class:`~.Right`): An already persisted Right to
                transfer
            rights_assignment_data (dict, optional): Model data for the
                generated :class:`~.RightsAssignment` that will be
                associated with the transfer
            current_holder (any, keyword): The current holder of the
                :attr:`right`; must be specified in the format
                required by the persistence layer
            to (any, keyword): The new holder of the right; must be
                specified in the format required by the persistence
                layer.
                If the specified user format includes private
                information (e.g. a private key) but is not required by
                the persistence layer to identify a transfer recipient,
                then this information may be omitted in this argument.
            **kwargs: keyword arguments passed through to the
                :attr:`right`'s ``transfer`` method (e.g.
                :meth:`~.Right.transfer`'s ``rights_assignment_format``)

        Returns:
            :class:`~.RightsAssignment`: the RightsAssignment entity
            associated with this transfer

        Raises:
            :exc:`~.EntityNotYetPersistedError`: If the :attr:`right`
                has not been persisted yet
            :exc:`~.EntityNotFoundError`: If the :attr:`right` was not
                found on the persistence layer
            :exc:`~.EntityTransferError`: If the :attr:`right` fails to
                be transferred on the persistence layer
            :exc:`~.PersistenceError`: If any other error occurred with
                the persistence layer
        """

        if not isinstance(right, Right):
            raise TypeError(("'right' argument to 'transfer_right()' must be "
                             'a Right (or subclass). Given '
                             "'{}'".format(right)))
        elif right.persist_id is None:
            raise EntityNotYetPersistedError(
                ("Right given as 'right' to 'transfer_right()' must be "
                 'already created on the backing persistence layer.')
            )
        elif right.plugin != self.plugin:
            raise IncompatiblePluginError([self.plugin, right.plugin])

        return right.transfer(rights_assignment_data, from_user=current_holder,
                              to_user=to, **kwargs)
