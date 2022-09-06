import datetime
import mongoengine as me
from ctirs.core.mongo.documents import Communities


def get_modified_from_object(object_):
    if 'modified' in object_:
        modified = object_['modified']
    elif 'created' in object_:
        modified = object_['created']
    else:
        from core.response import get_taxii_date_str
        modified = get_taxii_date_str(datetime.datetime.utcnow())
    return modified


class StixManifest(me.Document):
    added = me.DateTimeField(default=datetime.datetime.utcnow, required=True)
    object_type = me.StringField(required=True)
    spec_version = me.StringField(default='2.1')
    object_id = me.StringField(required=True)
    versions = me.ListField(me.StringField())
    media_types = me.ListField(me.StringField())
    deleted_versions = me.ListField(me.StringField(), default=[])
    deleted = me.BooleanField(required=True, default=False)
    stix_files = me.ListField()
    community = me.ReferenceField(Communities, required=True)

    meta = {
        'db_alias': 'taxii21_alias'
    }

    def _get_version_elem(self, stix_file, modified):
        return [stix_file.id, modified]

    def _is_exist_version(self, modified):
        for tup in self.stix_files:
            _, version = tup
            if version == modified:
                return True
        return False

    def append_stix_file(self, stix_file, modified):
        if modified not in self.versions:
            self.versions.append(modified)
        version_elem = self._get_version_elem(stix_file, modified)
        if version_elem not in self.stix_files:
            self.stix_files.append(version_elem)
        self.deleted = False
        self.community = stix_file.input_community
        self.save()
        return

    def delete(self, stix_file, modified):
        version_elem = self._get_version_elem(stix_file, modified)
        if version_elem in self.stix_files:
            self.stix_files.remove(version_elem)
        if not self._is_exist_version(modified):
            if modified in self.versions:
                self.versions.remove(modified)
            if modified not in self.deleted_versions:
                self.deleted_versions.append(modified)
        if len(self.versions) == 0:
            self.deleted = True
        else:
            self.deleted = False
        self.save()
        return self.deleted

    @staticmethod
    def update_or_create(stix_object, media_types, stix_file):
        try:
            manifest = StixManifest.objects.get(object_id=stix_object.object_id)
        except me.DoesNotExist:
            manifest = StixManifest()
            manifest.media_types = media_types
            manifest.object_type = stix_object.object_type
            manifest.spec_version = stix_object.spec_version
            manifest.object_id = stix_object.object_id
            manifest.deleted_versions = []
        manifest.append_stix_file(stix_file, stix_object.modified)
        return manifest


class StixObject(me.Document):
    object_value = me.DictField(required=True)
    added = me.DateTimeField(default=datetime.datetime.utcnow, required=True)
    object_type = me.StringField(requierd=True)
    spec_version = me.StringField(default='2.1')
    object_id = me.StringField(required=True)
    created = me.StringField(reqruied=True)
    modified = me.StringField(reqruied=True)
    revoked = me.BooleanField(default=False)
    object_marking_refs = me.ListField(me.StringField())
    created_by_ref = me.StringField()
    labels = me.ListField(me.StringField())
    source_ref = me.StringField()
    target_ref = me.StringField()
    relationship_type = me.StringField()
    manifest = me.ReferenceField(StixManifest)
    deleted = me.BooleanField(default=False)
    community = me.ReferenceField(Communities, required=True)

    meta = {
        'db_alias': 'taxii21_alias'
    }

    def append_stix_file(self, stix_file):
        self.manifest.append_stix_file(stix_file, self.modified)
        self.deleted = False
        self.save()
        return

    def delete(self, stix_file):
        self.deleted = self.manifest.delete(stix_file, self.modified)
        self.save()
        return

    @staticmethod
    def create(stix_object, media_types, stix_file):
        so = StixObject()
        so.object_value = stix_object
        so.object_type = stix_object['type']
        if 'spec_version' in stix_object:
            so.spec_version = stix_object['spec_version']
        else:
            so.spec_version = '2.1'
        so.object_id = stix_object['id']
        so.created = stix_object['created']
        so.modified = get_modified_from_object(stix_object)
        if 'revoked' in stix_object:
            so.revoked = stix_object['revoked']
        else:
            so.revoked = False
        if 'object_marking_refs' in stix_object:
            so.object_marking_refs = stix_object['object_marking_refs']
        else:
            so.object_marking_refs = []
        if 'created_by_ref' in stix_object:
            so.created_by_ref = stix_object['created_by_ref']
        else:
            so.created_by_ref = ''
        if 'labels' in stix_object:
            so.labels = stix_object['labels']
        else:
            so.labels = []
        if 'source_ref' in stix_object:
            so.source_ref = stix_object['source_ref']
        if 'target_ref' in stix_object:
            so.target_ref = stix_object['target_ref']
        if 'relationship_type' in stix_object:
            so.relationship_type = stix_object['relationship_type']
        so.deleted = False
        so.community = stix_file.input_community
        so.save()
        manifest = StixManifest.update_or_create(so, media_types, stix_file)
        so.manifest = manifest
        so.save()
        return so
