from typing import List, Tuple, Any


from .common_utils import CommonUtils
from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from ..utils.domain_transformer import DomainTransformerBuilder, Transformations
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class TableLocationsProcessor(TableProcessorBase):
    """
    Process location table requests.
    The structure of the TableLocationRow object is:
    id:
        type: string
        description: id of the location
    name:
        type: string
        description: name of the location
    barcode:
        type: string
        description: barcode of the location
    isGroup:
        type: boolean
        description: defines if the location has child locations
    notSelectable:
        type: boolean
        description: defines if the location can be selected on the mobile device
    parentId:
        type: string
        description: id of the parent location
    description:
        type: string
        description: description of the location
    """

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=str),
        FieldInfo(api_name_arg='name', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='barcode', api_type_arg=str, odoo_name_arg='barcode', odoo_type_arg=str),
        FieldInfo(api_name_arg='description', api_type_arg=str, odoo_name_arg='description', odoo_type_arg=str),
        FieldInfo(api_name_arg='notSelectable'.lower(), api_type_arg=bool, odoo_name_arg='not_selectable', odoo_type_arg=bool),
        FieldInfo(api_name_arg='isGroup'.lower(), api_type_arg=bool, odoo_name_arg='is_group', odoo_type_arg=bool),
        FieldInfo(api_name_arg='parentId'.lower(), api_type_arg=str, odoo_name_arg='parent_id', odoo_type_arg=str, odoo_null_value_equivalent_arg='-1')
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

        builder = DomainTransformerBuilder()
        builder.add_transformation_for_field('barcode', location_barcode_transformation)
        builder.add_transformation_for_field('description', Transformations.nonexistent_field_transformation)
        builder.add_transformation_for_field('name', location_name_transformation)
        builder.add_transformation_for_field('not_selectable', location_not_selectable_transformation),
        builder.add_transformation_for_field('is_group', location_is_group_transformation)
        builder.add_transformation_for_field('parent_id', location_parent_id_transformation)
        builder.add_transformation_for_field('located_in', location_located_in_transformation)
        self._locations_domain_transformer = builder.build()

        builder = DomainTransformerBuilder()
        builder.add_transformation_for_field('id', warehouse_id_field_transformation)
        builder.add_transformation_for_field('barcode', Transformations.nonexistent_field_transformation)
        builder.add_transformation_for_field('description', Transformations.nonexistent_field_transformation)
        builder.add_transformation_for_field('not_selectable', warehouse_not_selectable_field_transformation)
        builder.add_transformation_for_field('is_group', warehouse_is_group_field_transformation)
        builder.add_transformation_for_field('parent_id', warehouse_parent_id_field_transformation)
        builder.add_transformation_for_field('located_in', warehouse_located_in_transformation)
        self._warehouses_domain_transformer = builder.build()

    def _get_rows_int(self, env: OdooEnvWrapper, query, device_info, offset, limit, request_count: bool):
        where_root = query.get('whereTreeRoot')

        # pick_doc = self.cutils.get_odoo_doc_from_device_info(env, device_info)

        additional_domain = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)

        # self.cutils.append_company_filter_by_doc(additional_domain, pick_doc)

        # location_parent_path = self.cutils.get_location_parent_path_from_document(pick_doc)
        # if location_parent_path:
        #     additional_domain.append(('parent_path', '=like', location_parent_path + '%'))

        if request_count:
            return [self._get_clv_locations_count(env, additional_domain), None]

        return [None, self._get_clv_locations(env, additional_domain, limit, offset)]

    def _get_clv_locations_count(self, env: OdooEnvWrapper, additional_domain) -> int:
        warehouses_domain = []
        warehouses_domain.extend(self._warehouses_domain_transformer.transform(env, additional_domain))
        warehouses_count = env.warehouses.search_count(warehouses_domain)

        locations_domain = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
            '|',
            ('company_id', '=', False),
            ('company_id.active', '=', True),
            '|',
            ('warehouse_id', '=', False),
            ('warehouse_id.active', '=', True)
        ]
        locations_domain.extend(self._locations_domain_transformer.transform(env, additional_domain))
        locations_count = env['stock.location'].search_count(locations_domain)

        return warehouses_count + locations_count

    def _get_clv_locations(self, env: OdooEnvWrapper, additional_domain, limit, offset):
        result = []

        warehouses_domain = []
        warehouses_domain.extend(self._warehouses_domain_transformer.transform(env, additional_domain))
        warehouses = env.warehouses.search(warehouses_domain, limit=limit, offset=offset, order='id ASC')

        for warehouse in warehouses:
            result.append({
                'id': CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id),
                'name': self._model_converter.clear_to_str(warehouse.name),
                'isGroup': bool(warehouse.lot_stock_id.id),
                'notSelectable': True,
                'parentId': self._model_converter.clear_to_str(warehouse.view_location_id.location_id.id)
            })

        locations_domain_filter = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
            '|',
            ('company_id', '=', False),
            ('company_id.active', '=', True),
            '|',
            ('warehouse_id', '=', False),
            ('warehouse_id.active', '=', True)
        ]
        locations_domain_filter.extend(self._locations_domain_transformer.transform(env, additional_domain))
        locations = env['stock.location'].search(locations_domain_filter, limit=limit, offset=offset, order='id ASC')

        for location in locations:
            parent_id = None
            if location.location_id:
                parent_id = location.location_id.id

            if location.usage == 'view':
                if location.warehouse_id:
                    if location.warehouse_id in warehouses:
                        parent_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(location.warehouse_id.id)

            barcode = location.complete_name
            if location.barcode:
                barcode = location.barcode

            not_selectable = not location.active \
                or location.usage in ['view'] \
                or (env.w15_settings.allow_only_lowest_level_locations and len(location.child_ids) > 0)

            result.append({
                'id': self._model_converter.clear_to_str(location.id),
                'name': self._model_converter.clear_to_str(location.complete_name),
                'barcode': self._model_converter.clear_to_str(barcode),
                'isGroup': len(location.child_ids) > 0,
                'notSelectable': not_selectable,
                'parentId': self._model_converter.clear_to_str(parent_id)
            })

        return result


def location_barcode_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    return ['|', domain_element, ('complete_name', operator, value)]


def location_name_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    # 'complete_name' is calculated and stored field of 'stock.location'
    # therefore it is not impossible to use it in domain filter directly.
    # To solve this, we use this tricky way with additional request to 'stock.location' table.
    # Direct SQL-request is using to improve performance.
    _, operator, value = domain_element
    if operator == 'ilike':
        value = '%{}%'.format(value)
    elif operator == '=ilike':
        operator = 'ilike'

    query = f"""
                SELECT id
                FROM stock_location
                WHERE complete_name {operator} '{value}'
            """
    env.cr.execute(query)
    stock_locations = env.cr.fetchall()
    ids = [stock_location[0] for stock_location in stock_locations]

    return [('id', 'in', ids)]


def location_not_selectable_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element

    not_selectable_domain = ['|', ('active', '=', False), ('usage', '=', 'view')]
    if env.w15_settings.allow_only_lowest_level_locations:
        not_selectable_domain = ['|'] + not_selectable_domain + [('child_ids', '!=', False)]

    not_selectable_ids = env['stock.location'].search_read(not_selectable_domain, ['id'])
    not_selectable_ids = [item['id'] for item in not_selectable_ids]
    new_operator = 'in' if not ((operator == '=') ^ value) else 'not in'

    return [('id', new_operator, not_selectable_ids)]


def location_is_group_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    new_operator = '=' if not ((operator == '=') ^ value) else '!='
    return [('child_ids', new_operator, False)]


def location_parent_id_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    if value.startswith('clv_wh_'):
        return [('warehouse_id', operator, CommonUtils.convert_warehouse_id_from_clv_to_odoo(value))]
    return [('location_id', operator, int(value))]


def location_located_in_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, _, value = domain_element
    root_id = value.root_id
    if root_id.startswith('clv_wh_'):
        return [('warehouse_id', '=', CommonUtils.convert_warehouse_id_from_clv_to_odoo(root_id))]
    if value.include_root:
        return ['|', ('id', 'child_if', int(root_id)), ('id', '=', int(root_id))]
    return [('id', 'child_of', int(root_id)), ('id', '!=', int(root_id))]


def warehouse_id_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    field_name, operator, value = domain_element
    if value and isinstance(value, str) and value.startswith('clv_wh_'):
        return [(field_name, operator, CommonUtils.convert_warehouse_id_from_clv_to_odoo(value))]
    return [('id', operator, False)]


def warehouse_not_selectable_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    new_operator = '=' if not ((operator == '=') ^ (not value)) else '!='
    return [('id', new_operator, False)]


def warehouse_is_group_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    new_operator = '=' if not ((operator == '=') ^ value) else '!='
    return [('stock_lot_id', new_operator, False)]


def warehouse_parent_id_field_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, operator, value = domain_element
    if value.startswith('clv_wh_'):
        return [('id', operator, False)]

    warehouses_with_view = env.warehouses.search_read([('view_location_id', '!=', False)], ['id', 'view_location_id'])
    if not warehouses_with_view:
        return [('id', operator, False)]

    view_ids = [warehouse['view_location_id'][0] for warehouse in warehouses_with_view]
    location_ids = env['stock.location'].search_read([('id', 'in', view_ids), ('location_id', '=', value)], ['id'])
    if not location_ids:
        return [('id', operator, False)]

    location_ids = [location_id['location_id'] for location_id in location_ids]
    warehouse_ids = []
    for warehouse in warehouses_with_view:
        if warehouse['view_location_id'] in location_ids:
            warehouse_ids.append(warehouse['id'])

    return [('id', 'in', warehouse_ids)]


def warehouse_located_in_transformation(env: OdooEnvWrapper, domain_element: Tuple[str, str, Any]) -> list:
    _, _, value = domain_element
    root_id = value.root_id
    if root_id.startswith('clv_wh_'):
        if value.include_root:
            return [('id', '=', CommonUtils.convert_warehouse_id_from_clv_to_odoo(root_id))]
        return [('id', '=', False)]

    warehouses_with_view = env.warehouses.search_read([('view_location_id', '!=', False)], ['id', 'view_location_id'])
    if not warehouses_with_view:
        return [('id', '=', False)]

    view_ids = [warehouse['view_location_id'][0] for warehouse in warehouses_with_view]
    location_ids = env['stock.location'].search_read([('id', 'in', view_ids), ('location_id', '=', root_id)], ['id'])
    if not location_ids:
        return [('id', '=', False)]

    location_ids = [location_id['location_id'] for location_id in location_ids]
    warehouse_ids = []
    for warehouse in warehouses_with_view:
        if warehouse['view_location_id'] in location_ids:
            warehouse_ids.append(warehouse['id'])

    return [('id', 'in', warehouse_ids)]
