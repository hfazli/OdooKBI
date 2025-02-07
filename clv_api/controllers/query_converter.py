import re

from ..utils.type_checker import TypeChecker


class LocatedInOperator:

    def __init__(self, root_id: str, include_root: bool = False):
        self._root_id = root_id
        self._include_root = include_root

    @property
    def root_id(self) -> str:
        return self._root_id

    @property
    def include_root(self) -> bool:
        return self._include_root


class QueryConverter:
    """
    Used to convert InventoryAPI query structure object to odoo's domain query list
    """

    # all integer-mapped types of filter
    _plain_int_types = {
        'Char' : True,
        'SByte' : True,
        'Byte': True,
        'Int16': True,
        'UInt16': True,
        'Int32': True,
        'UInt32': True,
        'Int64': True,
        'UInt64': True,
    }

    # maps api operation name to odoo domain operation
    # noinspection SpellCheckingInspection
    _odoo_operations_map = {
        'Equal': '=',
        'NotEqual': '!=',
        'Less': '<',
        'Greater': '>',
        'LessOrEqual': '<=',
        'GreaterOrEqual': '>=',
        'Contains': 'ilike',
        'StartsWith': '=ilike',
        'Or': '|',
        'And': '&',
        'Not': '!'
    }

    def convert_api_where_expression_to_domain_filter(self, where_root, field_name_map):
        """
        Converts filter where expression do domain list query in ODOO
        @param where_root: the root of the where expression
        @param field_name_map: filed map
        @return:
        """
        return self._convert_node(where_root, field_name_map)

    def _convert_node(self, where_root, api_to_odoo_field_map):
        if not where_root:
            return []
        node_type = where_root.get('nodeType')
        value = where_root.get('value')
        operands = where_root.get('operands')

        if node_type == 'Field':
            if str(value.get('value') or '').lower().startswith('locatedIn'.lower()):
                root_id, include_root = self._extract_located_in_func(value.get('value').lower())
                return LocatedInOperator(root_id, include_root)
            field_info = api_to_odoo_field_map.get(value.get('value').lower())
            if not field_info:
                raise RuntimeError('Unknown field name for the query: ' + str(value.get('value')))
            return [field_info.odoo_name]
        if node_type == 'Value':
            if not value or value.get('valueType') == 'DBNull':
                return []
            return [self._convert_plain_value(value.get('value'), value.get('valueType'))]

        result = []
        if node_type == 'Not':
            arg = self._convert_node(operands[0], api_to_odoo_field_map)
            result.append('!')
            result.extend(arg)
        elif node_type == 'Or' or node_type == 'And':
            arg1 = self._convert_node(operands[0], api_to_odoo_field_map)
            arg2 = self._convert_node(operands[1], api_to_odoo_field_map)
            result.append(self._odoo_operations_map[node_type])
            result.extend(arg1)
            result.extend(arg2)
        else:
            mapped_operation = self._odoo_operations_map.get(node_type)
            if not mapped_operation:
                raise RuntimeError('Unknown where expression node type ' + str(node_type))
            arg1 = self._convert_node(operands[0], api_to_odoo_field_map)
            if isinstance(arg1, LocatedInOperator):
                return [('located_in', '=', arg1)]
            arg2 = self._convert_node(operands[1], api_to_odoo_field_map)
            if len(arg1) != 1 or len(arg2) != 1:
                raise RuntimeError('Invalid operands of binary operation in query filter')
            if operands[0].get('nodeType') == 'Field' and operands[1].get('nodeType') == 'Value':
                field_name = operands[0].get('value').get('value')
                field_info = api_to_odoo_field_map.get(field_name.lower())
                if not field_info:
                    raise RuntimeError('Unknown field name for the query: ' + str(field_name))
                if field_info.odoo_type:
                    # If api_type allows None, but odoo_type does not, we need to replace the value.
                    # For example, if api_type is str and odoo_type is int, operation int(None) can't be done.
                    if (not arg2[0] or arg2[0] == 'None') and field_info.odoo_null_value_equivalent:
                        arg2[0] = field_info.odoo_null_value_equivalent
                    arg2[0] = field_info.odoo_type(arg2[0])

            if mapped_operation == '=ilike':
                arg2[0] = '{}%'.format(arg2[0])

            result = [(arg1[0], mapped_operation, arg2[0])]
        return result

    def _convert_plain_value(self, plain_value, plain_type):
        if plain_type == 'String':
            return str(plain_value) if plain_value else ''
        if plain_type == 'DateTime':
            #  the date-time notation as defined by RFC 3339, section 5.6, for example, 2017-07-21T17:32:28Z
            return TypeChecker.get_as_datetime(plain_value)
        if plain_type in self._plain_int_types:
            return int(plain_value)
        if plain_type == 'Boolean':
            return TypeChecker.get_as_bool(plain_value)
        if plain_type == 'Single' or plain_type == 'Double' or plain_type == 'Decimal':
            return float(plain_value)
        raise RuntimeError('Unknown plain value type in query')

    def _extract_located_in_func(self, plain_value):
        pattern_with_bool = r'locatedin\(\"(.*?)\", (\w+)\)'
        pattern_without_bool = r'locatedin\(\"(.*?)\"\)'

        match = re.match(pattern_with_bool, plain_value)
        if match:
            x, y = match.groups()
            return TypeChecker.get_as_str(x), TypeChecker.get_as_bool(y)

        match = re.match(pattern_without_bool, plain_value)
        if match:
            x, = match.groups()
            return TypeChecker.get_as_str(x), True

        raise RuntimeError("Unable to extract located-in function from '{}'".format(plain_value))
