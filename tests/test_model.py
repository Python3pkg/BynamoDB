from _pytest.python import raises, fixture
from boto.dynamodb2.types import STRING
from boto.dynamodb2.layer1 import DynamoDBConnection
from bynamodb.exceptions import NullAttributeException
from bynamodb.filter_expression import GT

from bynamodb.model import Attribute, Model, GlobalAllIndex, AllIndex


@fixture
def test_model():
    class TestModel(Model):
        hash_key_attr = Attribute(STRING, hash_key=True)
        range_key_attr = Attribute(STRING, range_key=True)
        attr_1 = Attribute(STRING)
    return TestModel


def test_table_attr_name(test_model):
    assert test_model.hash_key_attr.attr_name == 'hash_key_attr'
    assert test_model.range_key_attr.attr_name == 'range_key_attr'
    assert test_model.attr_1.attr_name == 'attr_1'


def test_create_table(test_model):
    test_model.create_table()
    table_description = DynamoDBConnection().describe_table(test_model.get_table_name())[u'Table']
    expected_key_name = {
        'HASH': 'hash_key_attr',
        'RANGE': 'range_key_attr'
    }
    for key in table_description[u'KeySchema']:
        assert expected_key_name[key[u'KeyType']] == key[u'AttributeName']


@fixture
def fx_table_with_global_index():
    class TestModel(Model):
        attr_1 = Attribute(STRING, hash_key=True)
        attr_2 = Attribute(STRING)

        class TestIndex(GlobalAllIndex):
            read_throughput = 5
            write_throughput = 5

            hash_key = 'attr_2'
            range_key = 'attr_1'

    return TestModel


def test_create_table_with_global_index(fx_table_with_global_index):
    fx_table_with_global_index.create_table()
    table_description = DynamoDBConnection().describe_table(
        fx_table_with_global_index.get_table_name()
    )['Table']
    global_indexes = table_description['GlobalSecondaryIndexes']
    assert len(global_indexes) == 1
    global_index = global_indexes[0]
    assert global_index['IndexName'] == 'TestIndex'
    expected_key_name = {
        'HASH': 'attr_2',
        'RANGE': 'attr_1'
    }
    for key in global_index['KeySchema']:
        assert expected_key_name[key['KeyType']] == key['AttributeName']


def test_get_item(test_model):
    test_model.create_table()

    hash_key_value = 'Hash Key Value'
    range_key_value = 'Range Key Value'
    attr1_value = 'Attribute1 Value'
    test_model.put_item({
        'hash_key_attr': hash_key_value,
        'range_key_attr': range_key_value,
        'attr_1': attr1_value
    })

    item = test_model.get_item(hash_key_value, range_key_value)
    assert item.hash_key_attr == hash_key_value
    assert item.range_key_attr == range_key_value
    assert item.attr_1 == attr1_value


@fixture
def fx_table_with_local_index():
    class TestModel(Model):
        attr_1 = Attribute(STRING, hash_key=True)
        attr_2 = Attribute(STRING, range_key=True)
        attr_3 = Attribute(STRING)

        class TestIndex(AllIndex):
            hash_key = 'attr_1'
            range_key = 'attr_3'

    return TestModel


def test_create_table_with_local_index(fx_table_with_local_index):
    fx_table_with_local_index.create_table()
    table_description = DynamoDBConnection().describe_table(
        fx_table_with_local_index.get_table_name()
    )['Table']
    local_indexes = table_description['LocalSecondaryIndexes']
    assert len(local_indexes) == 1
    local_index = local_indexes[0]
    assert local_index['IndexName'] == 'TestIndex'
    expected_key_name = {
        'HASH': 'attr_1',
        'RANGE': 'attr_3'
    }
    for key in local_index['KeySchema']:
        assert expected_key_name[key['KeyType']] == key['AttributeName']


def test_put_item(test_model):
    test_model.create_table()
    hash_key_value = 'Hash Key Value'
    range_key_value = 'Range Key Value'
    attr1_value = 'Attribute1 Value'
    attrs = {
        'hash_key_attr': hash_key_value,
        'range_key_attr': range_key_value,
        'attr_1': attr1_value
    }
    test_model.put_item(attrs)

    item = test_model.get_item(hash_key=hash_key_value, range_key=range_key_value)
    assert item.hash_key_attr == hash_key_value
    assert item.range_key_attr == range_key_value
    assert item.attr_1 == attr1_value


def test_put_item_with_missing_attr(test_model):
    test_model.create_table()
    attrs = {
        'hash_key_attr': 'hash_key',
        'range_key_attr': 'range_key'
    }
    with raises(NullAttributeException):
        test_model.put_item(attrs)


def test_save_item_with_missing_attr(test_model):
    test_model.create_table()
    item = test_model({
        'hash_key_attr': 'hash_key',
        'range_key_attr': 'range_key'
    })
    with raises(NullAttributeException):
        item.save()


@fixture
def model_with_nullable_attr():
    class TestModelWithNullable(Model):
        hash_key = Attribute(STRING, hash_key=True)
        attr = Attribute(STRING, null=True)
    return TestModelWithNullable


def test_save_item_nullable_attr_emptied(model_with_nullable_attr):
    model_with_nullable_attr.create_table()
    hash_key_value = 'value'
    model_with_nullable_attr({
        'hash_key': hash_key_value
    }).save()
    item = model_with_nullable_attr.get_item(hash_key_value)
    assert item.hash_key == hash_key_value


@fixture
def fx_query_test_model():
    class QueryTestModel(Model):
        published_at = Attribute(STRING, hash_key=True)
        title = Attribute(STRING, range_key=True)
    QueryTestModel.create_table()
    return QueryTestModel


@fixture
def fx_query_test_items(fx_query_test_model):
    for i, ch in enumerate(['a', 'a', 'b', 'c', 'd', 'e']):
        fx_query_test_model.put_item({'published_at': ch * 5, 'title': str(i) * 5})


def test_scan(fx_query_test_model, fx_query_test_items):
    result = fx_query_test_model.scan()
    assert len(result.items) == 6
    assert all(type(item) == fx_query_test_model for item in result)


def test_scan_with_filter_operator(fx_query_test_model, fx_query_test_items):
    gt = GT('published_at', 'bbbbb')
    result = fx_query_test_model.scan(filter_builder=gt)
    assert len(result.items) == 3
    assert all([item.published_at > 'bbbbb' for item in result])


def test_query(fx_query_test_model, fx_query_test_items):
    result = fx_query_test_model.query({'published_at__eq': 'aaaaa'})
    assert len(result.items) == 2
    assert all(item.published_at == 'aaaaa' for item in result)