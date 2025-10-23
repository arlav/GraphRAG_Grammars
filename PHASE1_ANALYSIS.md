# Phase 1: GraphRAG System Analysis & Implementation Plan

## Dataset Overview: Swiss Dwelling Dataset

### Location
```
/Users/td3003/import_export/msd_json/
```

### Structure
```
msd_json/
├── graphs/        # 4,572 graph JSON files
├── geometries/    # 4,572 geometry JSON files
└── images/        # Floor plan images (optional)

Total: 9,144 JSON files (4,572 building floors)
```

### Graph File Format (`*_graph.json`)

Each graph file contains:

#### 1. **Properties** (Building-level metadata)
```json
{
  "properties": {
    "building_id": 1735,
    "floor_id": 7723,
    "plan_id": 4923,
    "site_id": 794,
    "elevation": 0.0,
    "height": 2.6,
    "ml_type": "train",
    "unit_usage": "RESIDENTIAL"
  }
}
```

#### 2. **Vertices** (Rooms/Spaces)
Each vertex represents a room with rich metadata:

```json
"Vertex_0001": {
  // Core identification
  "node_name": "Bedroom",           // Human-readable room name
  "roomtype": "Bedroom",            // Room classification
  "node_type": 0,                   // Numeric type code
  "node_color": "#1f77b4",         // Visualization color

  // Spatial properties
  "area": 13.32826,                // Area in m²
  "x": 7.261717,                   // Centroid X coordinate
  "y": -16.600271,                 // Centroid Y coordinate
  "z": 0.0,                        // Centroid Z coordinate (floor elevation)
  "height": 2.6,                   // Ceiling height in meters

  // Geometry (polygon boundary)
  "geometry": [
    [4.646343, -16.360176],
    [4.65964, -16.381818],
    [8.284688, -14.154588],
    // ... more vertices
  ],
  "geom": "POLYGON ((4.6463... ))", // WKT format

  // Apartment/unit context
  "apartment_id": "fe8e0e6e2e5118851d085ebb8edfac39",
  "apartment_number": 1,
  "apartment_color": "#FF0000",
  "unit_id": 37719.0,
  "unit_usage": "RESIDENTIAL",

  // Zoning classification
  "zone_name": "Zone1",             // Zone identifier
  "zone_type": 1,                   // Zone type code
  "zone_color": "#ff7f0e",         // Zone visualization color
  "zoning": "Zone1",

  // Building hierarchy
  "building_id": 1735,
  "floor_id": 7723,
  "plan_id": 4923,
  "site_id": 794,
  "area_id": 466373.0,
  "elevation": 0.0,

  // Entity classification
  "entity_type": "area",
  "entity_subtype": "ROOM"
}
```

**Key Room Types Found**:
- `ROOM` (generic bedroom)
- `LIVING_DINING` (combined living/dining)
- `KITCHEN`
- `BATHROOM`
- `CORRIDOR`
- `BALCONY`
- `STOREROOM`
- `ELEVATOR` / `STAIRS` (circulation)

**Zone Classifications**:
- `Zone1`: Private spaces (bedrooms)
- `Zone2`: Semi-private (living, dining, kitchen)
- `Zone3`: Services (bathroom, storage, stairs)
- `Zone4`: Exterior (balconies)

#### 3. **Edges** (Adjacencies/Connections)
```json
"Edge_00": {
  "source": "Vertex_0000",         // Source room ID
  "target": "Vertex_0002",         // Target room ID
  "connectivity": "door",          // Connection type
  "edge_width": 4                  // Opening width (meters)
}
```

**Connection Types**:
- `door`: Standard door between rooms
- `passage`: Open passage (no door)
- `entrance`: Main apartment entrance

### Data Characteristics

#### Dataset Scale
- **4,572 floor plans** from Swiss residential buildings
- **~35 rooms per floor** (average, from sample)
- **~34 edges per floor** (average)
- **Mix of apartment types**: 1BR, 2BR, 3BR, 4BR, studios
- **Multi-unit floors**: 2-4 apartments per floor common

#### Room Statistics (from sample 7723)
- Smallest room: 1.35m² (corridor segment)
- Largest room: 36.27m² (living/dining)
- Average bedroom: 13-15m²
- Average bathroom: 5-6m²
- Typical ceiling height: 2.6m

#### Metadata Richness
✅ **Available**:
- Room type classification
- Accurate area measurements
- 2D polygon geometry (for visualization)
- Apartment grouping
- Zone classifications
- Connection types (door/passage/entrance)

❌ **Not Available** (for GraphRAG):
- Room adjacency is only encoded via edges (no spatial reasoning needed)
- No furniture or fixture data
- No text descriptions
- No building codes or regulations

---

## Current Implementation Analysis

### Existing Notebook: `Kuzu_GraphRAG_New.ipynb`

#### What It Does ✅

1. **Data Loading** (`load_topologic_graph()`)
   - Reads JSON files from Swiss dataset
   - Extracts vertices and edges
   - Preserves all metadata in `props`
   - Handles missing fields gracefully

2. **Kuzu Database Integration**
   - Schema: Graph → Vertices → Edges
   - Stores all room properties as JSON
   - Bidirectional edges for undirected graphs
   - Clean separation of graph instances

3. **GraphRAG Core Loop** (`graphrag_build_loop()`)
   - **Seed**: Copies best example from dataset
   - **Candidate Generation**: Queries all graphs for neighbor patterns
   - **LLM Decision**: GPT-4o suggests ADD node or CONNECT nodes
   - **Execution**: Updates working graph in Kuzu
   - **Snapshots**: Saves TopologicPy Graph at each step

4. **Property Inheritance**
   - New nodes copy full props from best matching example
   - Includes area, zone, apartment context
   - Adds provenance metadata

#### Current Workflow

```
1. Import dataset → Kuzu
   ├─ Parse JSON (vertices + edges)
   ├─ Extract labels from node_name/roomtype
   └─ Store in Kuzu with full metadata

2. Initialize working graph
   ├─ Query: "Find best example of 'Entrance'"
   ├─ Copy: area, zone, geometry props
   └─ Create: Vertex "n0" in working graph

3. Iterative loop (max_steps=20)
   ├─ Query: Get current nodes + edges
   ├─ Build: Global candidate list (frequency-ranked)
   │   └─ "For nodes in current graph, what neighbors appear in dataset?"
   ├─ LLM: Choose action
   │   ├─ ADD: "Kitchen" connected to "Entrance"
   │   ├─ CONNECT: "Living" to "Bedroom"
   │   └─ STOP: "All essential rooms present"
   ├─ Execute: Update Kuzu graph
   └─ Snapshot: Export to TopologicPy Graph

4. Output
   └─ TopologicPy Graph with nodes + edges (no geometry yet)
```

---

## Phase 1 Gaps & Improvement Opportunities

### 🔴 Critical Issues

#### 1. **No Validation of Generated Graphs**
- **Problem**: LLM can create implausible layouts
- **Example**: Kitchen not connected to living room, bathroom unreachable
- **Impact**: Phase 2 shape grammar will fail on invalid topologies

**Solution**:
- Add graph validation rules
- Check connectivity (all rooms reachable)
- Validate apartment completeness (kitchen + bathroom required)

#### 2. **Limited Diversity in Generation**
- **Problem**: Always starts from "Entrance", follows similar patterns
- **Impact**: Generated apartments look similar

**Solution**:
- Support multiple seed strategies (start from living room, kitchen, etc.)
- Add diversity prompts to LLM
- Sample from different example types

#### 3. **No Size/Area Constraints**
- **Problem**: Props include area, but no validation
- **Impact**: Total area could be unrealistic (10m² apartment or 500m²)

**Solution**:
- Add area budget constraints
- Validate total area against apartment type (2BR ≈ 60-80m²)

### 🟡 Medium Priority

#### 4. **Inefficient Candidate Querying**
- **Current**: Queries all 4,572 graphs every iteration
- **Impact**: Slow for large datasets

**Solution**:
- Pre-compute neighbor frequency table
- Cache candidate lists
- Use graph sampling (query subset of graphs)

#### 5. **LLM Prompt Could Be Better**
- **Current**: Generic prompt, no architectural knowledge
- **Impact**: Suboptimal room arrangements

**Solution**:
- Add architectural rules to prompt
- Include Swiss building codes
- Provide good/bad examples

#### 6. **No Support for Multi-Room Types**
- **Current**: One room type per node
- **Dataset**: Has "LIVING_DINING" combined spaces

**Solution**:
- Support combined room types
- Allow flexible room type assignment

### 🟢 Nice to Have

#### 7. **No Visualization During Generation**
- **Current**: Must run separately after generation
- **Impact**: Hard to debug/understand process

**Solution**:
- Add mid-generation visualization
- Show abstract graph (node-link diagram)

#### 8. **Limited Apartment Type Control**
- **Current**: Only `house_type` parameter ("2 bedroom apartment")
- **Impact**: Can't specify area budget, luxury level, etc.

**Solution**:
- Add more control parameters
- Support style constraints ("compact", "spacious", "luxury")

---

## Phase 1 Implementation Plan

### Goals
1. ✅ **Robust**: Validate generated graphs, handle edge cases
2. ✅ **Flexible**: Support diverse apartment types and styles
3. ✅ **Fast**: Optimize Kuzu queries, cache results
4. ✅ **Documented**: Clear code, comprehensive tests

### Action Items (Priority Order)

#### 🔴 **Critical** (Must Have for Phase 2)

**Action P0.1**: chatGPT to Claude
- [ ] Transform the jupyter notebook to use claude.ai instead of chatGPT
- [ ] Create .env that will protect the claude keys
 
**Action P1.1**: Add graph validation
- [ ] Implement connectivity checker (all rooms reachable)
- [ ] Add completeness validator (required rooms present)
- [ ] Check for isolated nodes
- [ ] Validate against apartment type constraints
- [ ] Reject invalid graphs, retry with different LLM prompt

**Action P1.2**: Implement area constraints
- [ ] Add total area budget parameter
- [ ] Track cumulative area during generation
- [ ] Warn LLM when approaching budget limit
- [ ] Validate final area against apartment type

**Action P1.3**: Improve property inheritance
- [ ] Copy area constraints from similar rooms
- [ ] Adjust area based on apartment type
- [ ] Preserve zone classifications
- [ ] Add metadata for traceability

**Action P1.4**: Test with diverse apartment types
- [ ] Generate 1BR, 2BR, 3BR, 4BR, studio apartments
- [ ] Test with different starting seeds
- [ ] Validate against Swiss dataset distributions
- [ ] Document failure cases

#### 🟡 **Medium Priority** (Improves Quality)

**Action P1.5**: Optimize Kuzu queries
- [ ] Pre-compute neighbor frequency tables
- [ ] Cache candidate lists
- [ ] Implement incremental updates
- [ ] Benchmark query performance

**Action P1.6**: Enhance LLM prompt
- [ ] Add architectural design principles
- [ ] Include Swiss building code constraints
- [ ] Provide good/bad layout examples
- [ ] Add reasoning step (explain why action chosen)

**Action P1.7**: Support combined room types
- [ ] Parse "LIVING_DINING" as two functions
- [ ] Allow flexible type assignment
- [ ] Update candidate querying logic

**Action P1.8**: Add generation parameters
- [ ] Area budget (m²)
- [ ] Style ("compact", "spacious", "luxury")
- [ ] Required rooms (e.g., "must have balcony")
- [ ] Seed strategy ("start from living", "start from entrance")

#### 🟢 **Nice to Have** (Polish)

**Action P1.9**: Mid-generation visualization
- [ ] Add NetworkX graph visualization
- [ ] Show after each iteration
- [ ] Highlight new nodes/edges
- [ ] Display metadata (area, zone)

**Action P1.10**: Batch generation & analysis
- [ ] Generate 100+ apartments
- [ ] Compute diversity metrics
- [ ] Compare to dataset distributions
- [ ] Generate analysis report

**Action P1.11**: Export to multiple formats
- [ ] JSON (TopologicPy format)
- [ ] CSV (for analysis)
- [ ] GML/GraphML (for network tools)
- [ ] Markdown report

**Action P1.12**: Documentation & examples
- [ ] Document all functions
- [ ] Create tutorial notebook
- [ ] Add usage examples
- [ ] Write architecture guide

---

## Testing Strategy

### Unit Tests
```python
# Test graph validation
def test_connectivity_checker():
    # Valid: all rooms connected
    # Invalid: isolated room
    pass

def test_completeness_validator():
    # Valid: kitchen + bathroom + bedrooms
    # Invalid: missing kitchen
    pass

# Test property inheritance
def test_area_inheritance():
    # Bedroom should get 12-15m² from examples
    pass

# Test Kuzu operations
def test_candidate_query():
    # Query should return frequency-ranked list
    pass
```

### Integration Tests
```python
def test_full_generation_pipeline():
    # Generate 2BR apartment
    # Validate structure
    # Check area constraints
    pass

def test_diverse_apartment_types():
    # 1BR, 2BR, 3BR, 4BR, studio
    # All should be valid
    pass
```

### Dataset Tests
```python
def test_swiss_dataset_loading():
    # Load all 4,572 graphs
    # Verify no errors
    # Check metadata completeness
    pass
```

---

## Success Metrics

### Phase 1 Complete When:

1. **Robustness** ✅
   - 100% of generated graphs pass validation
   - No isolated rooms
   - All apartments have kitchen + bathroom

2. **Diversity** ✅
   - Can generate 10+ distinct apartment types
   - Starting from different seeds produces different results
   - Area distributions match Swiss dataset

3. **Performance** ✅
   - Generate 10-room apartment in < 60 seconds
   - Kuzu queries return in < 1 second

4. **Quality** ✅
   - 80%+ of generated graphs are architecturally plausible
   - LLM makes reasonable room connections
   - Area constraints respected

---

## Next Steps

1. **Review current notebook** (`Kuzu_GraphRAG_New.ipynb`)
   - Run end-to-end generation
   - Identify immediate issues
   - Document current behavior

2. **Implement critical fixes** (P1.1 - P1.4)
   - Add validation
   - Add area constraints
   - Test with diverse types

3. **Optimize & enhance** (P1.5 - P1.8)
   - Improve queries
   - Better prompts
   - More control

4. **Polish & document** (P1.9 - P1.12)
   - Visualization
   - Batch generation
   - Comprehensive docs

5. **Prepare for Phase 2**
   - Export validated graphs
   - Document graph structure
   - Identify edge cases for shape grammar

---

**Last Updated**: 2025-10-23
**Dataset**: Swiss Multi-Storey Dwelling (4,572 floors)
**Current Status**: Analysis complete, ready for implementation
