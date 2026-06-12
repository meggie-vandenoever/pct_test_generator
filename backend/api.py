"""
Flask API Backend for Flowchart Analysis

This file creates a REST API that:
1. Receives uploaded flowchart images
2. Translates them to edges using Gemini AI
3. Generates graph visualizations
4. Calculates edge coverage test paths
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from google import genai
from dotenv import load_dotenv
import os
import io
import base64
import json

from models import Flowchart
from graph import get_graph, get_colored_graph, PathGenerator

load_dotenv()


client = genai.Client()

# Create the Flask app
# Flask is the "web server" that listens for requests
app = Flask(__name__)

# CORS = Cross-Origin Resource Sharing
# By default, browsers block requests from one domain (localhost:3000) 
# to another (localhost:5000) for security. CORS allows it.
CORS(app)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    endpoint to check if the API is running
    """
    return jsonify({"status": "healthy", "message": "API is running!"})


@app.route('/api/translate', methods=['POST'])
def translate_flowchart():
    """
    receives an uploaded flowchart image and translates it to edges
    """
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read the image file
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Generate a unique filename based on timestamp
        import time
        timestamp = str(int(time.time()))
        image_filename = f"flowchart_{timestamp}"
        
        # Save the original uploaded image
        original_path = os.path.join(RESULTS_DIR, f"{image_filename}_original.png")
        image.save(original_path)
        
        # Use Gemini AI to analyze the flowchart
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            # model = "gemini-3.1-pro-preview",
            contents=[image, """Analyze this flowchart and identify ALL decision points.
            A decision point is any node that has MORE THAN ONE outgoing edge (i.e., multiple possible paths leaving it).

            Create edges that ONLY connect decision points to other decision points.
            - Skip over any nodes that have only one outgoing edge
            - Trace each branch from a decision point until you reach the NEXT decision point (or an endpoint like Start/End)
            - Include the branch label (Yes/No/etc.) that leads from one decision to the next

            For example, if the flow is: "Is A?" --Yes--> [Do X] --> "Is B?"
            The edge should be: source="Is A?", label="Yes", target="Is B?"

            If a branch leads to a node with no further decision point after it, use "End" as the target.
            Also include edges from "Start" to the first decision point, and from decision points to "End" where applicable.
            So the first term of the first edge HAS to be "Start".
            
            HANDLING DUPLICATE VERTEX NAMES:
            If the flowchart has multiple nodes with the same text (e.g., multiple "End" nodes at different positions),
            you MUST give each one a unique name by appending a number suffix.
            For example: "End_1", "End_2", "End_3" for three different End nodes.
            Use these unique names consistently in both the edges (source/target) and the vertices list.
            
            VERTEX POSITIONS:
            For each unique vertex that appears in the edges (including Start and all End nodes), provide:
            - label: The unique name of the vertex (must match source/target in edges exactly)
            - x: The approximate x coordinate of the vertex center (0-100 scale, where 0 is left edge, 100 is right edge)
            - y: The approximate y coordinate of the vertex center (0-100 scale, where 0 is top edge, 100 is bottom edge)
            
            This allows the graph visualization to match the original flowchart layout."""],
            config={
                "response_mime_type": "application/json",
                "response_schema": Flowchart
            }
        )
        
        # Parse the response
        flowchart_object = Flowchart.model_validate_json(response.text)
        edges = [(edge.source, edge.label, edge.target) for edge in flowchart_object.edges]
        if edges[0][0] != 'Start':
            edges = [('Start', '', edges[0][0])] + edges
        
        # Build vertex positions dictionary: label -> (x, y)
        vertex_positions = {v.label: (v.x, v.y) for v in flowchart_object.vertices}
        
        # Generate the graph visualization with positions
        graph_filename = f"{image_filename}_graph"
        get_graph(edges, graph_name=graph_filename, vertex_positions=vertex_positions)
        
        # Read the generated graph image and encode it as base64
        graph_path = os.path.join(RESULTS_DIR, f"{graph_filename}.png")
        with open(graph_path, 'rb') as f:
            graph_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Also encode the original image
        with open(original_path, 'rb') as f:
            original_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            "success": True,
            "edges": edges,
            "vertex_positions": vertex_positions,
            "original_image": original_base64,
            "graph_image": graph_base64,
            "session_id": timestamp  # We'll use this to track this analysis
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate-paths', methods=['POST'])
def generate_paths():
    """
    given a list of edges, calculate the edge coverage test paths using PathGenerator class to find the minimum set of paths
    needed to cover all edges in the flowchart
    
    Request body:
        {
            "edges": [["Start", "", "Decision1"], ["Decision1", "Yes", "End"], ...],
            "vertex_positions": {"Start": [x, y], "Decision1": [x, y], ...},
            "session_id": "timestamp"
        }
    
    Returns:
        JSON with the paths and a colored graph image
    """
    try:
        # Get the JSON data from the request body
        data = request.get_json()
        
        if not data or 'edges' not in data:
            return jsonify({"error": "No edges provided"}), 400
        
        # Convert edges from list format to tuple format
        edges = [tuple(edge) for edge in data['edges']]
        session_id = data.get('session_id', 'default')
        test_depth_level = data.get('test_depth_level', 1)
        
        # Get vertex positions (convert from list to tuple if needed)
        vertex_positions_raw = data.get('vertex_positions', {})
        vertex_positions = {k: tuple(v) if isinstance(v, list) else v for k, v in vertex_positions_raw.items()}

        # Use PathGenerator to find edge coverage paths
        pathgenerator = PathGenerator(edges, test_depth_level)
        edge_coverage_paths = pathgenerator.run()
        print('paths found')
        print(edge_coverage_paths)

        # Generate the colored graph showing the paths
        colored_graph_filename = f"flowchart_{session_id}_paths"
        get_colored_graph(pathgenerator.edge_coverage_3syntax, graph_name=colored_graph_filename, vertex_positions=vertex_positions)
        
        # Read and encode the colored graph
        colored_graph_path = os.path.join(RESULTS_DIR, f"{colored_graph_filename}.png")
        with open(colored_graph_path, 'rb') as f:
            colored_graph_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Format paths for display
        # Each path is a list of edges: [(src, label, dst), ...]
        formatted_paths = []
        for i, path in enumerate(edge_coverage_paths):
            path_description = []
            for edge in path:
                if edge[1]:  # If there's a label
                    path_description.append(f"{edge[0]} --{edge[1]}--> {edge[2]}")
                else:
                    path_description.append(f"{edge[0]} --> {edge[2]}")
            formatted_paths.append({
                "path_number": i + 1,
                "steps": path_description,
                "raw_path": path
            })
        
        return jsonify({
            "success": True,
            "num_paths": len(edge_coverage_paths),
            "paths": formatted_paths,
            "colored_graph": colored_graph_base64
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR in generate_paths: {str(e)}")
        print(error_traceback)
        return jsonify({"error": str(e), "traceback": error_traceback}), 500


@app.route('/api/regenerate', methods=['POST'])
def regenerate_translation():
    """
    regenerate the flowchart translation with additional feedback which
    allows users to provide corrections when the initial translation is wrong
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        feedback = request.form.get('feedback', '')
        previous_edges_json = request.form.get('previous_edges', '[]')
        previous_edges = json.loads(previous_edges_json)
        
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        import time
        timestamp = str(int(time.time()))
        image_filename = f"flowchart_{timestamp}"
        
        # Save the original uploaded image
        original_path = os.path.join(RESULTS_DIR, f"{image_filename}_original.png")
        image.save(original_path)
        
        # Enhanced prompt with user feedback
        prompt = f"""Analyze this flowchart and identify ALL decision points.
        A decision point is any node that has MORE THAN ONE outgoing edge (i.e., multiple possible paths leaving it).

        Create edges that ONLY connect decision points to other decision points.
        - Skip over any nodes that have only one outgoing edge
        - Trace each branch from a decision point until you reach the NEXT decision point (or an endpoint like Start/End)
        - Include the branch label (Yes/No/etc.) that leads from one decision to the next

        For example, if the flow is: "Is A?" --Yes--> [Do X] --> "Is B?"
        The edge should be: source="Is A?", label="Yes", target="Is B?"

        Also include edges from "Start" to the first decision point, and from decision points to "End" where applicable.
        If a branch leads to a node with no further decision point after it, use "End" as the target.
        
        HANDLING DUPLICATE VERTEX NAMES:
        If the flowchart has multiple nodes with the same text (e.g., multiple "End" nodes at different positions),
        you MUST give each one a unique name by appending a number suffix.
        For example: "End_1", "End_2", "End_3" for three different End nodes.
        Use these unique names consistently in both the edges (source/target) and the vertices list.
        
        VERTEX POSITIONS:
        For each unique vertex that appears in the edges (including Start and all End nodes), provide:
        - label: The unique name of the vertex (must match source/target in edges exactly)
        - x: The approximate x coordinate of the vertex center (0-100 scale, where 0 is left edge, 100 is right edge)
        - y: The approximate y coordinate of the vertex center (0-100 scale, where 0 is top edge, 100 is bottom edge)
        
        PREVIOUS TRANSLATION (that needs correction):
        {previous_edges}
        
        USER FEEDBACK on what was wrong with the previous translation:
        {feedback}
        
        Please correct the edges based on this feedback."""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": Flowchart
            }
        )
        
        flowchart_object = Flowchart.model_validate_json(response.text)
        edges = [(edge.source, edge.label, edge.target) for edge in flowchart_object.edges]
        
        # Build vertex positions dictionary: label -> (x, y)
        vertex_positions = {v.label: (v.x, v.y) for v in flowchart_object.vertices}
        
        graph_filename = f"{image_filename}_graph"
        get_graph(edges, graph_name=graph_filename, vertex_positions=vertex_positions)
        
        graph_path = os.path.join(RESULTS_DIR, f"{graph_filename}.png")
        with open(graph_path, 'rb') as f:
            graph_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        with open(original_path, 'rb') as f:
            original_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            "success": True,
            "edges": edges,
            "vertex_positions": vertex_positions,
            "original_image": original_base64,
            "graph_image": graph_base64,
            "session_id": timestamp
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask API server...")
    print("API running at http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET  /api/health          - Check if API is running")
    print("  POST /api/translate       - Upload flowchart image and get edges")
    print("  POST /api/generate-paths  - Calculate edge coverage paths")
    print("  POST /api/regenerate      - Regenerate translation with feedback")
    app.run(debug=True, port=5000)
