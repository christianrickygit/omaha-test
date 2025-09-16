# app.py - EcoVision: Climate Visualizer API
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_caching import Cache
from flasgger import Swagger
import os
from logger import logger
from utils.constants import QUALITY_VALUES, QUALITY_WEIGHTS
from utils.validators import is_valid_int, is_valid_date, is_valid_date_range
from utils.config import get_versioned_cache_key, DERIVED_VER_KEY, ALGO_VER_KEY, DERIVED_DATA_VERSION, ALGO_VERSION
from utils.helpers import clear_old_versioned_cache_keys
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



app = Flask(__name__)
CORS(app)
Swagger(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[]
)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'climate_data')
mysql = MySQL(app)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

def error_response(message, status=400):
    return jsonify({"error": message}), status

@app.route('/api/v1/climate', methods=['GET'])
def get_climate_data():
    """
    Get climate data records.
    ---
    parameters:
      - name: location_id
        in: query
        type: integer
        required: false
        description: Location ID (optional)
        example: 1
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Start date (YYYY-MM-DD, optional)
        example: "2025-01-01"
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: End date (YYYY-MM-DD, optional)
        example: "2025-04-15"
      - name: metric
        in: query
        type: string
        required: false
        description: Metric name (optional)
        example: "precipitation"
      - name: quality_threshold
        in: query
        type: string
        required: false
        description: Minimum quality value (optional)
        example: "good"
      - name: page
        in: query
        type: integer
        required: false
        description: Page number (optional)
        example: 1
      - name: per_page
        in: query
        type: integer
        required: false
        description: Results per page (optional)
        example: 5
    responses:
      200:
        description: Climate data response
        schema:
          type: object
          required:
            - data
            - meta
          properties:
            data:
              type: array
              items:
                type: object
                required:
                  - id
                  - location_id
                  - location_name
                  - latitude
                  - longitude
                  - date
                  - metric
                  - value
                  - unit
                  - quality
                properties:
                  id:
                    type: integer
                  location_id:
                    type: integer
                  location_name:
                    type: string
                  latitude:
                    type: number
                  longitude:
                    type: number
                  date:
                    type: string
                  metric:
                    type: string
                  value:
                    type: number
                  unit:
                    type: string
                  quality:
                    type: string
            meta:
              type: object
              required:
                - total_count
                - page
                - per_page
              properties:
                total_count:
                  type: integer
                page:
                  type: integer
                per_page:
                  type: integer
      400:
        description: Invalid request
        schema:
          type: object
          properties:
            error:
              type: string
        examples:
          application/json:
            error: "location_id must be a positive integer."
    """
    try:
        args = request.args
        location_id = args.get('location_id')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        metric = args.get('metric')
        quality_threshold = args.get('quality_threshold')
        page = args.get('page', 1)
        per_page = args.get('per_page', 50)

        # Validate params
        if location_id and not is_valid_int(location_id):
            return error_response("location_id must be a positive integer.", 400)
        if start_date and not is_valid_date(start_date):
            return error_response("start_date must be in YYYY-MM-DD format.", 400)
        if end_date and not is_valid_date(end_date):
            return error_response("end_date must be in YYYY-MM-DD format.", 400)
        if start_date and end_date and not is_valid_date_range(start_date, end_date):
            return error_response("end_date must be greater than or equal to start_date.", 400)
        if page and not is_valid_int(page):
            return error_response("page must be a positive integer.", 400)
        if per_page and not is_valid_int(per_page):
            return error_response("per_page must be a positive integer.", 400)
        if quality_threshold and quality_threshold.lower() not in [q.lower() for q in QUALITY_VALUES]:
            return error_response("Invalid quality_threshold value.", 400)
        if metric:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) FROM metrics WHERE LOWER(name) = %s", (metric.lower(),))
            if cur.fetchone()[0] == 0:
                cur.close()
                return error_response("Invalid metric name.", 400)
            cur.close()

        page = int(page)
        per_page = int(per_page)

        where_clauses = []
        params = []

        if location_id:
            where_clauses.append("c.location_id = %s")
            params.append(location_id)
        if start_date:
            where_clauses.append("c.date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("c.date <= %s")
            params.append(end_date)
        if metric:
            where_clauses.append("LOWER(m.name) = %s")
            params.append(metric.lower())
        if quality_threshold:
            # Case-insensitive comparison for quality
            threshold_index = [q.lower() for q in QUALITY_VALUES].index(quality_threshold.lower())
            allowed_qualities = [q for q in QUALITY_VALUES[threshold_index:]]
            where_clauses.append("LOWER(c.quality) IN (%s)" % ','.join(['%s'] * len(allowed_qualities)))
            params.extend([q.lower() for q in allowed_qualities])

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        offset = (page - 1) * per_page

        query = f"""
            SELECT
                c.id,
                c.location_id,
                l.name AS location_name,
                l.latitude,
                l.longitude,
                c.date,
                m.name AS metric,
                c.value,
                m.unit,
                c.quality
            FROM climate_data c
            JOIN locations l ON c.location_id = l.id
            JOIN metrics m ON c.metric_id = m.id
            {where_sql}
            ORDER BY c.date ASC
            LIMIT %s OFFSET %s
        """

        params.extend([per_page, offset])

        cur = mysql.connection.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        data = [
            {
                "id": row[0],
                "location_id": row[1],
                "location_name": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "date": row[5].strftime('%Y-%m-%d'),
                "metric": row[6],
                "value": row[7],
                "unit": row[8],
                "quality": row[9]
            }
            for row in rows
        ]

        count_query = f"""
            SELECT COUNT(*) FROM climate_data c
            JOIN locations l ON c.location_id = l.id
            JOIN metrics m ON c.metric_id = m.id
            {where_sql}
        """
        cur.execute(count_query, tuple(params[:-2]))
        total_count = cur.fetchone()[0]
        cur.close()

        logger.info(f"Fetched climate data for location_id={location_id}, metric={metric}, page={page}, per_page={per_page}, returned_ids={[d['id'] for d in data]}")

        return jsonify({
            "data": data,
            "meta": {
                "total_count": total_count,
                "page": page,
                "per_page": per_page
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching climate data for location_id={location_id}, metric={metric}, page={page}: {str(e)}")
        return error_response(f"Failed to fetch climate data: {str(e)}", 500)

@app.route('/api/v1/locations', methods=['GET'])
@cache.cached(timeout=0, key_prefix="locations")
def get_locations():
    """
    Get all locations.
    ---
    responses:
      200:
        description: List of locations
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
        examples:
          application/json:
            data:
              - id: 1
                name: "Irvine"
                country: "USA"
                latitude: 33.6846
                longitude: -117.8265
                region: "California"
              - id: 2
                name: "Tokyo"
                country: "Japan"
                latitude: 35.6762
                longitude: 139.6503
                region: "Kanto"
      400:
        description: Error
        schema:
          type: object
          properties:
            error:
              type: string
        examples:
          application/json:
            error: "Database error."
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, country, latitude, longitude FROM locations")
        rows = cur.fetchall()
        data = [
            {
                "id": row[0],
                "name": row[1],
                "country": row[2],
                "latitude": row[3],
                "longitude": row[4]
            }
            for row in rows
        ]
        cur.close()

        logger.info(f"Fetched locations, returned_ids={[d['id'] for d in data]}")

        return jsonify({"data": data}), 200
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        return error_response(f"Failed to fetch locations: {str(e)}", 500)

@app.route('/api/v1/metrics', methods=['GET'])
@cache.cached(timeout=0, key_prefix="metrics")
def get_metrics():
    """
    Get all metrics.
    ---
    responses:
      200:
        description: List of metrics
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
        examples:
          application/json:
            data:
              - id: 1
                name: "temperature"
                display_name: "Temperature"
                unit: "celsius"
                description: "Average daily temperature"
              - id: 2
                name: "precipitation"
                display_name: "Precipitation"
                unit: "mm"
                description: "Daily precipitation amount"
      400:
        description: Error
        schema:
          type: object
          properties:
            error:
              type: string
        examples:
          application/json:
            error: "Database error."
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, display_name, unit, description FROM metrics")
        rows = cur.fetchall()
        data = [
            {
                "id": row[0],
                "name": row[1],
                "display_name": row[2],
                "unit": row[3],
                "description": row[4]
            }
            for row in rows
        ]
        cur.close()

        logger.info(f"Fetched metrics, returned_ids={[d['id'] for d in data]}")

        return jsonify({"data": data}), 200
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        return error_response(f"Failed to fetch metrics: {str(e)}", 500)

@app.route('/api/v1/summary', methods=['GET'])
@limiter.limit("10 per minute")
def get_summary():
    """
    Get summary statistics for climate data.
    ---
    parameters:
      - name: location_id
        in: query
        type: integer
        required: false
        description: Location ID (optional)
        example: 1
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Start date (YYYY-MM-DD, optional)
        example: "2025-01-01"
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: End date (YYYY-MM-DD, optional)
        example: "2025-04-15"
      - name: metric
        in: query
        type: string
        required: false
        description: Metric name (optional)
        example: "precipitation"
      - name: quality_threshold
        in: query
        type: string
        required: false
        description: Minimum quality value (optional)
        example: "good"
    responses:
      200:
        description: Summary statistics
        schema:
          type: object
          properties:
            data:
              type: object
              additionalProperties:
                type: object
                properties:
                  min:
                    type: number
                  max:
                    type: number
                  avg:
                    type: number
                  weighted_avg:
                    type: number
                  unit:
                    type: string
                  quality_distribution:
                    type: object
                    additionalProperties:
                      type: number
        examples:
          application/json:
            data:
              temperature:
                min: -5.2
                max: 35.9
                avg: 15.7
                weighted_avg: 14.2
                unit: "celsius"
                quality_distribution:
                  excellent: 0.3
                  good: 0.5
                  questionable: 0.1
                  poor: 0.1
              precipitation:
                min: 0
                max: 120.5
                avg: 25.3
                unit: "mm"
      400:
        description: Invalid request
        schema:
          type: object
          properties:
            error:
              type: string
        examples:
          application/json:
            error: "end_date must be greater than or equal to start_date."
    """
    try:
        args = request.args
        cache_key = get_versioned_cache_key("summary", args)
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for summary: {cache_key}")
            return jsonify(cached), 200

        location_id = args.get('location_id')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        metric = args.get('metric')
        quality_threshold = args.get('quality_threshold')

        # Validate params
        if location_id and not is_valid_int(location_id):
            return error_response("location_id must be a positive integer.", 400)
        if start_date and not is_valid_date(start_date):
            return error_response("start_date must be in YYYY-MM-DD format.", 400)
        if end_date and not is_valid_date(end_date):
            return error_response("end_date must be in YYYY-MM-DD format.", 400)
        if start_date and end_date and not is_valid_date_range(start_date, end_date):
            return error_response("end_date must be greater than or equal to start_date.", 400)
        if quality_threshold and quality_threshold.lower() not in [q.lower() for q in QUALITY_VALUES]:
            return error_response("Invalid quality_threshold value.", 400)
        if metric:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) FROM metrics WHERE LOWER(name) = %s", (metric.lower(),))
            if cur.fetchone()[0] == 0:
                cur.close()
                return error_response("Invalid metric name.", 400)
            cur.close()

        where_clauses = []
        params = []

        if location_id:
            where_clauses.append("c.location_id = %s")
            params.append(location_id)
        if start_date:
            where_clauses.append("c.date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("c.date <= %s")
            params.append(end_date)
        if metric:
            where_clauses.append("LOWER(m.name) = %s")
            params.append(metric.lower())
        if quality_threshold:
            threshold_index = [q.lower() for q in QUALITY_VALUES].index(quality_threshold.lower())
            allowed_qualities = [q for q in QUALITY_VALUES[threshold_index:]]
            where_clauses.append("LOWER(c.quality) IN (%s)" % ','.join(['%s'] * len(allowed_qualities)))
            params.extend([q.lower() for q in allowed_qualities])

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        query = f"""
            SELECT
                m.name AS metric,
                m.unit,
                c.value,
                c.quality
            FROM climate_data c
            JOIN metrics m ON c.metric_id = m.id
            {where_sql}
        """

        cur = mysql.connection.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()

        metrics_summary = {}
        for row in rows:
            metric_name = row[0]
            unit = row[1]
            value = row[2]
            quality = row[3]
            weight = QUALITY_WEIGHTS.get(quality.lower(), 0.0)

            if metric_name not in metrics_summary:
                metrics_summary[metric_name] = {
                    "unit": unit,
                    "values": [],
                    "weighted_values": [],
                    "qualities": {}
                }
            metrics_summary[metric_name]["values"].append(value)
            metrics_summary[metric_name]["weighted_values"].append(value * weight)
            metrics_summary[metric_name]["qualities"][quality] = metrics_summary[metric_name]["qualities"].get(quality, 0) + 1

        summary_data = {}
        for metric_name, info in metrics_summary.items():
            values = info["values"]
            weighted_values = info["weighted_values"]
            total_weight = sum([QUALITY_WEIGHTS.get(q.lower(), 0.0) * count for q, count in info["qualities"].items()])
            weighted_avg = sum(weighted_values) / total_weight if total_weight > 0 else None

            metric_summary = {
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "avg": sum(values) / len(values) if values else None,
                "unit": info["unit"]
            }
            if weighted_avg is not None:
                metric_summary["weighted_avg"] = weighted_avg
            if info["qualities"]:
                # Optionally, normalize quality_distribution to fractions if you want
                total = sum(info["qualities"].values())
                metric_summary["quality_distribution"] = {
                    q: count / total for q, count in info["qualities"].items()
                }
            summary_data[metric_name] = metric_summary

        result = {"data": summary_data}
        cache.set(cache_key, result, timeout=600)
        logger.info(f"Cache set for summary: {cache_key}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching summary for location_id={location_id}, metric={metric}, quality_threshold={quality_threshold}: {str(e)}")
        return error_response(f"Failed to fetch summary: {str(e)}", 500)

@app.route('/api/v1/trends', methods=['GET'])
@limiter.limit("10 per minute")
def get_trends():
    """
    Get climate data trends.
    ---
    parameters:
      - name: location_id
        in: query
        type: integer
        required: false
        description: Location ID (optional)
        example: 1
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Start date (YYYY-MM-DD, optional)
        example: "2025-01-01"
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: End date (YYYY-MM-DD, optional)
        example: "2025-04-15"
      - name: metric
        in: query
        type: string
        required: false
        description: Metric name (optional)
        example: "precipitation"
      - name: quality_threshold
        in: query
        type: string
        required: false
        description: Minimum quality value (optional)
        example: "good"
    responses:
      200:
        description: Trends analysis
        schema:
          type: object
          properties:
            data:
              type: object
              additionalProperties:
                type: object
                properties:
                  trend:
                    type: object
                    properties:
                      direction:
                        type: string
                      rate:
                        type: number
                      unit:
                        type: string
                      confidence:
                        type: number
                  anomalies:
                    type: array
                    items:
                      type: object
                      properties:
                        date:
                          type: string
                        value:
                          type: number
                        deviation:
                          type: number
                        quality:
                          type: string
                  seasonality:
                    type: object
                    properties:
                      detected:
                        type: boolean
                      period:
                        type: string
                      confidence:
                        type: number
                      pattern:
                        type: object
                        additionalProperties:
                          type: object
                          properties:
                            avg:
                              type: number
                            trend:
                              type: string
        examples:
          application/json:
            data:
              temperature:
                trend:
                  direction: "increasing"
                  rate: 0.5
                  unit: "celsius/month"
                  confidence: 0.85
                anomalies:
                  - date: "2023-06-15"
                    value: 42.1
                    deviation: 2.5
                    quality: "excellent"
                seasonality:
                  detected: true
                  period: "yearly"
                  confidence: 0.92
                  pattern:
                    winter: { avg: 5.2, trend: "stable" }
                    spring: { avg: 15.7, trend: "increasing" }
                    summer: { avg: 25.3, trend: "increasing" }
                    fall: { avg: 18.1, trend: "stable" }
      400:
        description: Invalid request
        schema:
          type: object
          properties:
            error:
              type: string
        examples:
          application/json:
            error: "Invalid quality_threshold value."
    """
    location_id = None
    metric = None
    quality_threshold = None
    try:
        args = request.args
        cache_key = get_versioned_cache_key("trends", args)
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for trends: {cache_key}")
            return jsonify(cached), 200

        location_id = args.get('location_id')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        metric = args.get('metric')
        quality_threshold = args.get('quality_threshold')

        # Validate params
        if location_id and not is_valid_int(location_id):
            return error_response("location_id must be a positive integer.", 400)
        if start_date and not is_valid_date(start_date):
            return error_response("start_date must be in YYYY-MM-DD format.", 400)
        if end_date and not is_valid_date(end_date):
            return error_response("end_date must be in YYYY-MM-DD format.", 400)
        if start_date and end_date and not is_valid_date_range(start_date, end_date):
            return error_response("end_date must be greater than or equal to start_date.", 400)
        if quality_threshold and quality_threshold.lower() not in [q.lower() for q in QUALITY_VALUES]:
            return error_response("Invalid quality_threshold value.", 400)
        if metric:
            cur = mysql.connection.cursor()
            cur.execute("SELECT COUNT(*) FROM metrics WHERE LOWER(name) = %s", (metric.lower(),))
            if cur.fetchone()[0] == 0:
                cur.close()
                return error_response("Invalid metric name.", 400)
            cur.close()

        where_clauses = []
        params = []

        if location_id:
            where_clauses.append("c.location_id = %s")
            params.append(location_id)
        if start_date:
            where_clauses.append("c.date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("c.date <= %s")
            params.append(end_date)
        if metric:
            where_clauses.append("LOWER(m.name) = %s")
            params.append(metric.lower())
        if quality_threshold:
            threshold_index = [q.lower() for q in QUALITY_VALUES].index(quality_threshold.lower())
            allowed_qualities = [q for q in QUALITY_VALUES[threshold_index:]]
            where_clauses.append("LOWER(c.quality) IN (%s)" % ','.join(['%s'] * len(allowed_qualities)))
            params.extend([q.lower() for q in allowed_qualities])

        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql

        # --- Fetch metric units for all metrics ---
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, unit FROM metrics")
        metric_units = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()

        # --- Fetch climate data with quality ---
        query = f"""
            SELECT
                m.name AS metric,
                c.date,
                c.value,
                c.quality
            FROM climate_data c
            JOIN metrics m ON c.metric_id = m.id
            {where_sql}
            ORDER BY c.date ASC
        """

        cur = mysql.connection.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()

        metrics_data = {}
        for row in rows:
            metric_name = row[0]
            date = row[1]
            value = row[2]
            quality = row[3]
            if metric_name not in metrics_data:
                metrics_data[metric_name] = []
            metrics_data[metric_name].append((date, value, quality))

        trends_data = {}
        for metric_name, data_points in metrics_data.items():
            if len(data_points) < 2:
                trends_data[metric_name] = {
                    "trend": {
                        "direction": None,
                        "rate": None,
                        "unit": metric_units.get(metric_name, None),
                        "confidence": 0.0
                    },
                    "anomalies": [],
                    "seasonality": {
                        "detected": False,
                        "period": None,
                        "confidence": 0.0,
                        "pattern": {}
                    }
                }
                continue

            import numpy as np
            dates = np.array([dp[0].toordinal() for dp in data_points])
            values = np.array([dp[1] for dp in data_points])

            slope = float(np.polyfit(dates, values, 1)[0])
            trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            rate_of_change = float(slope)

            mean = float(np.mean(values))
            std = float(np.std(values))
            anomalies = [
                {
                    "date": data_points[i][0].strftime('%Y-%m-%d'),
                    "value": float(data_points[i][1]),
                    "deviation": float(abs(data_points[i][1] - mean)),
                    "quality": data_points[i][2]
                }
                for i in range(len(data_points))
                if abs(data_points[i][1] - mean) > 2 * std
            ]

            # Seasonality detection (group by season)
            season_map = {
                12: "winter", 1: "winter", 2: "winter",
                3: "spring", 4: "spring", 5: "spring",
                6: "summer", 7: "summer", 8: "summer",
                9: "fall", 10: "fall", 11: "fall"
            }
            season_groups = {"winter": [], "spring": [], "summer": [], "fall": []}
            for i, (date, value, quality) in enumerate(data_points):
                season = season_map[date.month]
                season_groups[season].append(value)
            pattern = {}
            for season, vals in season_groups.items():
                if vals:
                    avg = float(np.mean(vals))
                    trend = "stable"
                    if len(vals) > 1:
                        trend = "increasing" if vals[-1] > vals[0] else "decreasing" if vals[-1] < vals[0] else "stable"
                    pattern[season] = {"avg": avg, "trend": trend}
            detected = bool(any(len(vals) > 0 for vals in season_groups.values()))
            period = "yearly" if detected else None
            seasonality_confidence = float(min(1.0, sum(len(vals) for vals in season_groups.values()) / 30.0))

            trends_data[metric_name] = {
                "trend": {
                    "direction": trend_direction,
                    "rate": rate_of_change,
                    "unit": metric_units.get(metric_name, None),
                    "confidence": float(min(1.0, len(values) / 30.0))
                },
                "anomalies": anomalies,
                "seasonality": {
                    "detected": detected,
                    "period": period,
                    "confidence": seasonality_confidence,
                    "pattern": pattern
                }
            }

        result = {"data": trends_data}
        cache.set(cache_key, result, timeout=600)
        logger.info(f"Cache set for trends: {cache_key}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching trends for location_id={location_id}, metric={metric}, quality_threshold={quality_threshold}: {str(e)}")
        return error_response(f"Failed to fetch trends: {str(e)}", 500)

if __name__ == '__main__':
    clear_old_versioned_cache_keys(cache)
    app.run(host="0.0.0.0", port=5001, debug=True)
