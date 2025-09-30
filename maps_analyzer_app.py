#!/usr/bin/env python3
"""
Google Maps Campus Area Analyzer - Web Interface

A web-based tool using Google Maps with drawing overlays for manually 
designating school campus areas with high accuracy.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from flask import Flask, render_template, request, jsonify
from shapely.geometry import Polygon
import pyproj
from functools import partial

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

@dataclass
class AreaDesignation:
    """Represents a manually drawn area with its type"""
    coordinates: List[Tuple[float, float]]  # List of (lat, lng) coordinates
    area_type: str  # 'boundary', 'building', 'field', 'parking', 'other'
    area_m2: float = 0.0
    area_acres: float = 0.0
    area_sqft: float = 0.0
    floors: int = 1  # Number of floors (for buildings)
    total_floor_area_sqft: float = 0.0  # Total square footage including floors

@dataclass
class CampusAnalysis:
    """Complete analysis of a campus"""
    address: str
    lat: float
    lng: float
    areas: List[AreaDesignation]
    total_boundary_acres: float = 0.0
    building_acres: float = 0.0
    field_acres: float = 0.0
    parking_acres: float = 0.0
    other_acres: float = 0.0
    notes: str = ""

def geocode_address(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Geocode address to lat/lng using Google Maps API"""
    import requests
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    try:
        r = requests.get(url, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

def calculate_polygon_area_m2(coordinates: List[Tuple[float, float]]) -> float:
    """Calculate area of polygon in square meters using proper projection"""
    if len(coordinates) < 3:
        return 0.0
    
    # Use UTM projection for accurate area calculation
    # Get the center point to determine appropriate UTM zone
    center_lat = sum(coord[0] for coord in coordinates) / len(coordinates)
    center_lng = sum(coord[1] for coord in coordinates) / len(coordinates)
    
    # Determine UTM zone
    utm_zone = int((center_lng + 180) / 6) + 1
    utm_crs = f"EPSG:{32600 + utm_zone if center_lat >= 0 else 32700 + utm_zone}"
    
    # Create transformer
    transformer = pyproj.Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
    
    # Transform coordinates to UTM
    utm_coords = [transformer.transform(lng, lat) for lat, lng in coordinates]
    
    # Create polygon and calculate area
    polygon = Polygon(utm_coords)
    return polygon.area

def load_addresses_from_csv(csv_path: str) -> List[str]:
    """Load addresses from CSV file"""
    try:
        df = pd.read_csv(csv_path)
        if 'address' in df.columns:
            return df['address'].tolist()
        else:
            return []
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

# Global storage for current analysis (in production, use a database)
current_analyses: Dict[str, CampusAnalysis] = {}

@app.route('/')
def index():
    """Main page"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    return render_template('maps_index.html', google_maps_api_key=api_key)

@app.route('/api/load_addresses')
def load_addresses():
    """Load addresses from the CSV file"""
    csv_path = os.path.join(os.path.dirname(__file__), 'addresses.csv')
    addresses = load_addresses_from_csv(csv_path)
    return jsonify({'addresses': addresses})

@app.route('/api/geocode_address', methods=['POST'])
def geocode_address_api():
    """Geocode an address"""
    data = request.json
    address = data.get('address', '')
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return jsonify({'error': 'Google Maps API key not configured'}), 400
    
    coords = geocode_address(address, api_key)
    if not coords:
        return jsonify({'error': 'Address not found'}), 404
    
    lat, lng = coords
    
    # Create or get existing analysis
    if address not in current_analyses:
        current_analyses[address] = CampusAnalysis(
            address=address,
            lat=lat,
            lng=lng,
            areas=[]
        )
    
    return jsonify({
        'success': True,
        'address': address,
        'lat': lat,
        'lng': lng
    })

@app.route('/api/save_area', methods=['POST'])
def save_area():
    """Save a manually drawn area"""
    data = request.json
    address = data.get('address', '')
    coordinates = data.get('coordinates', [])  # List of [lat, lng] pairs
    area_type = data.get('area_type', 'other')
    
    if address not in current_analyses:
        return jsonify({'error': 'No analysis found for this address'}), 404
    
    analysis = current_analyses[address]
    
    # Calculate area
    area_m2 = calculate_polygon_area_m2(coordinates)
    area_acres = area_m2 / 4046.8564224
    area_sqft = area_m2 * 10.7639  # Convert m² to ft²
    
    # For buildings, default to 1 floor initially
    floors = 1 if area_type == 'building' else 1
    total_floor_area_sqft = area_sqft * floors if area_type == 'building' else area_sqft
    
    # Create area designation
    area_designation = AreaDesignation(
        coordinates=coordinates,
        area_type=area_type,
        area_m2=area_m2,
        area_acres=area_acres,
        area_sqft=area_sqft,
        floors=floors,
        total_floor_area_sqft=total_floor_area_sqft
    )
    
    # Add to analysis
    analysis.areas.append(area_designation)
    
    # Recalculate totals
    update_analysis_totals(analysis)
    
    return jsonify({
        'success': True,
        'area_m2': area_m2,
        'area_acres': area_acres,
        'area_sqft': area_sqft,
        'floors': floors,
        'total_floor_area_sqft': total_floor_area_sqft,
        'totals': get_analysis_totals(analysis)
    })

@app.route('/api/update_area', methods=['POST'])
def update_area():
    """Update coordinates of an existing area"""
    data = request.json
    address = data.get('address', '')
    area_index = data.get('area_index', -1)
    coordinates = data.get('coordinates', [])
    area_type = data.get('area_type', 'other')
    
    if address not in current_analyses:
        return jsonify({'error': 'No analysis found for this address'}), 404
    
    analysis = current_analyses[address]
    
    if not (0 <= area_index < len(analysis.areas)):
        return jsonify({'error': 'Invalid area index'}), 400
    
    # Calculate new area
    area_m2 = calculate_polygon_area_m2(coordinates)
    area_acres = area_m2 / 4046.8564224
    area_sqft = area_m2 * 10.7639  # Convert m² to ft²
    
    # Get floors from request or keep existing
    floors = data.get('floors', None)
    
    # Update the area
    area = analysis.areas[area_index]
    area.coordinates = coordinates
    area.area_type = area_type
    area.area_m2 = area_m2
    area.area_acres = area_acres
    area.area_sqft = area_sqft
    
    # Update floors if provided, otherwise keep existing
    if floors is not None:
        area.floors = floors
    
    # Calculate total floor area for buildings
    if area.area_type == 'building':
        area.total_floor_area_sqft = area_sqft * area.floors
    else:
        area.total_floor_area_sqft = area_sqft
    
    # Recalculate totals
    update_analysis_totals(analysis)
    
    return jsonify({
        'success': True,
        'area_m2': area_m2,
        'area_acres': area_acres,
        'area_sqft': area_sqft,
        'floors': area.floors,
        'total_floor_area_sqft': area.total_floor_area_sqft,
        'totals': get_analysis_totals(analysis)
    })

@app.route('/api/update_floors', methods=['POST'])
def update_floors():
    """Update the number of floors for a building"""
    data = request.json
    address = data.get('address', '')
    area_index = data.get('area_index', -1)
    floors = data.get('floors', 1)
    
    if address not in current_analyses:
        return jsonify({'error': 'No analysis found for this address'}), 404
    
    analysis = current_analyses[address]
    
    if not (0 <= area_index < len(analysis.areas)):
        return jsonify({'error': 'Invalid area index'}), 400
    
    area = analysis.areas[area_index]
    area.floors = floors
    
    # Recalculate total floor area for buildings
    if area.area_type == 'building':
        area.total_floor_area_sqft = area.area_sqft * floors
    else:
        area.total_floor_area_sqft = area.area_sqft
    
    # Recalculate totals
    update_analysis_totals(analysis)
    
    return jsonify({
        'success': True,
        'floors': floors,
        'total_floor_area_sqft': area.total_floor_area_sqft,
        'totals': get_analysis_totals(analysis)
    })

@app.route('/api/delete_area', methods=['POST'])
def delete_area():
    """Delete a drawn area"""
    data = request.json
    address = data.get('address', '')
    area_index = data.get('area_index', -1)
    
    if address not in current_analyses:
        return jsonify({'error': 'No analysis found for this address'}), 404
    
    analysis = current_analyses[address]
    
    if 0 <= area_index < len(analysis.areas):
        analysis.areas.pop(area_index)
        update_analysis_totals(analysis)
        
        return jsonify({
            'success': True,
            'totals': get_analysis_totals(analysis)
        })
    
    return jsonify({'error': 'Invalid area index'}), 400

@app.route('/api/get_analysis', methods=['GET'])
def get_analysis():
    """Get current analysis for an address"""
    address = request.args.get('address', '')
    
    if address not in current_analyses:
        return jsonify({'error': 'No analysis found for this address'}), 404
    
    analysis = current_analyses[address]
    
    return jsonify({
        'analysis': asdict(analysis),
        'totals': get_analysis_totals(analysis)
    })

@app.route('/api/export_results', methods=['GET'])
def export_results():
    """Export all analyses to CSV"""
    if not current_analyses:
        return jsonify({'error': 'No analyses to export'}), 400
    
    # Convert analyses to DataFrame
    results = []
    for address, analysis in current_analyses.items():
        results.append({
            'address': analysis.address,
            'lat': analysis.lat,
            'lng': analysis.lng,
            'total_boundary_acres': analysis.total_boundary_acres,
            'building_acres': analysis.building_acres,
            'field_acres': analysis.field_acres,
            'parking_acres': analysis.parking_acres,
            'other_acres': analysis.other_acres,
            'outdoor_acres': analysis.total_boundary_acres - analysis.building_acres,
            'field_utilization_pct': (analysis.field_acres / max(analysis.total_boundary_acres - analysis.building_acres, 0.001)) * 100,
            'building_coverage_pct': (analysis.building_acres / max(analysis.total_boundary_acres, 0.001)) * 100,
            'notes': analysis.notes
        })
    
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), 'maps_analysis_results.csv')
    df.to_csv(output_path, index=False)
    
    return jsonify({
        'success': True,
        'file_path': output_path,
        'results_count': len(results)
    })

def update_analysis_totals(analysis: CampusAnalysis):
    """Update the total areas for each type"""
    analysis.total_boundary_acres = sum(area.area_acres for area in analysis.areas if area.area_type == 'boundary')
    analysis.building_acres = sum(area.area_acres for area in analysis.areas if area.area_type == 'building')
    analysis.field_acres = sum(area.area_acres for area in analysis.areas if area.area_type == 'field')
    analysis.parking_acres = sum(area.area_acres for area in analysis.areas if area.area_type == 'parking')
    analysis.other_acres = sum(area.area_acres for area in analysis.areas if area.area_type == 'other')

def get_analysis_totals(analysis: CampusAnalysis) -> Dict:
    """Get summary totals for an analysis"""
    outdoor_acres = analysis.total_boundary_acres - analysis.building_acres
    field_utilization = (analysis.field_acres / max(outdoor_acres, 0.001)) * 100
    building_coverage = (analysis.building_acres / max(analysis.total_boundary_acres, 0.001)) * 100
    
    return {
        'total_boundary_acres': round(analysis.total_boundary_acres, 2),
        'building_acres': round(analysis.building_acres, 2),
        'field_acres': round(analysis.field_acres, 2),
        'parking_acres': round(analysis.parking_acres, 2),
        'other_acres': round(analysis.other_acres, 2),
        'outdoor_acres': round(outdoor_acres, 2),
        'field_utilization_pct': round(field_utilization, 1),
        'building_coverage_pct': round(building_coverage, 1)
    }

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)  # Different port to avoid conflicts
