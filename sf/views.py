def generate_mermaid_html(graph_data, metadata_dict, output_file="graph.html"):
    # assign color depending on status    
    colors = {
        'pending'    : '#6F7777',
        'inprogress': '#F7DEAD',
        'error'      : '#CD4439',
        'completed'  : '#72B896',
    }
    for d in metadata_dict.values():
        d['color'] = colors[d['class']]

    # Start building the Mermaid graph structure dynamically
    # graph_lines = ["graph TD"]
    
    # # Generate nodes and edges from graph data
    # for source, target, _ in graph_data:
    #     class_name = metadata_dict.get(source, {}).get("class", "default")
    #     label = metadata_dict.get(source, {}).get("label", source)
    #     graph_lines.append(f'    {source}["{label}"]:::{class_name} --> {target}')

    # Add class definitions based on metadata
    class_definitions = "classDef defaultSubgraph fill:#F0E68C,stroke:#666,stroke-width:2px;\n"
    class_definitions += "\n".join([
        f'classDef {meta["class"]} fill:{meta["color"]},stroke:{meta["color"]},stroke-width:2px;'
        for key, meta in metadata_dict.items()
    ])
    
    # Combine the graph lines and class definitions
    graph_content = graph_data + '\n' + class_definitions

    # HTML template with placeholders
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SnapFlow pipeline</title>

        <!-- Load Mermaid.js -->
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>

        <style>
            body {{
                font-family: Arial, sans-serif;
            }}

            .hidden {{
            display: none;
            }}
            
            .copy-button {{
            cursor: pointer;
            color: blue;
            text-decoration: underline;
            }}
            
            #graph-container {{
                display: flex;
                justify-content: center;
                align-items: flex-start;
                gap: 10px;
                margin-top: 10px;
            }}

            #graph {{
                border: 1px solid #ccc;
                min-width: 900px;
                min-height: 900px;
                overflow: hidden;
                position: relative;
            }}

            #metadata {{
                border: 1px solid #ccc;
                padding: 10px;
                width: 300px;
                height: 400px;
            }}

            svg {{
                cursor: grab;
                transition: transform 0.1s; /* Smooth out dragging */
            }}

            svg:active {{
                cursor: grabbing;
            }}
            h3 {{text-align: center;}}
            h4 {{text-align: center;}}
        </style>
    </head>
    <body>

    <!-- Graph and Metadata Container -->
    <div id="graph-container">
        <div>
        <h3>SnapFlow processing summary</h3>
        <div id="graph">
            <div class="mermaid">
            %%{{
  init: {{
    'theme': 'base',
    'themeVariables': {{
      'primaryColor': '#BB2528',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#7C0000',
      'clusterBkg': '#E9EED9',
      'titleColor':'#54473F',
      'lineColor': '#B0B0B0',
      'secondaryColor': '#006100',
      'tertiaryColor': '#fff'
    }}
  }}
}}%%
                {graph_content}
            </div>
        </div>
        </div>
        <div>
            <h4>Metadata:</h4>
        <div id="metadata">Click a node to display its metadata here.</div>
        </div>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true }});

        let isDragging = false;
        let startX = 0, startY = 0;
        let currentTranslateX = 0, currentTranslateY = 0;
        let scale = 1;

        // Function to set graph transform (for zoom & drag)
        function setTransform(svg, tx, ty, scale) {{
            svg.style.transform = `translate(${{tx}}px, ${{ty}}px) scale(${{scale}})`;
        }}

        function attachDragHandlers(svg) {{
            svg.addEventListener('mousedown', (event) => {{
                isDragging = true;
                startX = event.clientX;
                startY = event.clientY;
            }});

            window.addEventListener('mouseup', () => {{
                isDragging = false;
            }});

            svg.addEventListener('mousemove', (event) => {{
                if (!isDragging) return;

                const dx = event.clientX - startX;
                const dy = event.clientY - startY;

                currentTranslateX += dx;
                currentTranslateY += dy;

                setTransform(svg, currentTranslateX, currentTranslateY, scale);

                startX = event.clientX;
                startY = event.clientY;
            }});
        }}

        function attachZoomHandlers(svg) {{
            svg.addEventListener('wheel', (event) => {{
                event.preventDefault();

                const zoomFactor = 0.1;
                scale += event.deltaY < 0 ? zoomFactor : -zoomFactor;

                // Clamp the scale between 0.1 and 10
                scale = Math.max(0.1, Math.min(scale, 10));

                setTransform(svg, currentTranslateX, currentTranslateY, scale);
            }});
        }}

        function attachClickHandlers(svg) {{
            svg.querySelectorAll('g.node').forEach(node => {{
                node.addEventListener('click', () => {{
                    const nodeId = node.getAttribute('data-id');
                    const metadata = {metadata_dict};
                    const data = metadata[nodeId] || {{}};
                    const content = `
                        <strong>Name:</strong> ${{data.label || 'Unnamed'}}<br>
                        <strong>Status:</strong> ${{data.status || 'Unknown'}}<br>
                        <strong>Time Spent:</strong> ${{data.time_spent || 'N/A'}}<br>
                        <strong>Class:</strong> ${{data.class || 'default'}}<br>
                        <strong>Workdir:</strong> <span class="copy-button" onclick="copyHiddenText()">copy path</span><span id="hidden-text" class="hidden">${{data.workdir || '??'}}</span>
                    `;
                    const label = node.querySelector('.nodeLabel, foreignObject span');
                    document.getElementById('metadata').innerHTML = content;

                }});
            }});
        }}
        
        function copyHiddenText() {{
        const hiddenText = document.getElementById('hidden-text').textContent;
        navigator.clipboard.writeText(hiddenText).then(() => {{
            alert('Text copied to clipboard!');
        }}).catch(err => {{
            console.error('Failed to copy: ', err);
        }});
        }}
        
        document.addEventListener('DOMContentLoaded', () => {{
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));

            setTimeout(() => {{
                const svg = document.querySelector('#graph svg');
                if (svg) {{
                    attachDragHandlers(svg);
                    attachZoomHandlers(svg);
                    attachClickHandlers(svg);
                }}
            }}, 1000);
        }});
    </script>

    </body>
    </html>
    """

    # Write the generated HTML to the output file
    with open(output_file, "w") as f:
        f.write(html_template)

    print(f"HTML saved to {output_file}. Open it in your browser.")
    
def main():
    # Example usage
    graph_data = [
        ("A", "B", {}),
        ("B", "C", {}),
        ("B", "D", {}),
        ("D", "E", {}),
    ]

    metadata_dict = {
        "A": {"label"     : "Start", 
            "class"     : "start",
            "status"    : "Completed",
            "workdir"   : "/somepath/", 
            "time_spent": "5 min"},
        "B": {"label": "Process", "class": "process", "status": "In Progress", "workdir"   : "/somepath/", "time_spent": "10 min"},
        "C": {"label": "Finish", "class": "finish", "status": "Pending", "workdir"   : "/somepath/", "time_spent": "N/A"},
        "D": {"label": "Optional Step", "class": "optional", "status": "Error", "workdir"   : "/somepath/", "time_spent": "0 min"},
        "E": {"label": "Quantify Expression", "class": "process", "status": "Completed", "workdir"   : "/somepath/", "time_spent": "15 min"},
    }

    generate_mermaid_html(graph_data, metadata_dict)

if __name__ == "__main__":
    main()
