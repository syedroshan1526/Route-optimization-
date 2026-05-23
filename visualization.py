"""
Professional visualization module
Creates interactive maps and route visualizations
"""
import folium
import pandas as pd
import numpy as np
from branca.element import Figure
from typing import List, Dict
from config import Config


class RouteVisualizer:
    """
    Professional route visualization with enhanced features
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.colors = self.config.COLORS
    
    def create_interactive_map(self, locations_df, routes: List[Dict], 
                             title: str = "Optimized Delivery Routes") -> folium.Map:
        """
        Create professional interactive map with enhanced visualization
        
        Args:
            locations_df: DataFrame with location data
            routes: List of route dictionaries
            title: Map title
            
        Returns:
            Folium map object
        """
        # Calculate map center
        avg_lat = locations_df['lat'].mean()
        avg_lon = locations_df['lon'].mean()
        
        # Create base map
        fig = Figure(width=self.config.MAP_WIDTH, height=self.config.MAP_HEIGHT)
        m = folium.Map(
            location=[avg_lat, avg_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        fig.add_child(m)
        
        # Add depot marker with summary
        depot = locations_df.iloc[0]
        depot_routes = [r for r in routes if len(r['route']) > 2]  # Routes with customers
        depot_summary = f"Depot<br>Total Routes: {len(depot_routes)}"
        
        folium.Marker(
            [depot['lat'], depot['lon']],
            popup=folium.Popup(depot_summary, max_width=300),
            tooltip="Depot Location",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
        
        # Add customer markers with detailed information
        for idx, row in locations_df.iterrows():
            if idx > 0:  # Skip depot
                # Find which vehicle serves this customer
                assigned_vehicle = None
                for route_info in routes:
                    if idx in route_info['route']:
                        assigned_vehicle = route_info['vehicle_id']
                        break
                
                popup_content = f"""
                <b>Customer: {row['id']}</b><br>
                Demand: {row['demand']} units<br>
                Assigned Vehicle: {assigned_vehicle if assigned_vehicle is not None else 'Unassigned'}<br>
                Coordinates: ({row['lat']:.4f}, {row['lon']:.4f})
                """
                
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"Customer {row['id']}",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        
        # Draw routes with distinct colors and styling
        for i, route_info in enumerate(routes):
            route_indices = route_info['route']
            route_coords = []
            
            # Extract coordinates for this route
            for loc_idx in route_indices:
                lat = locations_df.iloc[loc_idx]['lat']
                lon = locations_df.iloc[loc_idx]['lon']
                route_coords.append([lat, lon])
            
            # Add route polyline
            color = self.colors[i % len(self.colors)]
            route_distance = route_info.get('distance', 0)
            route_load = route_info.get('load', 0)
            
            popup_content = f"""
            <b>Vehicle {route_info['vehicle_id']}</b><br>
            Distance: {route_distance:.2f} km<br>
            Load: {route_load} units<br>
            Customers: {len(route_indices) - 2}  <!-- Exclude depot visits -->
            """
            
            folium.PolyLine(
                route_coords,
                color=color,
                weight=5,
                opacity=0.8,
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(m)
            
            # Add directional arrows for better visualization
            self._add_directional_markers(m, route_coords, color, route_info['vehicle_id'])
        
        # Add legend
        self._add_legend(m, routes)
        
        # Add title
        self._add_title(m, title)
        
        # Add route statistics panel
        self._add_statistics_panel(m, routes, locations_df)
        
        return m
    
    def _add_directional_markers(self, map_obj, route_coords: List[List[float]], 
                               color: str, vehicle_id: int):
        """Add directional markers to show route flow"""
        if len(route_coords) < 2:
            return
            
        # Add arrows at regular intervals
        for i in range(0, len(route_coords) - 1, max(1, len(route_coords) // 4)):
            start_point = route_coords[i]
            end_point = route_coords[i + 1]
            
            # Calculate midpoint
            mid_lat = (start_point[0] + end_point[0]) / 2
            mid_lon = (start_point[1] + end_point[1]) / 2
            
            # Add small arrow marker
            folium.RegularPolygonMarker(
                [mid_lat, mid_lon],
                number_of_sides=3,
                radius=5,
                color=color,
                fill_color=color,
                fill_opacity=0.8,
                popup=f"Direction: Vehicle {vehicle_id}"
            ).add_to(map_obj)
    
    def _add_legend(self, map_obj, routes: List[Dict]):
        """Add legend showing vehicle assignments"""
        legend_html = """
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            width: 180px;
            height: auto;
            background-color: white;
            border: 2px solid grey;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
            z-index: 999;
        ">
        <p><strong>Vehicle Routes</strong></p>
        """
        
        for i, route_info in enumerate(routes):
            color = self.colors[i % len(self.colors)]
            legend_html += f"""
            <p>
                <span style="color:{color};font-size:20px;">&#9679;</span>
                Vehicle {route_info['vehicle_id']} ({len(route_info['route'])-2} customers)
            </p>
            """
        
        legend_html += "</div>"
        map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    def _add_title(self, map_obj, title: str):
        """Add title to the map"""
        title_html = f"""
        <div style="
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background-color: white;
            padding: 10px 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            z-index: 1000;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        ">
            {title}
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(title_html))
    
    def _add_statistics_panel(self, map_obj, routes: List[Dict], locations_df):
        """Add a statistics panel with route information"""
        total_distance = sum(route_info.get('distance', 0) for route_info in routes)
        total_customers = len(locations_df) - 1  # Exclude depot
        served_customers = sum(len(route_info['route']) - 2 for route_info in routes)  # Subtract 2 for depot entries
        num_vehicles_used = len(routes)
        avg_distance_per_route = total_distance / num_vehicles_used if num_vehicles_used > 0 else 0
        
        stats_html = f"""
        <div style="
            position: fixed;
            top: 70px;
            right: 10px;
            width: 250px;
            height: auto;
            background-color: white;
            border: 2px solid grey;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
            z-index: 1000;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            overflow-y: auto;
        ">
        <h4>Route Statistics</h4>
        <p><strong>Total Distance:</strong> {total_distance:.2f} km</p>
        <p><strong>Vehicles Used:</strong> {num_vehicles_used}</p>
        <p><strong>Customers Served:</strong> {served_customers}/{total_customers}</p>
        <p><strong>Avg. Distance/Route:</strong> {avg_distance_per_route:.2f} km</p>
        <h5>Per Vehicle Details:</h5>
        """
        
        for i, route_info in enumerate(routes):
            route_distance = route_info.get('distance', 0)
            route_load = route_info.get('load', 0)
            num_customers = len(route_info['route']) - 2  # Exclude depot visits
            stats_html += f"<p><strong>Vehicle {route_info['vehicle_id']}:</strong> {route_distance:.2f}km, {num_customers} customers, load: {route_load}</p>\n"
        
        stats_html += "</div>"
        map_obj.get_root().html.add_child(folium.Element(stats_html))


# Example usage
if __name__ == "__main__":
    from data_loader import DataLoader
    from solver import VRPSolver
    from distance_matrix import DistanceCalculator
    
    # Create sample problem and solve it
    loader = DataLoader()
    locations = loader.generate_sample_data(8)
    demands = locations['demand'].tolist()
    
    calculator = DistanceCalculator(use_real_distances=False)
    distance_matrix = calculator.calculate_distance_matrix(locations)
    
    solver = VRPSolver(distance_matrix, demands, [15, 15])
    solution = solver.solve()
    
    # Create visualization
    visualizer = RouteVisualizer()
    map_obj = visualizer.create_interactive_map(
        locations, 
        solution['routes'], 
        "Professional Route Visualization"
    )
    
    # Save map
    Config.create_output_dir()
    map_path = f"{Config.OUTPUT_DIR}/professional_routes.html"
    map_obj.save(map_path)
    print(f"✓ Map saved to {map_path}")