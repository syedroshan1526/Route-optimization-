"""
Distance matrix calculation module
Computes distances between all location pairs using various methods
"""
import numpy as np
import requests
from typing import Tuple
from math import radians, cos, sin, asin, sqrt
from config import Config


class DistanceCalculator:
    """
    Professional distance calculator supporting multiple distance metrics
    """
    
    def __init__(self, use_real_distances: bool = Config.USE_REAL_DISTANCES):
        self.use_real_distances = use_real_distances
        self.config = Config
    
    def calculate_distance_matrix(self, locations_df) -> np.ndarray:
        """
        Calculate distance matrix using appropriate method
        
        Args:
            locations_df: DataFrame with lat/lon columns
            
        Returns:
            Distance matrix as numpy array
        """
        if self.use_real_distances:
            try:
                return self._calculate_real_distances(locations_df)
            except Exception as e:
                print(f"⚠ Real distance calculation failed: {e}")
                print("⚠ Falling back to Haversine calculation")
                return self._calculate_haversine_distances(locations_df)
        else:
            return self._calculate_haversine_distances(locations_df)
    
    def _calculate_haversine_distances(self, locations_df) -> np.ndarray:
        """
        Calculate distances using Haversine formula (as-the-crow-flies)
        
        Args:
            locations_df: DataFrame with lat/lon columns
            
        Returns:
            Distance matrix using Haversine formula
        """
        n = len(locations_df)
        distance_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lon1 = locations_df.iloc[i]['lat'], locations_df.iloc[i]['lon']
                    lat2, lon2 = locations_df.iloc[j]['lat'], locations_df.iloc[j]['lon']
                    distance_matrix[i][j] = self._haversine_distance(lat1, lon1, lat2, lon2)
                else:
                    distance_matrix[i][j] = 0
        
        print("✓ Calculated Haversine distance matrix")
        return distance_matrix
    
    def _calculate_real_distances(self, locations_df) -> np.ndarray:
        """
        Calculate real driving distances using OSRM API
        
        Args:
            locations_df: DataFrame with lat/lon columns
            
        Returns:
            Distance matrix with real driving distances
        """
        n = len(locations_df)
        distance_matrix = np.zeros((n, n))
        
        # Prepare coordinates for OSRM
        coordinates = []
        for _, row in locations_df.iterrows():
            coordinates.append([row['lon'], row['lat']])  # OSRM uses lon,lat format
        
        # OSRM table service request
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        url = f"{self.config.OSRM_SERVER}/table/v1/driving/{coords_str}"
        
        response = requests.get(url, timeout=self.config.API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if 'distances' in data:
                # Convert from meters to kilometers
                for i in range(n):
                    for j in range(n):
                        if i != j and i < len(data['distances']) and j < len(data['distances'][i]):
                            distance_matrix[i][j] = data['distances'][i][j] / 1000
                print("✓ Calculated real driving distance matrix using OSRM")
                return distance_matrix
        
        # Fallback to Haversine if OSRM fails
        raise Exception("OSRM request failed")
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two points
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon1 - lon2
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return c * self.config.EARTH_RADIUS_KM


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    
    # Load sample data
    loader = DataLoader()
    locations = loader.generate_sample_data(5)
    
    # Calculate distances
    calculator = DistanceCalculator(use_real_distances=False)
    distance_matrix = calculator.calculate_distance_matrix(locations)
    
    print(f"Distance matrix shape: {distance_matrix.shape}")
    print("Sample distances:")
    print(distance_matrix[:3, :3])