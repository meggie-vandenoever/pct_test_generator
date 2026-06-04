# Flowchart Test Path Generator

A web application that analyzes flowchart images and generates test paths for configurable test depth level coverage (1, 2, or higher)

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
5. **Generate**: PathGenerator calculates test paths for the specified test depth level
6. **Display**: Shows color-coded paths through the flowchart

## Test Depth Levels

The test depth level determines the coverage granularity:

| Level | Coverage Requirement                           | Description                               |
| ----- | ---------------------------------------------- | ----------------------------------------- |
| 1     | Every **edge** is covered                      | Basic edge coverage                       |
| 2     | Every **pair of consecutive edges** is covered | Ensures all 2-step transitions are tested |
| N     | Every **N consecutive edges** are covered      | Higher confidence in sequential behavior  |

### Why Higher Test Depth Levels Matter

Consider a flowchart with a loop at node A:

```
Start → A → (loop back to A) or (exit to B) → End
```

- **Test depth level 1**: Only requires that the loop edge `A→A` is taken at least once.
- **Test depth level 2**: Requires testing `(A→A, A→A)` — taking the loop twice in a row — to verify the loop behaves correctly on repeated iterations.

Higher test depth levels provide more confidence that consecutive decision combinations work correctly together.

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

The `PathGenerator` class in `backend/graph.py` is the core of the application. Given a list of edges extracted from a flowchart and a test depth level N, it calculates a near-minimal set of test paths needed for **test depth level N coverage** — meaning every sequence of N consecutive edges in the flowchart is covered by at least one test path.

### Step 1: Find all paths (`get_all_paths`)

A **depth-first search (dfs)** explores every possible route from `Start` to an endpoint. The algorithm uses **N-tuple state tracking** to control loop exploration:

- **State definition**: `(current_node, set of N-consecutive-edge-tuples seen so far)`
- **Key insight**: Instead of tracking individual edges (which would block loops after one iteration), we track tuples of N consecutive edges

#### How N-tuple tracking enables loop coverage

For test depth level 2 with a self-loop at node A:

1. After taking loop once: state = `(A, {(Start→A, A→A)})`
2. After taking loop twice: state = `(A, {(Start→A, A→A), (A→A, A→A)})` ← **new tuple added, different state!**
3. After taking loop three times: state = `(A, {(Start→A, A→A), (A→A, A→A)})` ← **no new tuple, same state → blocked**

This naturally caps loop repetitions at exactly what's needed for N-coverage.

#### Helper functions

- **`extract_ntuples_from_path(path)`**: Extracts all N-tuples that actually appear consecutively in a specific path (sliding window). Used for state tracking.
- **`get_all_possible_ntuples(edges)`**: Generates all theoretically possible N-tuples based on edge connectivity. Used to define coverage requirements.

### Step 2: Select set of paths (`find_max_new_coverage`)

A **greedy algorithm** selects a near-minimal number of paths from the full set to achieve N-tuple coverage.

Finding the true minimum is an instance of the **set cover problem**, which is NP-hard, meaning no known algorithm solves it efficiently for all inputs. The greedy approach is the standard approximation: it is guaranteed to find a solution within a logarithmic factor of the true optimum, and in practice performs well on typical flowchart sizes.

1. Score every candidate path by how many **not-yet-covered N-tuples** it contains.
2. Pick the path with the highest score. When scores are tied, prefer the **shorter path** (fewer edges) to avoid unnecessary loops.
3. Mark those N-tuples as covered and remove the selected path from the candidate pool.
4. Repeat until all N-tuples are covered.

```
All paths ──► score by new N-tuple coverage
                       │
                       ▼
             pick highest score
          (shortest path on tie) ──► add to selected paths
                       │
                       ▼
            remove covered N-tuples
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
