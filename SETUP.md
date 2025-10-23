# Setup Guide: GraphRAG with Claude API

This guide walks you through setting up the GraphRAG system with Claude API integration.

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (get one at https://console.anthropic.com/)
- Swiss dwelling dataset at `/Users/td3003/import_export/msd_json/`

## Installation Steps

### 1. Install Python Dependencies

From the project root directory, run:

```bash
pip install -r requirements.txt
```

This installs:
- `topologicpy>=0.6.0` - Topological graph processing
- `kuzu>=0.5.0` - Graph database
- `pydantic>=2.0.0` - Data validation
- `anthropic>=0.39.0` - Claude API client
- `python-dotenv>=1.0.0` - Environment variable management
- `numpy`, `scipy`, `matplotlib`, `networkx` - Data processing and visualization
- `jupyter`, `ipywidgets` - Notebook environment

### 2. Configure API Key

#### Step 1: Get your Anthropic API key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-ant-...`)

#### Step 2: Create .env file

Copy the example environment file:

```bash
cp .env.example .env
```

#### Step 3: Edit .env file

Open `.env` in a text editor and replace `your_api_key_here` with your actual API key:

```bash
# Anthropic Claude API Key
ANTHROPIC_API_KEY=sk-ant-api03-...your_actual_key_here...

# Optional: Model selection (default: claude-sonnet-4-20250514)
# Options: claude-sonnet-4-20250514, claude-opus-4-20250514, claude-3-5-sonnet-20241022
CLAUDE_MODEL=claude-sonnet-4-20250514
```

**Important**: Never commit the `.env` file to git. It's already in `.gitignore`.

### 3. Verify Dataset Location

Ensure the Swiss dwelling dataset is available at:

```
/Users/td3003/import_export/msd_json/
├── graphs/        # 4,572 graph JSON files
└── geometries/    # 4,572 geometry JSON files
```

If your dataset is in a different location, you'll need to update the path in the notebook configuration cell.

## Running the Notebook

### 1. Start Jupyter

From the project root:

```bash
jupyter notebook
```

### 2. Open the Notebook

Navigate to and open `Kuzu_GraphRAG_New.ipynb`

### 3. Run Initial Setup Cells

Execute the first few cells in order:

1. **Imports Cell** - Loads all required libraries
2. **Claude API Setup Cell** (1722efbb) - Initializes Claude client
3. **Database Configuration Cell** (eb91a30e) - Creates Kuzu database
4. **Dataset Import Cell** (b59b2e1a) - Loads Swiss dwelling graphs

You should see output confirming:
```
✓ GraphRAG functions loaded (using Claude API)
✓ Claude model: claude-sonnet-4-20250514
✓ API key configured: True
✓ Kuzu database initialized at: ./demo_kuzu
✓ Imported 4572 graphs from Swiss dwelling dataset
```

### 4. Run GraphRAG Generation

Execute the main generation loop cell to create a new apartment layout:

```python
# Example: Generate a 2-bedroom apartment
house_type = "2 bedroom apartment"
max_steps = 20

graphrag_build_loop(
    mgr=mgr,
    house_type=house_type,
    max_steps=max_steps
)
```

## Troubleshooting

### API Key Not Found

**Error**: `Claude API not available, using heuristic`

**Solution**:
1. Verify `.env` file exists in project root
2. Check that `ANTHROPIC_API_KEY` is set correctly (no spaces around `=`)
3. Restart the Jupyter kernel: Kernel → Restart

### Invalid API Key

**Error**: `Error calling Claude API: 401 Unauthorized`

**Solution**:
1. Verify your API key is correct and active at https://console.anthropic.com/
2. Check for extra spaces or newlines in `.env` file
3. Ensure the key starts with `sk-ant-`

### Dataset Not Found

**Error**: `FileNotFoundError` or `0 graphs imported`

**Solution**:
1. Verify dataset path: `ls /Users/td3003/import_export/msd_json/graphs`
2. Update the `json_folder` path in cell b59b2e1a if dataset is elsewhere
3. Ensure you have read permissions on the dataset directory

### Kuzu Database Error

**Error**: `Database already exists` or corruption errors

**Solution**:
```bash
# Delete and recreate database
rm -rf ./demo_kuzu
```

Then re-run the database initialization cells.

### Rate Limits

**Error**: `429 Too Many Requests`

**Solution**:
1. Add delays between API calls (increase `time.sleep()` in loop)
2. Use a lower tier model (e.g., `claude-3-5-sonnet-20241022` instead of `claude-sonnet-4`)
3. Check your API usage at https://console.anthropic.com/

## Model Selection

You can change the Claude model by editing `.env`:

```bash
# Fastest, most cost-effective (recommended for development)
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Most capable (recommended for production)
CLAUDE_MODEL=claude-sonnet-4-20250514

# Highest quality (most expensive)
CLAUDE_MODEL=claude-opus-4-20250514
```

**Model Comparison**:
- **Sonnet 4**: Best balance of quality and speed for architectural reasoning
- **Sonnet 3.5**: Faster, cheaper, good for testing and iteration
- **Opus 4**: Highest quality, use for final production runs

## Understanding the Output

The GraphRAG loop will print progress for each step:

```
--- Step 1/20 ---
Current nodes: ['n0:Entrance']
Candidates: [('Kitchen', 245), ('Living_Dining', 198), ('Corridor', 156), ...]

LLM chose: ADD node Kitchen connected to Entrance
✓ Added 'Kitchen' (node n1) connected to 'Entrance'

--- Step 2/20 ---
Current nodes: ['n0:Entrance', 'n1:Kitchen']
Current edges: [('n0:Entrance', 'n1:Kitchen')]
...
```

The loop continues until:
- All required rooms are added (kitchen, bathrooms, bedrooms)
- Maximum steps reached
- LLM decides the apartment is complete

## Next Steps

After successful setup and test run:

1. Review `PHASE1_ANALYSIS.md` for implementation roadmap
2. Proceed with Action P1.1: Add graph validation
3. Implement area constraints (Action P1.2)
4. Test with diverse apartment types (Action P1.4)

## Support

For issues specific to:
- **Claude API**: https://docs.anthropic.com/
- **TopologicPy**: https://github.com/wassimj/topologicpy
- **Kuzu**: https://kuzudb.com/docs/

---

**Last Updated**: 2025-10-23
**Action**: P0.1 - Claude API Integration
**Status**: Complete
