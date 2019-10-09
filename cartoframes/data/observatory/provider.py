from __future__ import absolute_import

from .entity import CatalogEntity
from .repository.provider_repo import get_provider_repo
from .repository.dataset_repo import get_dataset_repo


class Provider(CatalogEntity):

    entity_repo = get_provider_repo()

    @property
    def datasets(self):
        return get_dataset_repo().get_by_provider(self.id)

    @property
    def name(self):
        return self.data['name']