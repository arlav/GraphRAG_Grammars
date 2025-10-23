Topologic Graph Retrieval Augmented Generation + Grammars

## Executive Summary

This document outlines a comprehensive development plan for building a **Topologic GraphRAg system including shape** that generate layout graphs out of a graph database and then the layout itself.

Based on analysis of existing code and documentation, this project will implement a **jupyter notebook series** with distinct steps ensuring high maintainability, testability, and extensibility.


## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale

## System Architecture

- use pydantic
- use topologicpy 
- use kuzu
- use streamlit

## Project Vision

Create a production-ready application that bridges the gap between:
- **SciKit Geometry** (Geometry Procdessing)
- **COMPAS framework** (Computational design)
- **Graph Analytics** (TopologicPy processing)
- **Graph Storage** (Kuzu graph database)
- **Blockchain Integration** (Ethereum tokenization)


## Codebases to use

- [TopologicPy](https://github.com/wassimj/topologicpy)
- [Kuzu](https://github.com/kuzudb/kuzu)
- [SciKit](https://github.com/scikit-geometry/scikit-geometry)
- [compas](Main library of the COMPAS framework and CAD integrations for Rhino/GH and Blender.)

## Previous files
- check the /previous files folders for good examples


## Current State Analysis

## Schema to use


### Existing Assets
- **README.md**: Well-defined architecture and feature requirements
- **Previous Work**: 
  - `graph_topo.py`: Comprehensive IFC processing with TopologicPy (1,465 lines)
  - `IFC_FIXES.md`: Detailed analysis of processing issues and solutions
  - `JSON_LD_Documentation.md`: JSON-LD export specifications -use these for the RDF exports
  - `GraphByIFCPath.ipynb`: Working Jupyter notebooks
  - `RDF_BOT_Export`: RDF export example
  - `RDF_BOT_Import`: RDF import example
  - `graph_topo_ld_graph.py` : Linked Data Schema example
  
### Key Insights from Previous Work


## Detailed Development Plan

### Phase 1: Switch the Jupyter notebook to using Claude

#### 1.1 Switch the Jupyter notebook to using Claude
#### 1.2
#### 1.3 Create a test run and validate
#### 1.4 go beyond rooms, Develop Graphs that track rooms, and walls, and openings- create a classification of nodes (Rooms, Walls, Openings)

### Phase 2: Develop a Graph to Shape grammar

#### 2.1 Develop a library of parametric shapes to use
#### 2.2 Assign a shape to each node a particular room function and visualise (squares, rectangles)
#### 2.3 Align the shapes so that the lines touch
#### 2.4 Create Variation with parameters
#### 2.2 Topology Engine with TopologicPy Graph Methods

### Phase 3: 3d development



