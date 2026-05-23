"""
Configuration file for Route Optimization System
Centralized configuration management
"""
import os

class Config:
    # Data configuration
    DEFAULT_NUM_LOCATIONS = 15
    DEFAULT_VEHICLE_CAPACITY = 15
    DEFAULT_NUM_VEHICLES = 3
    
    # Distance calculation
    EARTH_RADIUS_KM = 6371
    USE_REAL_DISTANCES = True  # Set to False to use Haversine only
    
    # API configuration
    OSRM_SERVER = "http://router.project-osrm.org"
    API_TIMEOUT = 30
    
    # Visualization
    MAP_WIDTH = 1000
    MAP_HEIGHT = 600
    COLORS = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', 
        '#00FFFF', '#FFA500', '#800080', '#FFC0CB', '#A52A2A'
    ]
    
    # Output configuration
    OUTPUT_DIR = "output"
    REPORT_FILENAME = "optimization_report.html"
    MAP_FILENAME = "routes.html"
    
    # Performance
    MAX_LOCATIONS_FOR_EXACT = 10  # Use exact methods for small problems
    SEED = 42  # For reproducible results
    LOCAL_SEARCH_IMPROVEMENT = True  # Enable local search improvement after initial solution
    
    @classmethod
    def create_output_dir(cls):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(cls.OUTPUT_DIR):
            os.makedirs(cls.OUTPUT_DIR)