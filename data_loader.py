"""
Data loading and preprocessing module
Handles CSV input and synthetic data generation
"""
import pandas as pd
import numpy as np
import random
from typing import Tuple, Dict
from config import Config


class DataLoader:
    """
    Professional data loader for route optimization problems
    """
    
    def __init__(self, seed: int = Config.SEED):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
    
    def load_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load delivery locations from CSV file
        
        Expected columns: id, lat, lon, demand (optional)
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with location data
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['id', 'lat', 'lon']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Add demand column if not present
            if 'demand' not in df.columns:
                df['demand'] = 1
                print("Warning: 'demand' column not found. Setting all demands to 1.")
            
            # Validate data ranges
            if not df['lat'].between(-90, 90).all():
                raise ValueError("Latitude values must be between -90 and 90")
            if not df['lon'].between(-180, 180).all():
                raise ValueError("Longitude values must be between -180 and 180")
            if (df['demand'] < 0).any():
                raise ValueError("Demand values must be non-negative")
            
            print(f"✓ Loaded {len(df)} locations from {csv_path}")
            return df
            
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty")
        except Exception as e:
            raise ValueError(f"Error loading CSV: {str(e)}")
    
    def generate_sample_data(self, num_locations: int = Config.DEFAULT_NUM_LOCATIONS,
                           center_lat: float = 40.7128, 
                           center_lon: float = -74.0060) -> pd.DataFrame:
        """
        Generate synthetic delivery data for testing
        
        Args:
            num_locations: Number of locations to generate
            center_lat: Center latitude for data generation
            center_lon: Center longitude for data generation
            
        Returns:
            DataFrame with synthetic location data
        """
        # Generate locations around the center point
        latitudes = [center_lat] + list(center_lat + np.random.uniform(-0.1, 0.1, num_locations - 1))
        longitudes = [center_lon] + list(center_lon + np.random.uniform(-0.1, 0.1, num_locations - 1))
        
        # Generate demands (depot has 0 demand)
        demands = [0] + list(np.random.randint(1, 10, num_locations - 1))
        
        data = {
            'id': ['depot'] + [f'customer_{i}' for i in range(1, num_locations)],
            'lat': latitudes,
            'lon': longitudes,
            'demand': demands
        }
        
        df = pd.DataFrame(data)
        print(f"✓ Generated {num_locations} synthetic locations")
        return df
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate input data for optimization
        
        Args:
            df: DataFrame with location data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(df) < 2:
            return False, "Need at least 2 locations (depot + 1 customer)"
        
        if df.iloc[0]['demand'] != 0:
            return False, "First location (depot) must have demand = 0"
        
        if (df['demand'] < 0).any():
            return False, "All demands must be non-negative"
        
        return True, "Data is valid"


# Example usage
if __name__ == "__main__":
    loader = DataLoader()
    
    # Generate sample data
    sample_data = loader.generate_sample_data(10)
    print(sample_data.head())
    
    # Validate data
    is_valid, message = loader.validate_data(sample_data)
    print(f"Validation: {message}")