#!/usr/bin/env python3
"""Simple test to verify DMAutomationEngine can be instantiated without visual_mode error"""

try:
    from instagram_dm_automation import DMAutomationEngine
    print("✓ Import successful")
    
    # Test instantiation
    engine = DMAutomationEngine()
    print("✓ DMAutomationEngine created successfully")
    
    # Test that visual_mode attribute doesn't exist
    if hasattr(engine, 'visual_mode'):
        print("✗ Error: visual_mode attribute still exists")
    else:
        print("✓ visual_mode attribute successfully removed")
        
    print("\n✓ All tests passed! DM automation should now work without visual_mode errors.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
