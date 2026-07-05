def create_markmap_html(markdown_content: str) -> str:
    """Convert markdown into interactive mindmap HTML with pan/zoom support."""
    markdown_escaped = (
        markdown_content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mindmap</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            width: 100vw; height: 100vh; overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
        }}
        #mindmap-container {{ width: 100%; height: 100%; overflow: auto; cursor: grab; position: relative; }}
        #mindmap-container:active {{ cursor: grabbing; }}
        #mindmap {{ width: 100%; height: 100%; min-width: 2000px; min-height: 2000px; }}
        .loading {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-size: 18px; color: #666; z-index: 1000;
        }}
        .controls {{
            position: fixed; bottom: 20px; right: 20px; display: flex;
            flex-direction: column; gap: 10px; z-index: 1000;
        }}
        .control-btn {{
            background: white; border: 2px solid #ddd; border-radius: 8px;
            padding: 10px 15px; cursor: pointer; font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: all 0.2s;
            font-weight: 600; color: #333;
        }}
        .control-btn:hover {{ background: #f0f0f0; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .control-btn:active {{ transform: translateY(0); }}
        .info-badge {{
            position: fixed; top: 20px; left: 20px; background: white;
            padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-size: 14px; color: #666; z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="loading">Loading mindmap...</div>
    <div class="info-badge">🖱️ Drag to pan • 🎯 Click nodes to expand/collapse • 🔍 Use controls to zoom</div>
    <div id="mindmap-container"><svg id="mindmap"></svg></div>
    <div class="controls">
        <button class="control-btn" onclick="zoomIn()">🔍 Zoom In</button>
        <button class="control-btn" onclick="zoomOut()">🔍 Zoom Out</button>
        <button class="control-btn" onclick="resetView()">🎯 Reset View</button>
        <button class="control-btn" onclick="fitView()">📐 Fit All</button>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.15.4"></script>
    <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.15.4/dist/browser/index.min.js"></script>

    <script>
        let mm;
        let isPanning = false;
        let startX, startY, scrollLeft, scrollTop;
        const container = document.getElementById('mindmap-container');

        container.addEventListener('mousedown', (e) => {{
            if (e.target.tagName.toLowerCase() === 'svg' || e.target.classList.contains('markmap-container')) {{
                isPanning = true;
                container.style.cursor = 'grabbing';
                startX = e.pageX - container.offsetLeft;
                startY = e.pageY - container.offsetTop;
                scrollLeft = container.scrollLeft;
                scrollTop = container.scrollTop;
            }}
        }});
        container.addEventListener('mouseleave', () => {{ isPanning = false; container.style.cursor = 'grab'; }});
        container.addEventListener('mouseup', () => {{ isPanning = false; container.style.cursor = 'grab'; }});
        container.addEventListener('mousemove', (e) => {{
            if (!isPanning) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const y = e.pageY - container.offsetTop;
            container.scrollLeft = scrollLeft - (x - startX) * 1.5;
            container.scrollTop = scrollTop - (y - startY) * 1.5;
        }});

        function zoomIn() {{ if (mm) mm.rescale(1.2); }}
        function zoomOut() {{ if (mm) mm.rescale(0.8); }}
        function resetView() {{
            if (mm) {{
                mm.rescale(1);
                container.scrollLeft = (container.scrollWidth - container.clientWidth) / 2;
                container.scrollTop = (container.scrollHeight - container.clientHeight) / 2;
            }}
        }}
        function fitView() {{
            if (mm) {{
                mm.fit();
                setTimeout(() => {{
                    container.scrollLeft = (container.scrollWidth - container.clientWidth) / 2;
                    container.scrollTop = (container.scrollHeight - container.clientHeight) / 2;
                }}, 100);
            }}
        }}

        (async function() {{
            try {{
                const loadingEl = document.querySelector('.loading');
                if (loadingEl) loadingEl.style.display = 'none';

                const markdown = `{markdown_escaped}`;
                const {{ markmap }} = window;
                const {{ Transformer }} = markmap;
                const transformer = new Transformer();
                const {{ root, features }} = transformer.transform(markdown);
                const {{ styles, scripts }} = transformer.getUsedAssets(features);

                if (styles) {{
                    styles.forEach(style => {{
                        const styleEl = document.createElement('style');
                        styleEl.textContent = style;
                        document.head.appendChild(styleEl);
                    }});
                }}
                if (scripts) {{
                    await Promise.all(scripts.map(src => new Promise((resolve, reject) => {{
                        const script = document.createElement('script');
                        script.src = src;
                        script.onload = resolve;
                        script.onerror = reject;
                        document.head.appendChild(script);
                    }})));
                }}

                const {{ Markmap }} = markmap;
                const options = {{
                    maxWidth: 300, colorFreezeLevel: 2, paddingX: 16,
                    duration: 500, zoom: true, pan: true,
                }};
                mm = Markmap.create('#mindmap', options, root);

                setTimeout(() => {{
                    mm.fit();
                    container.scrollLeft = (container.scrollWidth - container.clientWidth) / 2;
                    container.scrollTop = (container.scrollHeight - container.clientHeight) / 2;
                }}, 100);
            }} catch (error) {{
                console.error('Error creating mindmap:', error);
                document.body.innerHTML = `
                    <div style="padding: 20px; color: red; font-family: sans-serif;">
                        <h3>Error rendering mindmap</h3>
                        <p>${{error.message}}</p>
                    </div>
                `;
            }}
        }})();
    </script>
</body>
</html>"""
