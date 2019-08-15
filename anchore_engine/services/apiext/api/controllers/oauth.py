from connexion import request
from werkzeug.security import gen_salt
from werkzeug.datastructures import ImmutableMultiDict


from anchore_engine.apis.authorization import get_authorizer, make_response_error
from anchore_engine.apis import ApiRequestContextProxy
from anchore_engine.subsys import logger
from anchore_engine.db import session_scope, AccountTypes
from anchore_engine.db.entities.identity import OAuth2Client


authorizer = get_authorizer()


def get_oauth_token():
    """
    POST /oauth/token

    Requires the resource-owners credentials in the Authorization Header.

    This is a bit of a mix of the ResourceOwnerPasswordGrant flow and the ImplicitGrant flow since
    this function will populate the necessary fields to perform a password grant if the Authorization
    header is set and no content body is provided

    :return:
    """

    authz = ApiRequestContextProxy.get_service()._oauth_app

    if authz is None:
        # oauth is not enabled and not supported based on configuration
        return make_response_error(errmsg='Oauth not enabled in configuration', in_httpcode=500), 500

    # Add some default properties if not set in the request
    try:
        if request.content_length == 0 or not request.form:
            logger.debug('Handling converting empty body into form-based grant request')

            if not request.data and not request.form:
                setattr(request, 'form', ImmutableMultiDict([('username', request.authorization.username), ('password', request.authorization.password), ('grant_type', 'password'), ('client_id', 'anonymous')]))

        resp = authz.create_token_response()
        logger.debug('Token resp: {}'.format(resp))
        return resp
    except:
        logger.debug_exception('Error authenticating')
        raise


# @authorizer.requires_account(with_types=[AccountTypes.admin])
# def create_client(client_definition):
#     """
#     POST /create_client
#
#     :return:
#     """
#     with session_scope() as db:
#         # Use for handling form-urlencoded input instead of json
#         if not request.is_json:
#             logger.debug('Using non-json handler for defining the client')
#             client_definition = request.form.to_dict(flat=True)
#
#         logger.debug('Saving client from form: {}'.format(client_definition))
#
#         user = client_definition.get('user_id', ApiRequestContextProxy.identity().username)
#
#         if not client_definition.get('user_id'):
#             client_definition['user_id'] = user
#
#         client = OAuth2Client(**client_definition)
#         client.user_id = user
#         client.client_id = gen_salt(24)
#         if client.token_endpoint_auth_method == 'none':
#             client.client_secret = ''
#         else:
#             client.client_secret = gen_salt(48)
#
#         db.add(client)
#         return {'client_id': client.client_id, 'client_secret': client.client_secret}, 200
