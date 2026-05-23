"""
Main orchestrator for Professional Route Optimization System
Integrates all modules into a complete, professional solution
"""
import argparse
import sys
import os
import time
from typing import Dict

from config import Config
from data_loader import DataLoader
from distance_matrix import DistanceCalculator
from baseline import BaselineGenerator
from solver import VRPSolver
from visualization import RouteVisualizer
from report import ReportGenerator


class RouteOptimizationSystem:
    """
    Professional Route Optimization System Orchestrator
    
    This system provides a complete solution for capacitated vehicle routing problems
    with professional-grade features including baseline comparison, comprehensive reporting,
    and interactive visualization.
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.config.create_output_dir()
        
        # Initialize components
        self.data_loader = DataLoader(seed=self.config.SEED)
        self.distance_calculator = DistanceCalculator(
            use_real_distances=self.config.USE_REAL_DISTANCES
        )
        self.baseline_generator = BaselineGenerator(seed=self.config.SEED)
        self.solver = None
        self.visualizer = RouteVisualizer(config=self.config)
        self.report_generator = ReportGenerator(config=self.config)
        
        # Results storage
        self.locations_df = None
        self.distance_matrix = None
        self.optimized_solution = None
        self.baseline_solutions = {}
    
    def load_data(self, csv_path: str = None, num_locations: int = None) -> bool:
        """
        Load or generate location data
        
        Args:
            csv_path: Path to CSV file (optional)
            num_locations: Number of locations to generate (if no CSV)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if csv_path and os.path.exists(csv_path):
                print(f"Loading data from: {csv_path}")
                self.locations_df = self.data_loader.load_from_csv(csv_path)
            else:
                num_locations = num_locations or self.config.DEFAULT_NUM_LOCATIONS
                print(f"Generating {num_locations} synthetic locations")
                self.locations_df = self.data_loader.generate_sample_data(num_locations)
            
            # Validate data
            is_valid, message = self.data_loader.validate_data(self.locations_df)
            if not is_valid:
                print(f"❌ Data validation failed: {message}")
                return False
            
            print("✓ Data loaded and validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return False
    
    def calculate_distances(self) -> bool:
        """
        Calculate distance matrix for all locations
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Calculating distance matrix...")
            self.distance_matrix = self.distance_calculator.calculate_distance_matrix(
                self.locations_df
            )
            print(f"✓ Distance matrix calculated: {self.distance_matrix.shape}")
            return True
            
        except Exception as e:
            print(f"❌ Error calculating distances: {str(e)}")
            return False
    
    def generate_baselines(self, num_vehicles: int, vehicle_capacity: int) -> bool:
        """
        Generate baseline solutions for comparison
        
        Args:
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Generating baseline solutions...")
            
            # Random baseline
            random_baseline = self.baseline_generator.generate_random_baseline(
                self.locations_df, num_vehicles, vehicle_capacity
            )
            random_metrics = self.baseline_generator.calculate_baseline_metrics(
                random_baseline, self.distance_matrix
            )
            self.baseline_solutions['random'] = random_metrics
            
            # Sequential baseline
            sequential_baseline = self.baseline_generator.generate_sequential_baseline(
                self.locations_df, num_vehicles, vehicle_capacity
            )
            sequential_metrics = self.baseline_generator.calculate_baseline_metrics(
                sequential_baseline, self.distance_matrix
            )
            self.baseline_solutions['sequential'] = sequential_metrics
            
            # Nearest neighbor baseline
            nn_baseline = self.baseline_generator.generate_nearest_neighbor_baseline(
                self.locations_df, self.distance_matrix, num_vehicles, vehicle_capacity
            )
            nn_metrics = self.baseline_generator.calculate_baseline_metrics(
                nn_baseline, self.distance_matrix
            )
            self.baseline_solutions['nearest_neighbor'] = nn_metrics
            
            print("✓ Baseline solutions generated:")
            for name, metrics in self.baseline_solutions.items():
                print(f"  {name.title()}: {metrics['total_distance']:.2f}km, "
                      f"{metrics['num_vehicles']} vehicles")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating baselines: {str(e)}")
            return False
    
    def solve_optimization(self, num_vehicles: int, vehicle_capacity: int,
                          algorithm: str = "enhanced_nearest_neighbor") -> bool:
        """
        Solve the VRP optimization problem
        
        Args:
            num_vehicles: Number of vehicles
            vehicle_capacity: Capacity per vehicle
            algorithm: Algorithm to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Solving VRP using {algorithm}...")
            
            # Prepare solver
            demands = self.locations_df['demand'].tolist()
            vehicle_capacities = [vehicle_capacity] * num_vehicles
            
            self.solver = VRPSolver(
                distance_matrix=self.distance_matrix,
                demands=demands,
                vehicle_capacities=vehicle_capacities,
                config=self.config
            )
            
            # Solve
            self.optimized_solution = self.solver.solve(algorithm)
            
            if self.optimized_solution['feasible']:
                print(f"✓ Optimization successful:")
                print(f"  Total distance: {self.optimized_solution['total_distance']:.2f} km")
                print(f"  Vehicles used: {self.optimized_solution['num_vehicles']}")
                print(f"  Solve time: {self.optimized_solution['solve_time']:.3f} seconds")
                return True
            else:
                print("❌ Optimization produced infeasible solution")
                return False
                
        except Exception as e:
            print(f"❌ Error during optimization: {str(e)}")
            return False
    
    def generate_visualization(self, output_filename: str = None) -> bool:
        """
        Generate interactive route visualization
        
        Args:
            output_filename: Output file name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.optimized_solution:
                print("❌ No optimization solution available")
                return False
            
            output_filename = output_filename or self.config.MAP_FILENAME
            output_path = os.path.join(self.config.OUTPUT_DIR, output_filename)
            
            print("Generating interactive visualization...")
            map_obj = self.visualizer.create_interactive_map(
                self.locations_df,
                self.optimized_solution['routes'],
                "Professional Route Optimization Solution"
            )
            
            map_obj.save(output_path)
            print(f"✓ Visualization saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating visualization: {str(e)}")
            return False
    
    def generate_reports(self, output_filename: str = None) -> bool:
        """
        Generate comprehensive optimization reports
        
        Args:
            output_filename: Output file name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.optimized_solution or not self.baseline_solutions:
                print("❌ Missing solution data for reporting")
                return False
            
            output_filename = output_filename or self.config.REPORT_FILENAME
            output_path = os.path.join(self.config.OUTPUT_DIR, output_filename)
            
            # Generate HTML report
            print("Generating comprehensive report...")
            html_report = self.report_generator.generate_comprehensive_report(
                optimized_solution=self.optimized_solution,
                baseline_solutions=self.baseline_solutions,
                locations_df=self.locations_df,
                algorithm_metadata={
                    'timestamp': time.time(),
                    'data_source': 'synthetic' if len(self.locations_df) > 0 else 'csv'
                }
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # Generate console report
            improvements = self.report_generator._calculate_improvements(
                self.optimized_solution, self.baseline_solutions
            )
            
            console_report = self.report_generator.generate_console_report(
                self.optimized_solution, self.baseline_solutions, improvements
            )
            
            print("\n" + console_report)
            print(f"✓ HTML report saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating reports: {str(e)}")
            return False
    
    def run_complete_workflow(self, csv_path: str = None, num_locations: int = None,
                            num_vehicles: int = None, vehicle_capacity: int = None,
                            algorithm: str = "enhanced_nearest_neighbor") -> bool:
        """
        Run the complete optimization workflow
        
        Args:
            csv_path: Input CSV file path
            num_locations: Number of locations to generate
            num_vehicles: Number of vehicles
            vehicle_capacity: Vehicle capacity
            algorithm: Algorithm to use
            
        Returns:
            True if successful, False otherwise
        """
        print("🚀 PROFESSIONAL ROUTE OPTIMIZATION SYSTEM")
        print("=" * 60)
        
        # Use configuration defaults if not specified
        num_vehicles = num_vehicles or self.config.DEFAULT_NUM_VEHICLES
        vehicle_capacity = vehicle_capacity or self.config.DEFAULT_VEHICLE_CAPACITY
        
        # Step 1: Load data
        print("\n📋 STEP 1: Data Loading")
        if not self.load_data(csv_path, num_locations):
            return False
        
        # Step 2: Calculate distances
        print("\n📏 STEP 2: Distance Calculation")
        if not self.calculate_distances():
            return False
        
        # Step 3: Generate baselines
        print("\n📊 STEP 3: Baseline Generation")
        if not self.generate_baselines(num_vehicles, vehicle_capacity):
            return False
        
        # Step 4: Solve optimization
        print("\n🎯 STEP 4: Route Optimization")
        if not self.solve_optimization(num_vehicles, vehicle_capacity, algorithm):
            return False
        
        # Step 5: Generate visualization
        print("\n🗺️ STEP 5: Visualization Generation")
        if not self.generate_visualization():
            return False
        
        # Step 6: Generate reports
        print("\n📝 STEP 6: Report Generation")
        if not self.generate_reports():
            return False
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE WORKFLOW EXECUTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Output files generated in '{self.config.OUTPUT_DIR}' directory:")
        print(f"  • {self.config.MAP_FILENAME} - Interactive route map")
        print(f"  • {self.config.REPORT_FILENAME} - Comprehensive analysis report")
        print("=" * 60)
        
        return True


def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(
        description="Professional Route Optimization System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_professional.py --csv deliveries.csv
  python main_professional.py --num-locations 20 --num-vehicles 4
  python main_professional.py --algorithm nearest_neighbor
        """
    )
    
    parser.add_argument('--csv', type=str, help='Input CSV file path')
    parser.add_argument('--num-locations', type=int, default=Config.DEFAULT_NUM_LOCATIONS,
                       help='Number of locations to generate (default: 15)')
    parser.add_argument('--num-vehicles', type=int, default=Config.DEFAULT_NUM_VEHICLES,
                       help='Number of vehicles (default: 3)')
    parser.add_argument('--vehicle-capacity', type=int, default=Config.DEFAULT_VEHICLE_CAPACITY,
                       help='Vehicle capacity (default: 15)')
    parser.add_argument('--algorithm', type=str, default='enhanced_nearest_neighbor',
                       choices=['nearest_neighbor', 'enhanced_nearest_neighbor', 'ortools'],
                       help='Algorithm to use (default: enhanced_nearest_neighbor)')
    
    args = parser.parse_args()
    
    # Run the system
    system = RouteOptimizationSystem()
    success = system.run_complete_workflow(
        csv_path=args.csv,
        num_locations=args.num_locations,
        num_vehicles=args.num_vehicles,
        vehicle_capacity=args.vehicle_capacity,
        algorithm=args.algorithm
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()