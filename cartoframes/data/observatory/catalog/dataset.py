from __future__ import absolute_import

import pandas as pd
import geopandas as gpd

from shapely import wkt

from .entity import CatalogEntity
from .repository.dataset_repo import get_dataset_repo
from .repository.geography_repo import get_geography_repo
from .repository.variable_repo import get_variable_repo
from .repository.variable_group_repo import get_variable_group_repo
from .repository.constants import DATASET_FILTER
from .summary import dataset_describe, head, tail, counts, fields_by_type, geom_coverage
from . import subscription_info
from . import subscriptions
from . import utils

DATASET_TYPE = 'dataset'


class Dataset(CatalogEntity):
    """A Dataset represents the metadata of a particular dataset in the Data Observatory platform."""

    entity_repo = get_dataset_repo()

    @property
    def variables(self):
        """Get the list of variables that correspond to this dataset.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of Variable instances.

        """

        return get_variable_repo().get_all({DATASET_FILTER: self.id})

    @property
    def variables_groups(self):
        """Get the list of variables groups related to this dataset.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of VariableGroup instances.

        """
        return get_variable_group_repo().get_all({DATASET_FILTER: self.id})

    @property
    def name(self):
        """Name of this dataset."""

        return self.data['name']

    @property
    def description(self):
        """Description of this dataset."""

        return self.data['description']

    @property
    def provider(self):
        """Id of the Provider of this dataset."""

        return self.data['provider_id']

    @property
    def provider_name(self):
        return self.data['provider_name']

    @property
    def category(self):
        """Id of the Category assigned to this dataset."""

        return self.data['category_id']

    @property
    def category_name(self):
        return self.data['category_name']

    @property
    def data_source(self):
        """Id of the data source of this dataset."""

        return self.data['data_source_id']

    @property
    def country(self):
        """Code (ISO 3166-1 alpha-3) of the country of this dataset."""

        return self.data['country_id']

    @property
    def language(self):
        """Code (ISO 639-3) of the language that corresponds to the data of this dataset. """

        return self.data['lang']

    @property
    def geography(self):
        """Id of the Geography associated to this dataset."""

        return self.data['geography_id']

    @property
    def geography_name(self):
        return self.data['geography_name']

    @property
    def geography_description(self):
        return self.data['geography_description']

    @property
    def temporal_aggregation(self):
        """Time amount in which data is aggregated in this dataset."""

        return self.data['temporal_aggregation']

    @property
    def time_coverage(self):
        """Time range that covers the data of this dataset."""

        return self.data['time_coverage']

    @property
    def update_frequency(self):
        """Frequency in which the dataset is updated."""

        return self.data['update_frequency']

    @property
    def version(self):
        """Version info of this dataset."""

        return self.data['version']

    @property
    def is_public_data(self):
        """True if the content of this dataset can be accessed with public credentials. False otherwise."""

        return self.data['is_public_data']

    @property
    def summary(self):
        """JSON object with extra metadata that summarizes different properties of the dataset content."""

        return self.data['summary_json']

    def head(self):
        data = self.data['summary_json']
        return head(self.__class__, data)

    def tail(self):
        data = self.data['summary_json']
        return tail(self.__class__, data)

    def counts(self):
        data = self.data['summary_json']
        return counts(data)

    def fields_by_type(self):
        data = self.data['summary_json']
        return fields_by_type(data)

    def geom_coverage(self):
        return geom_coverage(self.geography)

    def describe(self):
        return dataset_describe(self.variables)

    @classmethod
    def get_all(cls, filters=None, credentials=None):
        """Get all the Dataset instances that comply with the indicated filters (or all of them if no filters
        are passed. If credentials are given, only the datasets granted for those credentials are returned.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If provided, only datasets granted for those credentials are
                returned.

            filters (dict, optional):
                Dict containing pairs of dataset properties and its value to be used as filters to query the available
                datasets. If none is provided, no filters will be applied to the query.

        Returns:
            :py:class:`CatalogList <cartoframes.data.observatory.entity.CatalogList>` List of Dataset instances.

        """

        return cls.entity_repo.get_all(filters, credentials)

    def download(self, credentials=None):
        """Download Dataset data.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.
        """

        return self._download(credentials)

    @classmethod
    def get_datasets_spatial_filtered(cls, filter_dataset):
        user_gdf = cls._get_user_geodataframe(filter_dataset)

        # TODO: check if the dataframe has a geometry column if not exception
        # Saving memory
        user_gdf = user_gdf[[user_gdf.geometry.name]]
        catalog_geographies_gdf = get_geography_repo().get_geographies_gdf()
        matched_geographies_ids = cls._join_geographies_geodataframes(catalog_geographies_gdf, user_gdf)

        # Get Dataset objects
        return get_dataset_repo().get_all({'geography_id': matched_geographies_ids})

    @staticmethod
    def _get_user_geodataframe(filter_dataset):
        if isinstance(filter_dataset, gpd.GeoDataFrame):
            # Geopandas dataframe
            return filter_dataset

        if isinstance(filter_dataset, str):
            # String WKT
            df = pd.DataFrame([{'geometry': filter_dataset}])
            df['geometry'] = df['geometry'].apply(wkt.loads)
            return gpd.GeoDataFrame(df)

    @staticmethod
    def _join_geographies_geodataframes(geographies_gdf1, geographies_gdf2):
        join_gdf = gpd.sjoin(geographies_gdf1, geographies_gdf2, how='inner', op='intersects')
        return join_gdf['id'].unique()

    def subscribe(self, credentials=None):
        """Subscribe to a Dataset.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.
        """

        _credentials = self._get_credentials(credentials)
        _subscribed_ids = subscriptions.get_subscription_ids(_credentials)

        if self.id in _subscribed_ids:
            utils.display_existing_subscription_message(self.id, DATASET_TYPE)
        else:
            utils.display_subscription_form(self.id, DATASET_TYPE, _credentials)

    def subscription_info(self, credentials=None):
        """Get the subscription information of a Dataset.

        Args:
            credentials (:py:class:`Credentials <cartoframes.auth.Credentials>`, optional):
                credentials of CARTO user account. If not provided,
                a default credentials (if set with :py:meth:`set_default_credentials
                <cartoframes.auth.set_default_credentials>`) will be used.
        """

        _credentials = self._get_credentials(credentials)

        return subscription_info.SubscriptionInfo(
            subscription_info.fetch_subscription_info(self.id, DATASET_TYPE, _credentials))
