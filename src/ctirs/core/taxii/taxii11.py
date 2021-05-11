import os
import pytz
import traceback
import datetime
import tempfile
import libtaxii
import libtaxii.clients as clients
import libtaxii.messages_11 as tm11
import libtaxii.constants as const


def _get_auth_credentials_dict(taxii_client):
    auth_credentials_dict = {}
    auth_credentials_dict['username'] = taxii_client._username
    auth_credentials_dict['password'] = taxii_client._password
    if taxii_client._auth_type == clients.HttpClient.AUTH_CERT_BASIC:
        _, cert_file = tempfile.mkstemp()
        with open(cert_file, 'w', encoding='utf-8') as fp:
            fp.write(taxii_client._cert_file)
        _, key_file = tempfile.mkstemp()
        with open(key_file, 'w', encoding='utf-8') as fp:
            fp.write(taxii_client._key_file)
        auth_credentials_dict['cert_file'] = cert_file
        auth_credentials_dict['key_file'] = key_file
    return auth_credentials_dict


def poll_11(taxii_client):
    auth_credentials_dict = _get_auth_credentials_dict(taxii_client)
    taxii_client._client.set_auth_credentials(auth_credentials_dict)

    try:
        poll_parameters = tm11.PollParameters()
        poll_request = tm11.PollRequest(
            message_id=tm11.generate_message_id(),
            collection_name=taxii_client._collection_name,
            exclusive_begin_timestamp_label=taxii_client._start,
            inclusive_end_timestamp_label=taxii_client._end,
            poll_parameters=poll_parameters,
        )
        last_requested = datetime.datetime.now(pytz.utc)

        http_resp = taxii_client._client.call_taxii_service2(
            taxii_client._address,
            taxii_client._path,
            const.VID_TAXII_XML_11,
            poll_request.to_xml(),
            port=taxii_client._port)

        taxii_message = libtaxii.get_message_from_http_response(
            http_resp,
            poll_request.message_id)
        try:
            if taxii_message.content_blocks is None:
                return 0
        except AttributeError:
            return 0

        count = 0
        for cb in taxii_message.content_blocks:
            _, stix_file_path = tempfile.mkstemp(suffix='.xml')
            with open(stix_file_path, 'wb+') as fp:
                fp.write(cb.content)
            try:
                from ctirs.core.stix.regist import regist
                if taxii_client._community is not None:
                    regist(
                        stix_file_path,
                        taxii_client._community,
                        taxii_client._via)
                count += 1
            except BaseException as e:
                traceback.print_exc()
                raise e

        taxii_client._taxii.last_requested = last_requested
        taxii_client._taxii.save()
        return count
    finally:
        if 'cert_file' in auth_credentials_dict:
            try:
                os.remove(auth_credentials_dict['cert_file'])
            except Exception:
                pass
        if 'key_file' in auth_credentials_dict:
            try:
                os.remove(auth_credentials_dict['key_file'])
            except Exception:
                pass


def push_11(taxii_client, stix_file_doc):
    if stix_file_doc.version.startswith('2'):
        try:
            content = stix_file_doc.get_slide_12()
        except Exception as e:
            traceback.print_exc()
            raise e
    else:
        with open(stix_file_doc.origin_path, 'r', encoding='utf-8') as fp:
            content = fp.read()

    auth_credentials_dict = _get_auth_credentials_dict(taxii_client)
    taxii_client._client.set_auth_credentials(auth_credentials_dict)
    try:
        subscription_information = tm11.SubscriptionInformation(
            collection_name=taxii_client._collection_name,
            subscription_id='subscripiton_id')
        cb = tm11.ContentBlock(const.CB_STIX_XML_11, content)
        im = tm11.InboxMessage(
            message_id=tm11.generate_message_id(),
            destination_collection_names=[taxii_client._collection_name],
            subscription_information=subscription_information,
            content_blocks=[cb])

        http_resp = taxii_client._client.call_taxii_service2(
            taxii_client._address,
            taxii_client._path,
            const.VID_TAXII_XML_11,
            im.to_xml(),
            port=taxii_client._port)
        taxii_message = libtaxii.get_message_from_http_response(
            http_resp,
            im.message_id)
        if taxii_message.status_type != 'SUCCESS':
            raise Exception('taxii_message.status_type is not SUCCESS')
        return 'Success !!'
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        if 'cert_file' in auth_credentials_dict:
            try:
                os.remove(auth_credentials_dict['cert_file'])
            except Exception:
                pass
        if 'key_file' in auth_credentials_dict:
            try:
                os.remove(auth_credentials_dict['key_file'])
            except Exception:
                pass
