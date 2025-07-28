"""
Utility functions for Apple Watch Health Data MCP Server
"""
from typing import Any, Dict, List


def build_elasticsearch_query(start_date: str, end_date: str, device: str, aggregation: str) -> Dict[str, Any]:
    """
    Build Elasticsearch query based on provided parameters.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        device: Device name to filter by
        aggregation: Aggregation interval (hourly, daily, weekly, monthly)
    
    Returns:
        Dictionary containing the Elasticsearch query
    """
    query = {"query": {"match_all": {}}}
    filters = []
    
    # Date filters
    date_ranges = []
    if start_date:
        date_ranges.append({"gte": start_date})
    if end_date:
        date_ranges.append({"lte": end_date})
    
    if date_ranges:
        filters.append({
            "range": {
                "day": {**{k: v for d in date_ranges for k, v in d.items()}}
            }
        })
    
    # Device filter
    if device:
        filters.append({
            "wildcard": {
                "device": f"*{device}*"
            }
        })
    
    if filters:
        query["query"] = {"bool": {"must": filters}}
    
    # Aggregation handling
    if aggregation:
        interval_mapping = {
            "hourly": "1h",
            "daily": "1d", 
            "weekly": "1w",
            "monthly": "1M"
        }
        interval = interval_mapping.get(aggregation, "1d")
        date_field = "startDate" if aggregation == "hourly" else "day"
        
        query["aggs"] = {
            "time_series": {
                "date_histogram": {
                    "field": date_field,
                    "calendar_interval": interval,
                    "min_doc_count": 0
                },
                "aggs": {
                    "total_steps": {"sum": {"field": "value"}},
                    "avg_steps": {"avg": {"field": "value"}},
                    "max_steps": {"max": {"field": "value"}},
                    "min_steps": {"min": {"field": "value"}}
                }
            }
        }
        query["size"] = 0
    else:
        query.update({
            "sort": [{"startDate": "desc"}],
            "size": 10
        })
    
    return query


def process_aggregated_results(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process aggregated Elasticsearch results.
    
    Args:
        data: Raw Elasticsearch response data
    
    Returns:
        List of processed aggregated results
    """
    results = []
    if "aggregations" in data and "time_series" in data["aggregations"]:
        for bucket in data["aggregations"]["time_series"]["buckets"]:
            results.append({
                "date": bucket["key_as_string"],
                "total_steps": bucket["total_steps"]["value"],
                "average_steps": bucket["avg_steps"]["value"],
                "max_steps": bucket["max_steps"]["value"],
                "min_steps": bucket["min_steps"]["value"],
                "records": bucket["doc_count"]
            })
    return results


def process_raw_results(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process raw Elasticsearch results.
    
    Args:
        data: Raw Elasticsearch response data
    
    Returns:
        List of processed raw results
    """
    results = []
    for hit in data["hits"]["hits"]:
        source = hit["_source"]
        results.append({
            "startDate": source.get("startDate"),
            "endDate": source.get("endDate"),
            "day": source.get("day"),
            "dayOfWeek": source.get("dayOfWeek"),
            "hour": source.get("hour"),
            "value": source.get("value"),
            "device": source.get("device"),
            "sourceName": source.get("sourceName")
        })
    return results