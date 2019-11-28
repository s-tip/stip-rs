import datetime
import pytz

V1_OBSERVABLE_TYPE_IPV4 = 'ipv4'
V1_OBSERVABLE_TYPE_DOMAIN = 'domain_name'
V1_OBSERVABLE_TYPE_MD5 = 'md5'
V1_OBSERVABLE_TYPE_SHA1 = 'sha1'
V1_OBSERVABLE_TYPE_SHA256 = 'sha256'
V1_OBSERVABLE_TYPE_SHA512 = 'sha512'
V1_OBSERVABLE_TYPE_URL = 'uri'

def get_observed_data_file_objects(type_,value):
    o_ = {}
    o_['type'] = 'file'
    hashes = {}
    if type_ == V1_OBSERVABLE_TYPE_MD5:
        hashes['MD5'] = value
    elif type_ == V1_OBSERVABLE_TYPE_SHA1:
        hashes['SHA-1'] = value
    elif type_ == V1_OBSERVABLE_TYPE_SHA256:
        hashes['SHA-256'] = value
    elif type_ == V1_OBSERVABLE_TYPE_SHA512:
        hashes['SHA-512'] = value
    else:
        hashes = None
    o_['hashes'] = hashes
    return o_

def get_observed_data_objects(type_,value):
    o_ = {}
    FILE_HASHES = [V1_OBSERVABLE_TYPE_MD5, V1_OBSERVABLE_TYPE_SHA1, V1_OBSERVABLE_TYPE_SHA256, V1_OBSERVABLE_TYPE_SHA512]

    if type_ == V1_OBSERVABLE_TYPE_IPV4:
        o_['type'] = 'ipv4-addr'
        o_['value'] = value
    elif type_ == V1_OBSERVABLE_TYPE_DOMAIN:
        o_['type'] = 'domain-name'
        o_['value'] = value
    elif type_ == V1_OBSERVABLE_TYPE_URL:
        o_['type'] = 'url'
        o_['value'] = value
    elif type_ in FILE_HASHES:
        o_ = get_observed_data_file_objects(type_,value)
    return o_

def get_time_str():
    n = datetime.datetime.now(pytz.utc)
    n_str = n.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return n_str

def _get_observed_data(cache):
    observed_data = {}
    observed_data['type'] = 'observed-data'
    now_date_str = get_time_str()
    if cache.first_observed is not None:
        observed_data['first_observed'] = cache.first_observed
    else:
        observed_data['first_observed'] = now_date_str
    if cache.first_observed is not None:
        observed_data['last_observed'] = cache.last_observed
    else:
        observed_data['last_observed'] = now_date_str
    observed_data['number_observed'] = cache.number_observed
    objects_ = {}
    object_ = get_observed_data_objects(cache.type,cache.value)
    objects_['0'] = object_
    observed_data['objects'] = objects_
    return observed_data
