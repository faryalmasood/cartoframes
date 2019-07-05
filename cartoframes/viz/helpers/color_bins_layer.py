from __future__ import absolute_import

from ..layer import Layer


def color_bins_layer(source, value, title='', method='quantiles', bins=5, palette=None, description='', footer=''):
    """Helper function for quickly creating a classed color map

    Args:
        source (:py:class:`Dataset <cartoframes.data.Dataset>` or str): Dataset
          or text representing a table or query associated with user account.
        value (str): Column to symbolize by
        title (str, optional): Title of legend
        bins (int, optional): Number of classes (bins) for map. Default is 5.
        palette (str, optional): Palette that can be a named cartocolor palette
          or other valid CARTO VL palette expression. Default is `purpor`.

    Returns:
        cartoframes.viz.Layer: Layer styled by `value`. Includes Legend and
        popup on `value`.
    """
    return Layer(
        source,
        style={
            'point': {
                'color': 'ramp(global{0}(${1}, {2}), {3})'.format(method, value, bins, palette or 'purpor')
            },
            'line': {
                'color': 'ramp(global{0}(${1}, {2}), {3})'.format(method, value, bins, palette or 'purpor')
            },
            'polygon': {
                'color': 'opacity(global{0}(${1}, {2}), {3}), 0.9)'.format(method, value, bins, palette or 'purpor')
            }
        },
        popup={
            'hover': {
                'title': title or value,
                'value': '$' + value
            }
        },
        legend={
            'type': {
                'point': 'color-bins-point',
                'line': 'color-bins-line',
                'polygon': 'color-bins-polygon'
            },
            'title': title or value,
            'description': '',
            'description': description,
            'footer': footer
        }
    )
