#!/usr/bin/env python3
"""
Fix Summary Page - Remove new charts from Summary, create separate Analytics page
"""

import json
import uuid

def generate_page_id():
    """Generate a unique page ID"""
    return str(uuid.uuid4())[:8]

def main():
    input_file = 'dashboards/WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json'
    
    print("🔧 Fixing Summary Page...")
    print("="*60)
    
    # Load dashboard
    with open(input_file, 'r') as f:
        dashboard = json.load(f)
    
    # Find the Summary page
    summary_page = None
    for page in dashboard.get('pages', []):
        if 'Summary' in page.get('displayName', ''):
            summary_page = page
            break
    
    if not summary_page:
        print("❌ Summary page not found")
        return
    
    # Separate original widgets from new analytics widgets
    original_widgets = []
    analytics_widgets = []
    
    for layout in summary_page['layout']:
        widget = layout.get('widget', {})
        spec = widget.get('spec', {})
        frame = spec.get('frame', {})
        title = frame.get('title', '')
        
        # Check if it's one of our new analytics charts (has emojis)
        if any(emoji in title for emoji in ['💰', '🔥', '📦', '⚡', '🔐', '✅', '🔍']):
            analytics_widgets.append(layout)
        else:
            original_widgets.append(layout)
    
    # Update Summary page to only have original widgets
    summary_page['layout'] = original_widgets
    
    print(f"✅ Summary page cleaned: {len(original_widgets)} widgets kept")
    print(f"✅ Found {len(analytics_widgets)} analytics charts to move")
    
    # Create new Analytics page with the charts
    if analytics_widgets:
        # Reposition widgets to start from top
        for i, layout in enumerate(analytics_widgets):
            pos = layout.get('position', {})
            # Calculate new Y position (arrange in rows)
            row = i // 2  # 2 widgets per row
            col = i % 2
            
            layout['position'] = {
                'x': col * 6,
                'y': row * 5,
                'z': 0,
                'width': pos.get('width', 6),
                'height': pos.get('height', 4)
            }
        
        analytics_page = {
            "name": generate_page_id(),
            "displayName": "Analytics & Insights",
            "layout": analytics_widgets
        }
        
        # Add the new page after Summary
        pages = dashboard.get('pages', [])
        summary_index = 0
        for i, page in enumerate(pages):
            if 'Summary' in page.get('displayName', ''):
                summary_index = i
                break
        
        pages.insert(summary_index + 1, analytics_page)
        dashboard['pages'] = pages
        
        print(f"✅ Created 'Analytics & Insights' page with {len(analytics_widgets)} charts")
    
    # Save updated dashboard
    with open(input_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Dashboard fixed!")
    print(f"{'='*60}")
    print(f"   Summary: Only completion percentage metrics")
    print(f"   New page: 'Analytics & Insights' with 7 charts")
    print(f"\n🚀 Ready to redeploy!")

if __name__ == "__main__":
    main()
