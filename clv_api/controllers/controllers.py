# -*- coding: utf-8 -*-
from typing import Any

from odoo import http
from odoo.http import request
from odoo.release import version_info

from .clv_api_endpoint import clv_api_endpoint
from .documents import DocumentImpl
from .inventory import InventoryImpl
from .tables import TablesImpl
from ..utils.type_checker import TypeChecker
from ..wrappers.odoo_env_wrapper import OdooEnvWrapper


class ClvApi(http.Controller):
    """
    Entry point of the Inventory API controller (module).
    It supports Inventory API endpoints
    """

    # implementation of the /inventory endpoints
    _inventory_impl = InventoryImpl()
    # implementation of the /documents endpoints
    _documents_impl = DocumentImpl()
    # implementation of the /tables endpoints
    _tables_impl = TablesImpl()

    @http.route('/Auth', type='json', auth='public', methods=['POST'])
    @clv_api_endpoint
    def auth(self, body: dict[str, Any], **query_params):
        """
        @deprecated
        May be used by alternative authorization call.
        @return:
        """

        # /Auth endpoint was deprecated due to the fact
        # that on Odoo servers working with multiple databases, the server returns 404 NotFound
        # because public endpoint cannot be resolved in this case.
        # A possible solution could be the server wide module,
        # but it was decided to use authentication via /web/session/authenticate.

        request.session.authenticate(body.get('db'), body.get('login'), body.get('password'))

        current_db = request.env.cr.dbname
        if current_db == body.get('db'):
            env = OdooEnvWrapper(request.env, version_info[0])
            if not env.w15_settings.warehouse15_connected:
                env.w15_settings.warehouse15_connected = True

        return {'authResult': 'success'}

    @http.route('/RegisterConnection', type='json', auth='user', methods=['POST'])
    @clv_api_endpoint
    def register_connection(self, body: dict[str, Any], **query_params):
        env = OdooEnvWrapper(request.env, version_info[0])
        if not env.w15_settings.warehouse15_connected:
            env.w15_settings.warehouse15_connected = True

        return {}

    @http.route('/Inventory/getItems', type='json', auth='user', methods=['POST'])
    @clv_api_endpoint
    def inventory_get_items(self, body: dict[str, Any], **query_params):
        """
        /Inventory/getItems endpoint implementation. Used to get page of inventory items.
        @return: Dictionary as described in Inventory API swagger model
        """
        offset = TypeChecker.get_as_int(query_params.get('offset'))
        limit = TypeChecker.get_as_int(query_params.get('limit'))
        request_count = TypeChecker.get_as_bool(query_params.get('requestCount'))

        return self._inventory_impl.get_items(OdooEnvWrapper(http.request.env, version_info[0]),
                                              query_params.get('parentId'),
                                              offset,
                                              limit,
                                              request_count)

    @http.route('/Inventory/getItemsByString', type='json', auth='user', methods=['POST'])
    @clv_api_endpoint
    def inventory_get_items_by_string(self, body: dict[str, Any], **query_params):
        """
        '/Inventory/getItemsByString' endpoint implementation. Used to search inventory items by string match.
        @return: Dictionary as described in Inventory API swagger model
        """
        offset = TypeChecker.get_as_int(query_params.get('offset'))
        limit = TypeChecker.get_as_int(query_params.get('limit'))
        request_count = TypeChecker.get_as_bool(query_params.get('requestCount'))
        match_string = TypeChecker.get_as_str(query_params.get('matchString'))

        return self._inventory_impl.get_items_by_string(OdooEnvWrapper(http.request.env, version_info[0]),
                                                        match_string,
                                                        offset,
                                                        limit,
                                                        request_count)

    @http.route('/Inventory/getItemsByIds', type='json', auth='user', methods=['POST'])
    @clv_api_endpoint
    def inventory_get_items_by_ids(self, body: dict[str, Any], **query_params):
        """
        '/Inventory/getItemsByIds' endpoint implementation. Used to get inventory items with specified UOM ids.
        @return: Dictionary as described in Inventory API swagger model
        """
        return self._inventory_impl.get_items_by_ids(OdooEnvWrapper(http.request.env, version_info[0]), body.get('idList'))

    @http.route('/Inventory/getItemsBySearchCode', type='json', auth='user', methods=['POST'])
    @clv_api_endpoint
    def inventory_get_items_by_search_code(self, body: dict[str, Any], **query_params):
        """
        '/Inventory/getItemsBySearchCode' implementation. Used to search inventory Item by id, marking or barcode.
        @return: Dictionary as described in Inventory API swagger model
        """
        return self._inventory_impl.get_items_by_search_code(OdooEnvWrapper(http.request.env, version_info[0]),
                                                             body.get('searchMode'),
                                                             body.get('searchData'))

    @http.route('/Documents/getDocumentDescriptions', auth='user', type='json', methods=['POST'])
    @clv_api_endpoint
    def get_documents_desc(self, body: dict[str, Any], **query_params):
        """
        '/Documents/getDocumentDescriptions' endpoint implementation. Used to get list of document's headers
        @return: Dictionary as described in Inventory API swagger model
        """
        offset = TypeChecker.get_as_int(query_params.get('offset'))
        limit = TypeChecker.get_as_int(query_params.get('limit'))
        request_count = TypeChecker.get_as_bool(query_params.get('requestCount'))
        doc_type_name = TypeChecker.get_as_str(query_params.get('documentTypeName'))

        return self._documents_impl.get_descriptions(OdooEnvWrapper(http.request.env, version_info[0]),
                                                     doc_type_name,
                                                     offset,
                                                     limit,
                                                     request_count)

    @http.route('/Documents/getDocument', auth='user', type='json', methods=['POST'])
    @clv_api_endpoint
    def get_document(self, body: dict[str, Any], **query_params):
        """
        '/Documents/getDocument' endpoint implementation. Used to get full document (with expected and actual lines).
        @return: Dictionary as described in Inventory API swagger model
        """
        search_mode = TypeChecker.get_as_str(query_params.get('searchMode'))
        search_code = TypeChecker.get_as_str(query_params.get('searchCode'))
        doc_type_name = TypeChecker.get_as_str(query_params.get('documentTypeName'))

        return self._documents_impl.get_document(OdooEnvWrapper(http.request.env, version_info[0]),
                                                 search_mode,
                                                 search_code,
                                                 doc_type_name)

    @http.route('/Documents/setDocument', auth='user', type='json', methods=['POST'])
    @clv_api_endpoint
    def set_document(self, body: dict[str, Any], **query_params):
        """
        '/Documents/setDocument' endpoint implementation. Used to process finished document in odoo.
        """
        return self._documents_impl.set_document(OdooEnvWrapper(http.request.env, version_info[0]), body.get('document'), body.get('deviceInfo'))

    @http.route('/Tables/getTable', auth='user', type='json', methods=['POST'])
    @clv_api_endpoint
    def tables_get_items(self, body: dict[str, Any], **query_params):
        """
        '/Tables/getTable' endpoint implementation. Used to get table's rows page by query.
        @return: Dictionary as described in Inventory API swagger model
        """
        offset = TypeChecker.get_as_int(query_params.get('offset'))
        limit = TypeChecker.get_as_int(query_params.get('limit'))
        request_count = TypeChecker.get_as_bool(query_params.get('requestCount'))

        return self._tables_impl.get_rows(OdooEnvWrapper(http.request.env, version_info[0]),
                                          body.get('query'),
                                          body.get('deviceInfo'),
                                          offset,
                                          limit,
                                          request_count)
