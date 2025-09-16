import pytest
import MySQLdb
import flask_mysqldb

# Patch MySQL teardown to suppress OperationalError during test teardown
def safe_teardown(self, exception):
    try:
        orig_teardown(self, exception)
    except MySQLdb.OperationalError:
        pass

orig_teardown = flask_mysqldb.MySQL.teardown
flask_mysqldb.MySQL.teardown = safe_teardown

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# /api/v1/climate tests
def test_get_climate_data_valid(client):
    response = client.get('/api/v1/climate?location_id=1&page=1&per_page=5')
    assert response.status_code == 200
    assert 'data' in response.json
    assert 'meta' in response.json

def test_get_climate_data_invalid_location(client):
    response = client.get('/api/v1/climate?location_id=-1')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_climate_data_invalid_metric(client):
    response = client.get('/api/v1/climate?location_id=1&metric=invalid_metric')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_climate_data_invalid_quality(client):
    response = client.get('/api/v1/climate?location_id=1&quality_threshold=badquality')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_climate_data_invalid_date_format(client):
    response = client.get('/api/v1/climate?location_id=1&start_date=2025-99-99')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_climate_data_invalid_date_range(client):
    response = client.get('/api/v1/climate?location_id=1&start_date=2025-04-15&end_date=2025-01-01')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_climate_data_pagination(client):
    response = client.get('/api/v1/climate?location_id=1&page=2&per_page=2')
    assert response.status_code == 200
    assert 'data' in response.json
    assert 'meta' in response.json

# /api/v1/locations tests
def test_get_locations(client):
    response = client.get('/api/v1/locations')
    assert response.status_code == 200
    assert 'data' in response.json

# /api/v1/metrics tests
def test_get_metrics(client):
    response = client.get('/api/v1/metrics')
    assert response.status_code == 200
    assert 'data' in response.json

# /api/v1/summary tests
def test_get_summary_valid(client):
    response = client.get('/api/v1/summary?location_id=1')
    assert response.status_code == 200
    assert 'data' in response.json

def test_get_summary_invalid_location(client):
    response = client.get('/api/v1/summary?location_id=-1')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_summary_invalid_metric(client):
    response = client.get('/api/v1/summary?location_id=1&metric=invalid_metric')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_summary_invalid_quality(client):
    response = client.get('/api/v1/summary?location_id=1&quality_threshold=badquality')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_summary_invalid_date_format(client):
    response = client.get('/api/v1/summary?location_id=1&start_date=2025-99-99')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_summary_invalid_date_range(client):
    response = client.get('/api/v1/summary?location_id=1&start_date=2025-04-15&end_date=2025-01-01')
    assert response.status_code == 400
    assert 'error' in response.json

# /api/v1/trends tests
def test_get_trends_valid(client):
    response = client.get('/api/v1/trends?location_id=1')
    assert response.status_code == 200
    assert 'data' in response.json

def test_get_trends_invalid_location(client):
    response = client.get('/api/v1/trends?location_id=-1')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_trends_invalid_metric(client):
    response = client.get('/api/v1/trends?location_id=1&metric=invalid_metric')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_trends_invalid_quality(client):
    response = client.get('/api/v1/trends?location_id=1&quality_threshold=badquality')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_trends_invalid_date_format(client):
    response = client.get('/api/v1/trends?location_id=1&start_date=2025-99-99')
    assert response.status_code == 400
    assert 'error' in response.json

def test_get_trends_invalid_date_range(client):
    response = client.get('/api/v1/trends?location_id=1&start_date=2025-04-15&end_date=2025-01-01')
    assert response.status_code == 400
    assert 'error' in response.json