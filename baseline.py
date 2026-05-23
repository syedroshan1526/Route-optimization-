"""
Baseline solution generator for comparison
Implements naive routing strategies for performance benchmarking
"""
import numpy as np
import random
from typing import List, Dict, Tuple


class BaselineGenerator:
    """
    Generates naive baseline solutions for performance comparison
    """
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_random_baseline(self, locations_df, num_vehicles: int, 
                               vehicle_capacity: int) -> List[Dict]:
        """
        Generate random assignment baseline
        
        Args:
            locations_df: DataFrame with location data
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            
        Returns:
            List of route dictionaries
        """
        n_customers = len(locations_df) - 1  # Exclude depot
        customers = list(range(1, n_customers + 1))  # Customer indices
        demands = locations_df['demand'].tolist()
        
        # Randomly shuffle customers
        random.shuffle(customers)
        
        routes = []
        customer_idx = 0
        
        for vehicle_id in range(num_vehicles):
            if customer_idx >= len(customers):
                break
                
            route = [0]  # Start at depot
            current_load = 0
            
            # Assign customers to this vehicle
            while (customer_idx < len(customers) and 
                   current_load + demands[customers[customer_idx]] <= vehicle_capacity):
                customer = customers[customer_idx]
                route.append(customer)
                current_load += demands[customer]
                customer_idx += 1
            
            if len(route) > 1:  # Only add route if customers were assigned
                route.append(0)  # Return to depot
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def generate_sequential_baseline(self, locations_df, num_vehicles: int,
                                   vehicle_capacity: int) -> List[Dict]:
        """
        Generate sequential assignment baseline (customers in order)
        
        Args:
            locations_df: DataFrame with location data
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            
        Returns:
            List of route dictionaries
        """
        n_customers = len(locations_df) - 1
        customers = list(range(1, n_customers + 1))
        demands = locations_df['demand'].tolist()
        
        routes = []
        customer_idx = 0
        
        for vehicle_id in range(num_vehicles):
            if customer_idx >= len(customers):
                break
                
            route = [0]
            current_load = 0
            
            # Assign customers sequentially
            while (customer_idx < len(customers) and 
                   current_load + demands[customers[customer_idx]] <= vehicle_capacity):
                customer = customers[customer_idx]
                route.append(customer)
                current_load += demands[customer]
                customer_idx += 1
            
            if len(route) > 1:
                route.append(0)
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def generate_nearest_neighbor_baseline(self, locations_df, distance_matrix,
                                         num_vehicles: int, vehicle_capacity: int) -> List[Dict]:
        """
        Generate nearest neighbor baseline (greedy approach)
        
        Args:
            locations_df: DataFrame with location data
            distance_matrix: Precomputed distance matrix
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            
        Returns:
            List of route dictionaries
        """
        n_customers = len(locations_df) - 1
        demands = locations_df['demand'].tolist()
        unvisited = set(range(1, n_customers + 1))
        
        routes = []
        
        for vehicle_id in range(num_vehicles):
            if not unvisited:
                break
                
            route = [0]  # Start at depot
            current_load = 0
            current_location = 0
            
            # Greedily assign nearest unvisited customer
            while unvisited and current_load < vehicle_capacity:
                # Find nearest unvisited customer that fits capacity
                nearest_customer = None
                min_distance = float('inf')
                
                # Convert unvisited to list for efficient iteration
                unvisited_list = list(unvisited)
                for customer in unvisited_list:
                    if current_load + demands[customer] <= vehicle_capacity:
                        distance = distance_matrix[current_location][customer]
                        if distance < min_distance:
                            min_distance = distance
                            nearest_customer = customer
                
                if nearest_customer is None:
                    break  # No more customers fit in this vehicle
                
                # Add customer to route
                route.append(nearest_customer)
                current_load += demands[nearest_customer]
                unvisited.remove(nearest_customer)
                current_location = nearest_customer
            
            if len(route) > 1:
                route.append(0)  # Return to depot
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def generate_improved_nearest_neighbor_baseline(self, locations_df, distance_matrix,
                                                   num_vehicles: int, vehicle_capacity: int) -> List[Dict]:
        """
        Generate improved nearest neighbor baseline with performance optimizations
        
        Args:
            locations_df: DataFrame with location data
            distance_matrix: Precomputed distance matrix
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            
        Returns:
            List of route dictionaries
        """
        n_customers = len(locations_df) - 1
        demands = np.array(locations_df['demand'].tolist())  # Use numpy for efficiency
        unvisited = set(range(1, n_customers + 1))
        
        routes = []
        
        for vehicle_id in range(num_vehicles):
            if not unvisited:
                break
                
            route = [0]  # Start at depot
            current_load = 0
            current_location = 0
            
            # Convert distance matrix row to numpy array for faster access
            dist_row = distance_matrix[current_location]
            
            # Greedily assign nearest unvisited customer
            while unvisited and current_load < vehicle_capacity:
                # Find nearest unvisited customer that fits capacity
                nearest_customer = None
                min_distance = float('inf')
                
                # Vectorized approach to find nearest customer
                for customer in unvisited:
                    if current_load + demands[customer] <= vehicle_capacity:
                        distance = dist_row[customer]
                        if distance < min_distance:
                            min_distance = distance
                            nearest_customer = customer
                
                if nearest_customer is None:
                    break  # No more customers fit in this vehicle
                
                # Add customer to route
                route.append(nearest_customer)
                current_load += demands[nearest_customer]
                unvisited.remove(nearest_customer)
                current_location = nearest_customer
                
                # Update distance row for next iteration
                if unvisited:
                    dist_row = distance_matrix[current_location]
            
            if len(route) > 1:
                route.append(0)  # Return to depot
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def calculate_baseline_metrics(self, routes: List[Dict], distance_matrix) -> Dict:
        """
        Calculate performance metrics for baseline solution
        
        Args:
            routes: List of route dictionaries
            distance_matrix: Distance matrix
            
        Returns:
            Dictionary with performance metrics
        """
        total_distance = 0
        num_vehicles = len(routes)
        
        # Calculate total distance
        for route_info in routes:
            route = route_info['route']
            route_distance = 0
            for i in range(len(route) - 1):
                from_idx = route[i]
                to_idx = route[i + 1]
                route_distance += distance_matrix[from_idx][to_idx]
            total_distance += route_distance
            route_info['distance'] = route_distance
        
        return {
            'total_distance': total_distance,
            'num_vehicles': num_vehicles,
            'routes': routes
        }


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    from distance_matrix import DistanceCalculator
    
    # Generate sample data
    loader = DataLoader()
    locations = loader.generate_sample_data(8)
    
    # Calculate distances
    calculator = DistanceCalculator(use_real_distances=False)
    distance_matrix = calculator.calculate_distance_matrix(locations)
    
    # Generate baselines
    baseline_gen = BaselineGenerator()
    
    random_baseline = baseline_gen.generate_random_baseline(
        locations, num_vehicles=2, vehicle_capacity=15
    )
    
    sequential_baseline = baseline_gen.generate_sequential_baseline(
        locations, num_vehicles=2, vehicle_capacity=15
    )
    
    nn_baseline = baseline_gen.generate_nearest_neighbor_baseline(
        locations, distance_matrix, num_vehicles=2, vehicle_capacity=15
    )
    
    # Calculate metrics
    random_metrics = baseline_gen.calculate_baseline_metrics(random_baseline, distance_matrix)
    sequential_metrics = baseline_gen.calculate_baseline_metrics(sequential_baseline, distance_matrix)
    nn_metrics = baseline_gen.calculate_baseline_metrics(nn_baseline, distance_matrix)
    
    print("Baseline Comparison:")
    print(f"Random: {random_metrics['total_distance']:.2f}km, {random_metrics['num_vehicles']} vehicles")
    print(f"Sequential: {sequential_metrics['total_distance']:.2f}km, {sequential_metrics['num_vehicles']} vehicles")
    print(f"Nearest Neighbor: {nn_metrics['total_distance']:.2f}km, {nn_metrics['num_vehicles']} vehicles")