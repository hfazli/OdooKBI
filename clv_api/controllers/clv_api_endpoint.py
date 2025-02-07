import json
from typing import Any
from urllib import parse

from odoo.http import request, Response
from odoo.release import version_info
from odoo.tools import json_default


def clv_api_endpoint(func):
    """
    The decorator function used to customize processing of http-requests in Warehouse 15 ('clv_api') module.
    """

    def wrapper(*args, **kwargs):
        _set_response_preprocessor(request, _preprocess_response)

        body = _extract_json_body(request)
        query_params = _extract_query_params(request)

        new_args = args + (body,)
        return func(*new_args, **query_params)

    return wrapper


def _extract_json_body(request) -> dict[str, Any]:
    """
    Extracts json body from http-request object as python dictionary.
    """
    odoo_version = version_info[0]
    if odoo_version >= 16:
        return request.dispatcher.jsonrequest or {}
    elif odoo_version >= 13:
        return request.jsonrequest or {}
    else:
        raise RuntimeError("Function \'extract_json_body\' is not implemented for Odoo v{} in the 'clv_api' module. Contact the Cleverence developers for details.".format(odoo_version))


def _extract_query_params(request) -> dict[str, Any]:
    """
    Extracts query parameters from http-request object as python dictionary.
    """
    return dict(parse.parse_qsl(parse.urlsplit(request.httprequest.url).query)) or {}


def _set_response_preprocessor(request, preprocessor) -> None:
    """
    Sets custom preprocessor of http-response to http-request object.
    """
    odoo_version = version_info[0]
    if odoo_version >= 16:
        request.dispatcher._response = preprocessor.__get__(request, type(request))
    elif odoo_version >= 13:
        request._json_response = preprocessor.__get__(request, type(request))
    else:
        raise RuntimeError("Function 'set_response_preprocessor' is not implemented for Odoo v{} in the 'clv_api' module. Contact the Cleverence developers for details.".format(odoo_version))


def _preprocess_response(request, result=None, error=None):
    """
    Preprocesses body of Odoo http-response object.
    Removes json-rpc headers
    @param result: returning result object
    @param error: error object
    @return:
    """
    default_http_code = 200
    response = {}
    if error is not None:
        response = {'error': _extract_pretty_error_test(error)}
        default_http_code = 500
    if result is not None:
        response = result
    mime = 'application/json'
    body = json.dumps(response, default=json_default)
    return Response(
        body, status=error and error.pop('http_status', default_http_code) or default_http_code,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )


def _extract_pretty_error_test(error) -> str:
    """
    Extracts error message from Odoo error object.
    @param error: Error object (dictionary)
    @return:
    """
    result = ''
    if 'message' in error:
        result = result + error['message']
    if 'data' in error and 'message' in error['data']:
        result = result + '. ' + error['data']['message']
    if len(result) == 0:
        result = 'ODOO server error. check odoo.log file for details.'
    return result
