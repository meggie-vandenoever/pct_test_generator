# Flowchart Test Path Generator

A web application that analyzes flowchart images and generates test paths for test level depth 1 coverage

## How It Works

```
┌─────────────────────┐                    ┌─────────────────────┐
│   Next.js Frontend  │  ◄───HTTP───►     │  Python Flask API   │
│   localhost:3000    │                    │  localhost:5000     │
└─────────────────────┘                    └─────────────────────┘
         │                                           │
         │                                           │
         ▼                                           ▼
    ┌─────────┐                              ┌─────────────┐
    │ Browser │                              │ Gemini AI   │
    │  User   │                              │ + graphviz  │
    └─────────┘                              └─────────────┘
```

1. **Upload**: User uploads a flowchart image
2. **Translate**: Gemini AI extracts decision points and edges
3. **Visualize**: Graphviz generates a graph visualization
4. **Compare**: User reviews and accepts/rejects the translation
5. **Generate**: PathGenerator calculates test level depth 1 coverage test paths
6. **Display**: Shows color-coded paths through the flowchart

## Prerequisites

- **Node.js** (v18+) - for the frontend
- **Python** (3.10+) - for the backend
- **Graphviz** - for graph visualization (install from https://graphviz.org/download/)
- **Google Gemini API Key** - for AI analysis

## Setup

### 1. Backend Setup

```bash
# Navigate to the backend folder
cd flowchart-app/backend

# Install dependencies (use your existing virtual environment)
pip install -r requirements.txt

# Copy the .env.example and add your API key
copy .env.example .env
# Then edit .env and add your GOOGLE_API_KEY
```

### 2. Frontend Setup

```bash
# Navigate to the frontend folder
cd flowchart-app

# Install dependencies (already done)
npm install
```

## Running the Application

### Start the Backend (Terminal 1)

```bash
cd flowchart-app/backend
python api.py
```

The API will start at `http://localhost:5000`

### Start the Frontend (Terminal 2)

```bash
cd flowchart-app
npm run dev
```

The web app will open at `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Drag and drop a flowchart image (or click to browse)
3. Click "Analyze Flowchart"
4. Review the generated graph:
   - **Accept** if it's correct → proceeds to generate test paths
   - **Reject** if it's wrong → provide feedback and regenerate
5. View the edge coverage test paths with color-coded visualization

## Project Structure

```
pct_test_generator/
├── backend/                 # Python Flask API
│   ├── api.py              # API endpoints
│   ├── graph.py            # Graph visualization & PathGenerator
│   ├── models.py           # Pydantic models
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
│
├── src/                     # Next.js frontend
│   ├── app/
│   │   ├── page.tsx        # Main page component
│   │   ├── layout.tsx      # Root layout
│   │   └── globals.css     # Global styles
│   │
│   └── components/
│       ├── ImageUpload.tsx     # Drag-and-drop file upload
│       ├── GraphComparison.tsx # Side-by-side comparison
│       └── PathDisplay.tsx     # Test path visualization
│
├── results/                 # Generated images (created at runtime)
├── package.json            # Node.js dependencies
└── README.md
```

## PathGenerator Algorithm

The `PathGenerator` class in `backend/graph.py` is the core of the application. Given a list of edges extracted from a flowchart, it calculates a near-minimal set of test paths needed for **test level depth 1 coverage** — meaning every edge in the flowchart is covered by at least one test path.

### Step 1: Find all paths (`get_all_paths`)

A **depth-first search (dfs)** explores every possible route from `Start` to an endpoint. A shared `visited_states` set tracks which `(node, path-so-far)` combinations have already been explored across all branches of the recursion. This prevents the algorithm from re-entering the same state and ensures loops are traversed at most once per path.

### Step 2: Select the minimum set of paths (`find_max_new_coverage`)

A **greedy algorithm** selects a near-minimal number of paths from the full set to achieve edge coverage.

Finding the true minimum is an instance of the **set cover problem**, which is NP-hard — meaning no known algorithm solves it efficiently for all inputs. The greedy approach is the standard approximation: it is guaranteed to find a solution within a logarithmic factor of the true optimum, and in practice performs well on typical flowchart sizes.

1. Score every candidate path by how many **not-yet-covered** edges it contains.
2. Pick the path with the highest score. When scores are tied, prefer the **shorter path** (fewer edges) to avoid unnecessary loops.
3. Mark those edges as covered and remove the selected path from the candidate pool.
4. Repeat until all edges are covered.

```
All paths ──► score by new edge coverage
                       │
                       ▼
             pick highest score
          (shortest path on tie) ──► add to selected paths
                       │
                       ▼
             remove covered edges
                       │
                  all covered? ──Yes──► done
                       │
                      No
                       │
                       └──────────────┘ (repeat)
```

## API Endpoints

| Method | Endpoint              | Description                   |
| ------ | --------------------- | ----------------------------- |
| GET    | `/api/health`         | Health check                  |
| POST   | `/api/translate`      | Upload image and get edges    |
| POST   | `/api/generate-paths` | Calculate edge coverage paths |
| POST   | `/api/regenerate`     | Regenerate with feedback      |
