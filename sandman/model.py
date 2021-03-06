"""The Model class is meant to be the base class for user Models. It represents
a table in the database that should be modeled as a resource."""
# pylint: disable=pointless-string-statement

# Standard library imports
from decimal import Decimal

# Third-party imports
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # pylint: disable=invalid-name


class Model(object):
    """A mixin class containing the majority of the RESTful API functionality.

    :class:`sandman.Model` is the base class from which user models
    are derived.

    """

    __endpoint__ = None
    """override :attr:`__endpoint__` if you wish to configure the
    :class:`sandman.model.Model`'s endpoint.

    Default: __tablename__ in lowercase and pluralized

    """

    __tablename__ = None
    """The name of the database table this class should be mapped to

    Default: None

    """

    __top_level_json_name__ = 'resources'
    """The top level json text to output for this class

    Default: ``resources``

    """

    __methods__ = ('GET', 'POST', 'PATCH', 'DELETE', 'PUT')
    """override :attr:`__methods__` if you wish to change the HTTP methods
    this :class:`sandman.model.Model` supports.

    Default: ``('GET', 'POST', 'PATCH', 'DELETE', 'PUT')``

    """

    __table__ = None
    """Will be populated by SQLAlchemy with the table's meta-information."""

    __from_class__ = None
    """Is this class being generated from an existing declarative SQLAlchemy
    class?"""

    @classmethod
    def endpoint(cls):
        """Return the :class:`sandman.model.Model`'s endpoint.

        :rtype: string

        """
        endpoint = cls.__table__.name.lower()
        if not endpoint.endswith('s'):
            endpoint += 's'
        return endpoint

    def resource_uri(self):
        """Return the URI at which the resource can be found.

        :rtype: string

        """
        primary_key_value = getattr(self, self.primary_key(), None)
        return '/{}/{}'.format(self.endpoint(), primary_key_value)

    @classmethod
    def primary_key(cls):
        """Return the name of the table's primary key

        :rtype: string

        """

        return cls.__table__.primary_key.columns.values()[0].name

    def links(self):
        """Return a list of links for endpoints related to the resource.

        :rtype: list

        """

        links = []
        for foreign_key in self.__table__.foreign_keys:
            column = foreign_key.column.name
            column_value = getattr(self, column, None)
            if column_value:
                table = foreign_key.column.table.name
                links.append({'rel': 'related', 'uri': '/{}/{}'.format(
                    table, column_value)})
        links.append({'rel': 'self', 'uri': self.resource_uri()})
        return links

    def as_dict(self):
        """Return a dictionary containing only the attributes which map to
        an instance's database columns.

        :rtype: dict

        """
        result_dict = {column: getattr(self, column, None) for column in
                       self.__table__.columns.keys()}
        for column in result_dict:
            if isinstance(result_dict[column], Decimal):
                result_dict[column] = str(result_dict[column])
        result_dict['_links'] = self.links()
        return result_dict

    def from_dict(self, dictionary):
        """Set a set of attributes which correspond to the
        :class:`sandman.model.Model`'s columns.

        :param dict dictionary: A dictionary of attributes to set on the
            instance whose keys are the column names of
            the :class:`sandman.model.Model`'s underlying database table.

        """

        for column in self.__table__.columns.keys():
            value = dictionary.get(column, None)
            if value:
                setattr(self, column, value)

    def replace(self, dictionary):
        """Set all attributes which correspond to the
        :class:`sandman.model.Model`'s columns to the values in *dictionary*,
        inserting None if an attribute's value is not specified.

        :param dict dictionary: A dictionary of attributes to set on the
            instance whose keys are the column names of the
            :class:`sandman.model.Model`'s underlying database table.

        """

        for column in self.__table__.columns.keys():
            setattr(self, column, None)
        self.from_dict(dictionary)

    @classmethod
    def meta(cls):
        """Return a dictionary containing meta-information about the given
        resource."""
        attribute_info = {}
        for name, value in cls.__table__.columns.items():
            attribute_info[name] = str(value.type).lower()

        return {cls.__name__: attribute_info}
