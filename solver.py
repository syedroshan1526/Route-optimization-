"""
Professional VRP solver implementation
Heuristic solver for capacitated vehicle routing problems
"""
import numpy as np
import time
from typing import List, Dict
from config import Config

# Import OR-Tools if available
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class VRPSolver:
    """
    Heuristic VRP solver for capacitated vehicle routing problems
    
    This is a constructive heuristic that builds feasible solutions under
    capacity constraints. It does not guarantee global optimality but
    provides good-quality solutions in reasonable time for practical problems.
    """
    
    def __init__(self, distance_matrix, demands: List[int], 
                 vehicle_capacities: List[int], config: Config = None):
        """
        Initialize VRP solver
        
        Args:
            distance_matrix: Precomputed distance matrix
            demands: Demand at each location (depot = 0)
            vehicle_capacities: Capacity of each vehicle
            config: Configuration object
        """
        self.distance_matrix = distance_matrix
        self.demands = demands
        self.vehicle_capacities = vehicle_capacities
        self.config = config or Config()
        self.num_locations = len(distance_matrix)
        self.num_vehicles = len(vehicle_capacities)
    
    def solve(self, algorithm: str = "enhanced_nearest_neighbor") -> Dict:
        """
        Solve VRP using specified algorithm
        
        Args:
            algorithm: Algorithm to use ('nearest_neighbor', 'enhanced_nearest_neighbor', 'ortools')
            
        Returns:
            Dictionary with solution and metrics
        """
        start_time = time.time()
        
        if algorithm == "nearest_neighbor":
            routes = self._nearest_neighbor_heuristic()
        elif algorithm == "enhanced_nearest_neighbor":
            routes = self._enhanced_nearest_neighbor_heuristic()
        elif algorithm == "ortools":
            if not ORTOOLS_AVAILABLE:
                print("⚠️ OR-Tools not available, falling back to enhanced nearest neighbor")
                routes = self._enhanced_nearest_neighbor_heuristic()
            else:
                routes = self._solve_with_ortools()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        solve_time = time.time() - start_time
        
        # Calculate total distance
        total_distance = 0
        for route_info in routes:
            route_distance = self._calculate_route_distance(route_info['route'])
            total_distance += route_distance
            route_info['distance'] = route_distance
        
        result = {
            'routes': routes,
            'total_distance': total_distance,
            'num_vehicles': len(routes),
            'solve_time': solve_time,
            'algorithm': algorithm,
            'feasible': self._validate_solution(routes)
        }
        
        # Apply local search improvement if requested
        if self.config.LOCAL_SEARCH_IMPROVEMENT:
            result = self._apply_local_search_improvement(result)
        
        return result
    
    def _solve_with_ortools(self) -> List[Dict]:
        """
        Solve VRP using Google OR-Tools
        """
        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(self.distance_matrix), 
            self.num_vehicles, 
            0  # Depot is at index 0
        )

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # Create a callback to return the distance between locations
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(self.distance_matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint
        def demand_callback(from_index):
            """Returns the demand of the node."""
            from_node = manager.IndexToNode(from_index)
            return self.demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            self.vehicle_capacities,  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )

        # Setting first solution heuristic
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        
        # Set time limit to prevent long computations
        search_parameters.time_limit.seconds = 30

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            # Extract the solution
            routes = []
            for vehicle_id in range(self.num_vehicles):
                index = routing.Start(vehicle_id)
                route = [manager.IndexToNode(index)]
                
                # Track the load for this route
                current_load = 0
                
                while not routing.IsEnd(index):
                    node_index = manager.IndexToNode(index)
                    current_load += self.demands[node_index] if node_index != 0 else 0  # Don't count depot
                    index = solution.Value(routing.NextVar(index))
                    route.append(manager.IndexToNode(index))
                
                # Only add route if it has more than just the depot
                if len(route) > 2:  # depot -> other nodes -> depot
                    routes.append({
                        'vehicle_id': vehicle_id,
                        'route': route[:-1],  # Exclude the last depot duplicate
                        'load': current_load
                    })
            return routes
        else:
            # Fallback to heuristic if OR-Tools couldn't find a solution
            print("⚠️ OR-Tools couldn't find a solution, using enhanced nearest neighbor")
            return self._enhanced_nearest_neighbor_heuristic()

    def _nearest_neighbor_heuristic(self) -> List[Dict]:
        """
        Basic nearest neighbor heuristic for VRP
        
        This greedy approach builds routes by always selecting the
        nearest unvisited customer that fits in the current vehicle's capacity.
        
        Tradeoffs:
        + Fast execution time O(n²)
        + Simple implementation
        - May produce suboptimal solutions
        - No global optimization
        """
        unvisited = set(range(1, self.num_locations))  # Exclude depot
        routes = []
        
        for vehicle_id in range(self.num_vehicles):
            if not unvisited:
                break
                
            route = [0]  # Start at depot
            current_load = 0
            current_location = 0
            
            # Greedily assign nearest feasible customer
            while unvisited and current_load < self.vehicle_capacities[vehicle_id]:
                nearest_customer = None
                min_distance = float('inf')
                
                for customer in unvisited:
                    if current_load + self.demands[customer] <= self.vehicle_capacities[vehicle_id]:
                        distance = self.distance_matrix[current_location][customer]
                        if distance < min_distance:
                            min_distance = distance
                            nearest_customer = customer
                
                if nearest_customer is None:
                    break  # No more customers fit in this vehicle
                
                # Add customer to route
                route.append(nearest_customer)
                current_load += self.demands[nearest_customer]
                unvisited.remove(nearest_customer)
                current_location = nearest_customer
            
            # Return to depot
            if len(route) > 1:
                route.append(0)
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def _enhanced_nearest_neighbor_heuristic(self) -> List[Dict]:
        """
        Enhanced nearest neighbor with look-ahead optimization
        
        Improves basic nearest neighbor by considering future capacity
        utilization and route efficiency.
        
        Tradeoffs:
        + Better solution quality than basic NN
        + Still maintains reasonable execution time
        - More complex implementation
        - Still heuristic (no optimality guarantee)
        """
        unvisited = set(range(1, self.num_locations))
        routes = []
        
        for vehicle_id in range(self.num_vehicles):
            if not unvisited:
                break
                
            route = [0]
            current_load = 0
            current_location = 0
            
            # Enhanced assignment with efficiency consideration
            while unvisited and current_load < self.vehicle_capacities[vehicle_id]:
                best_customer = None
                best_score = float('inf')
                
                # Evaluate all feasible customers
                for customer in unvisited:
                    if current_load + self.demands[customer] <= self.vehicle_capacities[vehicle_id]:
                        # Distance to customer
                        distance = self.distance_matrix[current_location][customer]
                        
                        # Efficiency score (distance per demand unit)
                        efficiency = distance / max(self.demands[customer], 1)
                        
                        # Prefer customers that are close and have high demand
                        score = efficiency
                        
                        if score < best_score:
                            best_score = score
                            best_customer = customer
                
                if best_customer is None:
                    break
                
                # Add best customer to route
                route.append(best_customer)
                current_load += self.demands[best_customer]
                unvisited.remove(best_customer)
                current_location = best_customer
            
            # Return to depot
            if len(route) > 1:
                route.append(0)
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route,
                    'load': current_load
                })
        
        return routes
    
    def _calculate_route_distance(self, route: List[int]) -> float:
        """Calculate total distance for a route"""
        return sum(self.distance_matrix[route[i]][route[i+1]] 
                  for i in range(len(route) - 1))
    
    def _validate_solution(self, routes: List[Dict]) -> bool:
        """
        Validate that solution satisfies all constraints
        
        Args:
            routes: List of route dictionaries
            
        Returns:
            True if solution is feasible, False otherwise
        """
        # Check capacity constraints
        for route_info in routes:
            vehicle_idx = route_info['vehicle_id']
            if vehicle_idx < len(self.vehicle_capacities) and route_info['load'] > self.vehicle_capacities[vehicle_idx]:
                return False
        
        # Check that all customers are served
        served_customers = set()
        for route_info in routes:
            for location in route_info['route']:
                if location > 0:  # Skip depot
                    served_customers.add(location)
        
        total_customers = self.num_locations - 1
        if len(served_customers) != total_customers:
            return False
        
        return True
    
    def _apply_local_search_improvement(self, solution: Dict) -> Dict:
        """
        Apply 2-opt local search to improve the solution
        
        Args:
            solution: Initial solution dictionary
            
        Returns:
            Improved solution dictionary
        """
        improved_routes = []
        total_improvement = 0
        
        for route_info in solution['routes']:
            original_route = route_info['route']
            improved_route = self._two_opt(original_route)
            
            # Calculate new distance
            new_distance = self._calculate_route_distance(improved_route)
            old_distance = route_info['distance']
            improvement = old_distance - new_distance
            total_improvement += improvement
            
            improved_routes.append({
                'vehicle_id': route_info['vehicle_id'],
                'route': improved_route,
                'load': route_info['load'],
                'distance': new_distance
            })
        
        # Update total distance
        new_total_distance = solution['total_distance'] - total_improvement
        
        return {
            'routes': improved_routes,
            'total_distance': new_total_distance,
            'num_vehicles': solution['num_vehicles'],
            'solve_time': solution['solve_time'],
            'algorithm': solution['algorithm'] + '_with_local_search',
            'feasible': solution['feasible']
        }
    
    def _two_opt(self, route: List[int]) -> List[int]:
        """
        Apply 2-opt improvement to a single route
        
        Args:
            route: Original route
            
        Returns:
            Potentially improved route
        """
        # Don't include the depot at both ends for 2-opt operation
        if len(route) <= 3:  # route is depot -> customer -> depot, or shorter
            return route
        
        # Extract the inner part of the route (excluding start/end depot)
        if route[0] == 0 and route[-1] == 0:
            inner_route = route[1:-1]
        else:
            # If the route doesn't start/end with depot, handle differently
            inner_route = route[1:] if route[0] == 0 else route[:]
        
        if len(inner_route) <= 2:
            return route
        
        best_route = inner_route[:]
        improved = True
        
        while improved:
            improved = False
            
            for i in range(len(best_route) - 1):
                for j in range(i + 2, len(best_route)):
                    new_route = best_route[:]
                    # Reverse the section between i and j
                    new_route[i:j+1] = reversed(new_route[i:j+1])
                    
                    # Calculate distances - first add depot back for evaluation
                    test_route_with_depot = [0] + new_route + [0]
                    new_distance = self._calculate_route_distance(test_route_with_depot)
                    
                    test_route_with_depot_old = [0] + best_route + [0]
                    old_distance = self._calculate_route_distance(test_route_with_depot_old)
                    
                    if new_distance < old_distance:
                        best_route = new_route
                        improved = True
                        break
                if improved:
                    break
        
        # Add depot back to the route
        return [0] + best_route + [0]


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    from distance_matrix import DistanceCalculator
    
    # Generate sample problem
    loader = DataLoader()
    locations = loader.generate_sample_data(10)
    demands = locations['demand'].tolist()
    
    calculator = DistanceCalculator(use_real_distances=False)
    distance_matrix = calculator.calculate_distance_matrix(locations)
    
    # Solve VRP
    solver = VRPSolver(
        distance_matrix=distance_matrix,
        demands=demands,
        vehicle_capacities=[15, 15, 15]
    )
    
    # Compare algorithms
    basic_solution = solver.solve("nearest_neighbor")
    enhanced_solution = solver.solve("enhanced_nearest_neighbor")
    
    print("VRP Solution Comparison:")
    print(f"Basic NN: {basic_solution['total_distance']:.2f}km in {basic_solution['solve_time']:.4f}s")
    print(f"Enhanced NN: {enhanced_solution['total_distance']:.2f}km in {enhanced_solution['solve_time']:.4f}s")
    
    if ORTOOLS_AVAILABLE:
        ortools_solution = solver.solve("ortools")
        print(f"OR-Tools: {ortools_solution['total_distance']:.2f}km in {ortools_solution['solve_time']:.4f}s")
    else:
        print("OR-Tools not available")
    
    improvement = ((basic_solution['total_distance'] - enhanced_solution['total_distance']) / basic_solution['total_distance'] * 100)
    print(f"Improvement: {improvement:.1f}%")