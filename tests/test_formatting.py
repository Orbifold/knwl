"""
Simple test to verify the formatting system works.
Run this after installing rich: uv pip install rich
"""


def test_basic_formatting():
    """Test basic formatting functionality."""
    print("\nTesting basic formatting...")
    
    try:
        from knwl.models import KnwlNode
        from knwl.format import print_knwl, format_knwl
        
        # Create a test node
        node = KnwlNode(
            name="Test Node",
            type="Test",
            description="A test node for validation"
        )
        
        print("\n--- Terminal Format ---")
        print_knwl(node)
        
        print("\n--- HTML Format ---")
        html = format_knwl(node, format_type="html")
        print(html[:200] + "...")
        
        print("\n--- Markdown Format ---")
        md = format_knwl(node, format_type="markdown")
        print(md)
        
        print("\n✓ Basic formatting works!")
        return True
        
    except Exception as e:
        print(f"✗ Formatting failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_formatting():
    """Test graph formatting."""
    print("\nTesting graph formatting...")
    
    try:
        from knwl.models import KnwlNode, KnwlEdge, KnwlGraph
        from knwl.format import print_knwl
        
        # Create test graph
        nodes = [
            KnwlNode(name="Node A", type="Type1"),
            KnwlNode(name="Node B", type="Type2"),
        ]
        edges = [
            KnwlEdge(
                source_id=nodes[0].id,
                target_id=nodes[1].id,
                type="CONNECTS"
            )
        ]
        graph = KnwlGraph(nodes=nodes, edges=edges, keywords=["test", "graph"])                
        print_knwl(graph, compact=False)
        
        return True
        
    except Exception as e:
        print(f"✗ Graph formatting failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("KNWL FORMATTING SYSTEM - VALIDATION TESTS")
    print("="*70)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Basic Formatting", test_basic_formatting()))
    results.append(("Graph Formatting", test_graph_formatting()))
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
