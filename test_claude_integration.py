#!/usr/bin/env python3
"""
Test script for Claude API integration with GraphRAG system.
This tests the LLM decision-making function without requiring full dataset import.
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

def test_claude_api():
    """Test basic Claude API connectivity."""
    print("=" * 60)
    print("Testing Claude API Integration")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not found in environment")
        return False

    print(f"✓ API key found: {api_key[:20]}...")

    # Check model selection
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    print(f"✓ Model: {model}")

    # Initialize client
    try:
        client = Anthropic(api_key=api_key)
        print("✓ Anthropic client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    return client, model


def test_llm_decision():
    """Test the LLM decision-making function with sample data."""
    print("\n" + "=" * 60)
    print("Testing LLM Decision Function")
    print("=" * 60)

    client, model = test_claude_api()
    if not client:
        return False

    # Sample data mimicking the GraphRAG state
    current_nodes = ["n0:Entrance"]
    current_edges = []
    candidate_counts = [
        ("Kitchen", 245),
        ("Living_Dining", 198),
        ("Corridor", 156),
        ("Bathroom", 134),
        ("Bedroom", 128),
        ("Balcony", 67)
    ]
    house_type = "2 bedroom apartment"

    print(f"\nTest scenario:")
    print(f"  House type: {house_type}")
    print(f"  Current nodes: {current_nodes}")
    print(f"  Current edges: {current_edges}")
    print(f"  Top candidates: {candidate_counts[:3]}")

    # Build system prompt (same as in notebook)
    sys_prompt = (
        "You are designing a plausible house adjacency graph. "
        "Return ONLY valid JSON (no markdown, no extra text) with one of these actions:\n\n"
        "1) ADD a new node:\n"
        '   {"action": "ADD", "new_label": "Kitchen", "attach_to": "Entrance", "reasoning": "why"}\n\n'
        "2) CONNECT existing nodes:\n"
        '   {"action": "CONNECT", "node_a": "Kitchen", "node_b": "Living_Dining", "reasoning": "why"}\n\n'
        "3) STOP when the layout is complete:\n"
        '   {"action": "STOP", "reasoning": "why"}\n\n'
        "Rules:\n"
        "- Use exact labels from candidates or current_nodes\n"
        "- Ensure logical adjacencies (kitchen near living, bedrooms private)\n"
        "- Keep the graph connected\n"
        "- Return ONLY the JSON object"
    )

    # Build user payload
    user_payload = {
        "house_type": house_type,
        "current_nodes": current_nodes,
        "current_edges": current_edges,
        "candidate_counts": candidate_counts,
    }

    print(f"\n⏳ Calling Claude API...")

    try:
        # Call Claude API
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=0.3,
            system=sys_prompt,
            messages=[{
                "role": "user",
                "content": json.dumps(user_payload, indent=2)
            }]
        )

        print(f"✓ API call successful")
        print(f"  Tokens used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")

        # Extract response
        text = message.content[0].text.strip()
        print(f"\n📝 Raw response:\n{text}")

        # Parse JSON (handle markdown code blocks)
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        json_data = json.loads(text)
        print(f"\n✓ Valid JSON parsed")

        # Validate response structure
        if "action" not in json_data:
            print(f"✗ Missing 'action' field")
            return False

        action = json_data["action"]
        print(f"\n🎯 Decision:")
        print(f"  Action: {action}")

        if action == "ADD":
            print(f"  New node: {json_data.get('new_label', 'MISSING')}")
            print(f"  Connect to: {json_data.get('attach_to', 'MISSING')}")
            print(f"  Reasoning: {json_data.get('reasoning', 'MISSING')}")

            if "new_label" not in json_data or "attach_to" not in json_data:
                print(f"✗ Missing required fields for ADD action")
                return False

        elif action == "CONNECT":
            print(f"  Node A: {json_data.get('node_a', 'MISSING')}")
            print(f"  Node B: {json_data.get('node_b', 'MISSING')}")
            print(f"  Reasoning: {json_data.get('reasoning', 'MISSING')}")

            if "node_a" not in json_data or "node_b" not in json_data:
                print(f"✗ Missing required fields for CONNECT action")
                return False

        elif action == "STOP":
            print(f"  Reasoning: {json_data.get('reasoning', 'MISSING')}")
        else:
            print(f"✗ Invalid action: {action}")
            return False

        print(f"\n✓ Response structure valid")
        return True

    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse JSON: {e}")
        print(f"  Response was: {text}")
        return False
    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False


def test_multi_step_scenario():
    """Test multiple decision steps to simulate the GraphRAG loop."""
    print("\n" + "=" * 60)
    print("Testing Multi-Step Decision Scenario")
    print("=" * 60)

    client, model = test_claude_api()
    if not client:
        return False

    # Simulate 3 steps of graph building
    scenarios = [
        {
            "step": 1,
            "nodes": ["n0:Entrance"],
            "edges": [],
            "candidates": [("Kitchen", 245), ("Living_Dining", 198), ("Corridor", 156)]
        },
        {
            "step": 2,
            "nodes": ["n0:Entrance", "n1:Kitchen"],
            "edges": [("n0:Entrance", "n1:Kitchen")],
            "candidates": [("Living_Dining", 198), ("Corridor", 156), ("Bedroom", 128)]
        },
        {
            "step": 3,
            "nodes": ["n0:Entrance", "n1:Kitchen", "n2:Living_Dining"],
            "edges": [("n0:Entrance", "n1:Kitchen"), ("n1:Kitchen", "n2:Living_Dining")],
            "candidates": [("Bedroom", 128), ("Bathroom", 134), ("Balcony", 67)]
        }
    ]

    sys_prompt = (
        "You are designing a plausible house adjacency graph. "
        "Return ONLY valid JSON (no markdown, no extra text) with one of these actions:\n\n"
        "1) ADD a new node:\n"
        '   {"action": "ADD", "new_label": "Kitchen", "attach_to": "Entrance", "reasoning": "why"}\n\n'
        "2) CONNECT existing nodes:\n"
        '   {"action": "CONNECT", "node_a": "Kitchen", "node_b": "Living_Dining", "reasoning": "why"}\n\n'
        "3) STOP when the layout is complete:\n"
        '   {"action": "STOP", "reasoning": "why"}\n\n'
        "Return ONLY the JSON object"
    )

    for scenario in scenarios:
        print(f"\n--- Step {scenario['step']}/3 ---")
        print(f"Current nodes: {scenario['nodes']}")
        print(f"Current edges: {scenario['edges']}")

        user_payload = {
            "house_type": "2 bedroom apartment",
            "current_nodes": scenario['nodes'],
            "current_edges": scenario['edges'],
            "candidate_counts": scenario['candidates'],
        }

        try:
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                temperature=0.3,
                system=sys_prompt,
                messages=[{"role": "user", "content": json.dumps(user_payload, indent=2)}]
            )

            text = message.content[0].text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

            json_data = json.loads(text)
            action = json_data["action"]

            if action == "ADD":
                print(f"✓ Added '{json_data['new_label']}' connected to '{json_data['attach_to']}'")
            elif action == "CONNECT":
                print(f"✓ Connected '{json_data['node_a']}' to '{json_data['node_b']}'")
            elif action == "STOP":
                print(f"⊗ Stopped: {json_data['reasoning']}")
                break

        except Exception as e:
            print(f"✗ Step {scenario['step']} failed: {e}")
            return False

    print(f"\n✓ Multi-step scenario completed successfully")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CLAUDE API INTEGRATION TEST SUITE")
    print("=" * 60)

    # Test 1: Basic API connectivity
    success = test_claude_api()
    if not success:
        print("\n❌ Basic API test failed - check your .env file")
        exit(1)

    # Test 2: Single LLM decision
    success = test_llm_decision()
    if not success:
        print("\n❌ LLM decision test failed")
        exit(1)

    # Test 3: Multi-step scenario
    success = test_multi_step_scenario()
    if not success:
        print("\n❌ Multi-step scenario failed")
        exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nClaude API integration is working correctly!")
    print("You can now run the Jupyter notebook: Kuzu_GraphRAG_New.ipynb")
    print("=" * 60)
