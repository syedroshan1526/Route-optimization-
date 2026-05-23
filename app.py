"""
Web application for the Route Optimization System
Provides a modern web interface to interact with the optimization algorithms
"""
import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Import our optimization modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import RouteOptimizationSystem
from config import Config


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


@app.route('/')
def index():
    """Main page with optimization form"""
    return render_template('index.html')


@app.route('/optimize', methods=['POST'])
def optimize():
    """Handle route optimization request"""
    try:
        # Get parameters from request
        num_locations = int(request.form.get('num_locations', 10))
        num_vehicles = int(request.form.get('num_vehicles', 3))
        vehicle_capacity = int(request.form.get('vehicle_capacity', 15))
        algorithm = request.form.get('algorithm', 'enhanced_nearest_neighbor')
        
        # Handle CSV upload
        csv_file = request.files.get('csv_file')
        
        # Initialize system
        config = Config()
        system = RouteOptimizationSystem(config)
        
        # Load data
        if csv_file and csv_file.filename != '':
            # Save uploaded file temporarily
            filename = secure_filename(csv_file.filename)
            filepath = os.path.join('temp', filename)
            os.makedirs('temp', exist_ok=True)
            csv_file.save(filepath)
            
            # Load from CSV
            success = system.load_data(csv_path=filepath, num_locations=num_locations)
            os.remove(filepath)  # Clean up temp file
        else:
            # Generate synthetic data
            success = system.load_data(num_locations=num_locations)
        
        if not success:
            return jsonify({'error': 'Failed to load data'}), 400
        
        # Calculate distances
        success = system.calculate_distances()
        if not success:
            return jsonify({'error': 'Failed to calculate distances'}), 400
        
        # Generate baselines
        success = system.generate_baselines(num_vehicles, vehicle_capacity)
        if not success:
            return jsonify({'error': 'Failed to generate baselines'}), 400
        
        # Solve optimization
        success = system.solve_optimization(num_vehicles, vehicle_capacity, algorithm)
        if not success:
            return jsonify({'error': 'Failed to solve optimization'}), 400
        
        # Prepare response data
        result = {
            'success': True,
            'solution': {
                'total_distance': system.optimized_solution['total_distance'],
                'num_vehicles': system.optimized_solution['num_vehicles'],
                'solve_time': system.optimized_solution['solve_time'],
                'algorithm': system.optimized_solution['algorithm'],
                'routes': system.optimized_solution['routes']
            },
            'baselines': system.baseline_solutions,
            'locations': system.locations_df.to_dict('records')
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/visualize', methods=['POST'])
def visualize():
    """Generate visualization and return map HTML"""
    try:
        # Get data from request
        data = request.json
        locations_data = data.get('locations', [])
        routes = data.get('routes', [])
        
        # Convert locations back to DataFrame
        locations_df = pd.DataFrame(locations_data)
        
        # Initialize system
        config = Config()
        system = RouteOptimizationSystem(config)
        system.locations_df = locations_df
        system.optimized_solution = {'routes': routes}
        
        # Generate visualization
        success = system.generate_visualization(output_filename='web_routes.html')
        if not success:
            return jsonify({'error': 'Failed to generate visualization'}), 400
        
        # Return path to generated map
        return jsonify({'map_path': 'output/web_routes.html'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_map/<filename>')
def get_map(filename):
    """Serve generated map file"""
    import os
    file_path = os.path.join('output', filename)
    return send_file(file_path)


@app.route('/output/<path:filename>')
def output_static(filename):
    """Serve files from output directory"""
    import os
    file_path = os.path.join('output', filename)
    return send_file(file_path)


@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Generate HTML report"""
    try:
        data = request.json
        locations_data = data.get('locations', [])
        routes = data.get('routes', [])
        solution = data.get('solution', {})
        baselines = data.get('baselines', {})
        
        # Convert locations back to DataFrame
        import pandas as pd
        locations_df = pd.DataFrame(locations_data)
        
        # Initialize system and generate report
        config = Config()
        system = RouteOptimizationSystem(config)
        system.locations_df = locations_df
        
        # Ensure solution has all required keys
        required_keys = ['total_distance', 'num_vehicles', 'solve_time', 'algorithm', 'routes', 'feasible']
        for key in required_keys:
            if key not in solution:
                solution[key] = '' if key == 'algorithm' else 0 if key in ['total_distance', 'num_vehicles', 'solve_time'] else [] if key == 'routes' else True
        
        system.optimized_solution = solution
        system.baseline_solutions = baselines
        
        # Generate report
        success = system.generate_reports(output_filename='web_optimization_report.html')
        if not success:
            return jsonify({'error': 'Failed to generate report'}), 400
        
        return jsonify({'report_path': 'output/web_optimization_report.html'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)