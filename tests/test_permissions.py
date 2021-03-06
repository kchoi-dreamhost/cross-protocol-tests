from tools import get_config
from tools import assert_raises
from tools import create_valid_name
from tools import get_s3conn
from tools import get_swiftconn
from tools import get_s3user
from tools import get_swiftuser
from tools import get_unauthuser

import httplib

import unittest
from nose.tools import eq_ as eq


# USERNAME of the second (non-main) account
conf = get_config()
username = conf['username']


# Used for setup/teardown functions

def create_swift_container_with_acl(acl_headers):
    # Create Swift container
    swiftconn = get_swiftconn()
    container = create_valid_name()
    ### No support for creating container ACLs using PUT
    swiftconn.put_container(container)
    swiftconn.post_container(container, acl_headers)
    return container


def create_s3_bucket_with_acl(permission, username=None):
    # Create S3 bucket with specified ACL
    s3conn = get_s3conn()
    bucket = create_valid_name()
    s3conn.put_bucket(bucket)
    if username:
        s3conn.add_private_acl(permission, username, bucket)
        return bucket
    s3conn.add_public_acl(permission, bucket)
    return bucket


def delete_bucket(name):
    # Delete bucket (and objects inside it)
    s3conn = get_s3conn()
    bucket = s3conn.get_bucket(name)
    keys = bucket.list()
    for key in keys:
        key.delete()
    s3conn.delete_bucket(bucket)


# These classes are meant to be inherited with different
# setUp and tearDown cases - nosetests will not run them


class SwiftContainerReadPermissions(object):

    def test_read_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_read_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_read_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_read_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create private read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_read_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create public full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_read_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create private full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Read object using S3 (second user)
        s3user = get_s3user()
        eq(s3user.get_contents(bucket, objectname), text)
        # Read object using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.get_contents(bucket, objectname), text)


class SwiftContainerWritePermissions(object):

    def test_create_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object with second user
        swiftuser = get_swiftuser()
        swiftuser.put_object(bucket, objectname, text)
        # Check that it was created
        eq(swiftuser.get_contents(bucket, objectname), text)
        # Delete with Swift
        swiftconn = get_swiftconn()
        swiftconn.delete_object(bucket, objectname)
        # Check that it was deleted
        eq(swiftconn.list_objects(bucket), [])

        # Create Swift object with second user
        swiftuser.put_object(bucket, objectname, text)
        # Check that it was created
        eq(swiftuser.get_contents(bucket, objectname), text)
        # Delete with S3
        s3conn = get_s3conn()
        s3conn.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_create_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object with second user
        s3user = get_s3user()
        s3user.put_object(bucket, objectname, text)
        # Check that it was created
        eq(s3user.get_contents(bucket, objectname), text)
        # Delete with Swift
        swiftconn = get_swiftconn()
        swiftconn.delete_object(bucket, objectname)
        # Check that it was deleted
        eq(swiftconn.list_objects(bucket), [])

        # Create S3 object with second user
        s3user.put_object(bucket, objectname, text)
        # Check that it was created
        eq(s3user.get_contents(bucket, objectname), text)
        # Delete with S3
        s3conn = get_s3conn()
        s3conn.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(swiftconn.list_objects(bucket), [])

        # Create Swift object (main user)
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])


class S3BucketReadPermissions(object):
    def test_read_bucket_with_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])

    def test_read_bucket_with_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])

    def test_read_bucket_with_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])

    def test_read_bucket_with_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])

    def test_read_bucket_with_public_full_control_s3_object(self):
        # Create public read S3 object (main user)
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])

    def test_read_bucket_with_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # List objects using S3 (second user)
        s3user = get_s3user()
        eq(s3user.list_objects(bucket), [objectname])
        # List objects using Swift (second user)
        swiftuser = get_swiftuser()
        eq(swiftuser.list_objects(bucket), [objectname])


class S3BucketWritePermissions(object):
    def test_create_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object with second user
        swiftuser = get_swiftuser()
        swiftuser.put_object(bucket, objectname, text)
        # Check that it was created
        eq(swiftuser.get_contents(bucket, objectname), text)
        # Delete with Swift
        swiftconn = get_swiftconn()
        swiftconn.delete_object(bucket, objectname)

        # Create Swift object with second user
        swiftuser.put_object(bucket, objectname, text)
        # Check that it was created
        eq(swiftuser.get_contents(bucket, objectname), text)
        # Delete with S3
        s3conn = get_s3conn()
        s3conn.delete_object(bucket, objectname)

    def test_create_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object with second user
        s3user = get_s3user()
        s3user.put_object(bucket, objectname, text)
        # Check that it was created
        eq(s3user.get_contents(bucket, objectname), text)
        # Delete with Swift
        swiftconn = get_swiftconn()
        swiftconn.delete_object(bucket, objectname)

        # Create S3 object with second user
        s3user.put_object(bucket, objectname, text)
        # Check that it was created
        eq(s3user.get_contents(bucket, objectname), text)
        # Delete with S3
        s3conn = get_s3conn()
        s3conn.delete_object(bucket, objectname)

    def test_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(swiftconn.list_objects(bucket), [])

        # Create Swift object (main user)
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that container is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])


# These classes will test different permutations of object/bucket
# permissions and operations


class TestPublicReadSwiftContainer(unittest.TestCase,
                                   SwiftContainerReadPermissions):

    def setUp(self):
        # Create a Swift public read container
        self.bucket = create_swift_container_with_acl(
            {'x-container-read': '.r:*'})

    def tearDown(self):
        # Delete all buckets
        delete_bucket(self.bucket)

    def test_unauthuser_read_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Read object using unauthenticated user
        # QUESTIONABLE BEHAVIOR
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_public_acl('READ', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Re-add object ACL
        s3conn.add_public_acl('READ', bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create private read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Read object using unauthenticated user
        # QUESTIONABLE BEHAVIOR
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_private_acl('READ', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Re-add object ACL
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

    def test_unauthuser_read_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create public full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_public_acl('FULL_CONTROL', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Re-add object ACL
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create private full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Read object using unauthenticated user
        # QUESTIONABLE BEHAVIOR
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Re-add object ACL
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)


class TestPrivateReadSwiftContainer(unittest.TestCase,
                                    SwiftContainerReadPermissions):

    def setUp(self):
        # Create a Swift private read container
        self.bucket = create_swift_container_with_acl(
            {'x-container-read': username})

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_read_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Read object using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

    def test_unauthuser_read_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Read object using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

    def test_unauthuser_read_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        # QUESTIONABLE BEHAVIOR
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_public_acl('READ', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Re-add object ACL
        s3conn.add_public_acl('READ', bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create private read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Remove object ACL
        s3conn.remove_private_acl('READ', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Re-add object ACL
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

    def test_unauthuser_read_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create public full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        # QUESTIONABLE BEHAVIOR
        eq(unauthuser.get_contents(bucket, objectname), text)

        # Remove object ACL
        s3conn.remove_public_acl('FULL_CONTROL', bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Re-add object ACL
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        eq(unauthuser.get_contents(bucket, objectname), text)

    def test_unauthuser_read_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create private full control S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Remove object ACL
        s3conn.remove_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)

        # Re-add object ACL
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Remove container permissions
        swiftconn = get_swiftconn()
        swiftconn.post_container(bucket, {'x-container-read': ''})
        # Read object using unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.get_contents,
                      bucket, objectname)



class TestPublicWriteSwiftContainer(unittest.TestCase,
                                    SwiftContainerWritePermissions):

    def setUp(self):
        # Create a Swift public write container
        self.bucket = create_swift_container_with_acl(
            {'x-container-write': '.r:*'})

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create_objects(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        swiftconn = get_swiftconn()
        eq(swiftconn.list_objects(bucket), [objectname])
        # Delete with Swift
        swiftconn.delete_object(bucket, objectname)

        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        s3conn = get_s3conn()
        eq(s3conn.list_objects(bucket), [objectname])
        # Delete with S3
        s3conn.delete_object(bucket, objectname)

    def test_unauthuser_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    ## CHANGING THE S3 BUCKET PERMS (that is, making it have non-default perms)
    ## disables Swift public write.
    def test_unauthuser_create_objects_after_removing_default_perms(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Set read permissions using S3 (no more default S3)
        s3conn = get_s3conn()
        s3conn.add_public_acl('READ', bucket)
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        # Fails... QUESTIONABLE BEHAVIOR
        assert_raises(httplib.HTTPException, unauthuser.put_object,
                      bucket, objectname, text)

    ## Does changing the perms BACK to default re-enable swift public write?
    ## Nope, Swift public write is still disabled
    def test_unauthuser_create_objects_after_reseting_default_perms(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Set read permissions using S3 (no more default S3)
        s3conn = get_s3conn()
        s3conn.add_public_acl('READ', bucket)
        # Reset permissions using S3
        s3conn.remove_public_acl('READ', bucket)
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        # Fails: QUESTIONABLE BEHAVIOR
        assert_raises(httplib.HTTPException, unauthuser.put_object,
                      bucket, objectname, text)


class TestPrivateWriteSwiftContainer(unittest.TestCase,
                                     SwiftContainerWritePermissions):

    def setUp(self):
        # Create a Swift private write container
        self.bucket = create_swift_container_with_acl(
            {'x-container-write': username})

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create_objects(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.put_object,
                      bucket, objectname, text)

    def test_unauthuser_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_swiftconn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)


class TestPublicReadS3Bucket(unittest.TestCase, S3BucketReadPermissions):

    def setUp(self):
        # Create an S3 public read bucket
        self.bucket = create_s3_bucket_with_acl('READ')

    def tearDown(self):
        # Delete specified bucket
        delete_bucket(self.bucket)

    def test_unauth_read_bucket_with_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))

    def test_unauth_read_bucket_with_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))

    def test_unauth_read_bucket_with_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))

    def test_unauth_read_bucket_with_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))

    def test_unauth_read_bucket_with_public_full_control_s3_object(self):
        # Create public read S3 object (main user)
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))

    def test_unauth_read_bucket_with_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # List objects using unauthenticated user
        unauthuser = get_unauthuser()
        s3conn = get_s3conn()
        eq(unauthuser.list_objects(bucket),
           s3conn.compare_list_objects(bucket))


class TestPrivateReadS3Bucket(unittest.TestCase, S3BucketReadPermissions):

    def setUp(self):
        # Create an S3 private read bucket
        self.bucket = create_s3_bucket_with_acl('READ', username)

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauth_read_bucket_with_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)

    def test_unauth_read_bucket_with_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)

    def test_unauth_read_bucket_with_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)

    def test_unauth_read_bucket_with_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)

    def test_unauth_read_bucket_with_public_full_control_s3_object(self):
        # Create public read S3 object (main user)
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)

    def test_unauth_read_bucket_with_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create public read S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # List objects using unauthenticated user (should fail)
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.list_objects,
                      bucket)


class TestPublicWriteS3Bucket(unittest.TestCase, S3BucketWritePermissions):

    def setUp(self):
        # Create a Swift public write bucket
        self.bucket = create_s3_bucket_with_acl('WRITE')

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create_objects(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        swiftconn = get_swiftconn()
        eq(swiftconn.list_objects(bucket), [objectname])
        # Delete with Swift
        swiftconn.delete_object(bucket, objectname)

        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        s3conn = get_s3conn()
        eq(s3conn.list_objects(bucket), [objectname])
        # Delete with S3
        s3conn.delete_object(bucket, objectname)

    def test_unauthuser_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])


class TestPrivateWriteS3Bucket(unittest.TestCase, S3BucketWritePermissions):

    def setUp(self):
        # Create a S3 private write bucket
        self.bucket = create_s3_bucket_with_acl('WRITE', username)

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        assert_raises(httplib.HTTPException, unauthuser.put_object,
                      bucket, objectname, text)

    def test_unauthuser_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_public_read_s3_object(self):
        bucket = self.bucket
        objectname = 'public-read-s3-object'
        text = 'public read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('READ', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_private_read_s3_object(self):
        bucket = self.bucket
        objectname = 'private-read-s3-object'
        text = 'private read s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('READ', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_public_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'public-full-control-s3-object'
        text = 'public full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_public_acl('FULL_CONTROL', bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_private_full_control_s3_object(self):
        bucket = self.bucket
        objectname = 'private-full-control-s3-object'
        text = 'private full control s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        s3conn.add_private_acl('FULL_CONTROL', username, bucket, objectname)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # Delete should fail
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)


# The following classes test conflicted write permissions between
# S3 and Swift


class CrossBucketWritePermissions(object):
    def test_create_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object with second user
        swiftuser = get_swiftuser()
        swiftuser.put_object(bucket, objectname, text)
        # Check that it was created
        eq(swiftuser.get_contents(bucket, objectname), text)

    def test_create_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object with second user
        s3user = get_s3user()
        s3user.put_object(bucket, objectname, text)
        # Check that it was created
        eq(s3user.get_contents(bucket, objectname), text)

    def test_delete_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

        # Create Swift object (main user)
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_delete_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with Swift second user
        swiftuser = get_swiftuser()
        swiftuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

        # Create S3 object (main user)
        s3conn.put_object(bucket, objectname, text)
        # Delete object with S3 second user
        s3user = get_s3user()
        s3user.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])


class TestPrivateWriteSwiftPublicWriteS3(unittest.TestCase,
                                         CrossBucketWritePermissions):

    def setUp(self):
        # Create a Swift public write container
        self.bucket = create_swift_container_with_acl(
            {'x-container-write': username})
        s3conn = get_s3conn()
        # Change bucket permissions
        s3conn.add_public_acl('WRITE', self.bucket)

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'
        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        swiftconn = get_swiftconn()
        eq(swiftconn.list_objects(bucket), [objectname])
        # Delete with Swift
        swiftconn.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.put_object(bucket, objectname, text)
        # Check that it was created
        s3conn = get_s3conn()
        eq(s3conn.list_objects(bucket), [objectname])
        # Delete with S3
        s3conn.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])

    def test_unauthuser_delete_default_swift_object(self):
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(swiftconn.list_objects(bucket), [])

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        unauthuser.delete_object(bucket, objectname)
        # Check that bucket is empty
        eq(s3conn.list_objects(bucket), [])


class TestPrivateWriteS3PublicWriteSwift(unittest.TestCase,
                                         CrossBucketWritePermissions):
    # Right now, S3 permissions are overriding Swift permissions

    def setUp(self):
        # Create a Swift public write container
        self.bucket = create_swift_container_with_acl(
            {'x-container-write': '.r:*'})
        s3conn = get_s3conn()
        # Change bucket permission to private write
        s3conn.add_private_acl('WRITE', username, self.bucket)

    def tearDown(self):
        delete_bucket(self.bucket)

    def test_unauthuser_create(self):
        bucket = self.bucket
        objectname = 'default-object'
        text = 'default object'

        # Create object with unauthenticated user
        unauthuser = get_unauthuser()
        # QUESTIONABLE BEHAVIOR
        assert_raises(httplib.HTTPException, unauthuser.put_object,
                      bucket, objectname, text)

    def test_unauthuser_delete_default_swift_object(self):
        # Create Swift object (main user)
        bucket = self.bucket
        objectname = 'default-swift-object'
        text = 'default swift object'
        # Create Swift object (main user)
        swiftconn = get_swiftconn()
        swiftconn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # QUESTIONABLE BEHAVIOR
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)

    def test_unauthuser_delete_default_s3_object(self):
        bucket = self.bucket
        objectname = 'default-s3-object'
        text = 'default s3 object'
        # Create S3 object (main user)
        s3conn = get_s3conn()
        s3conn.put_object(bucket, objectname, text)
        # Delete object with unauthenticated user
        unauthuser = get_unauthuser()
        # QUESTIONABLE BEHAVIOR
        assert_raises(httplib.HTTPException, unauthuser.delete_object,
                      bucket, objectname)
