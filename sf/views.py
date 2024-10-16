def generate_mermaid_html(graph_data, metadata_dict, output_file="graph.html"):
    # assign color depending on status    
    colors = {
        'pending'        : '#6F7777',
        'inprogress'     : '#F7DEAD',
        'error'          : '#CD4439',
        'completed'      : '#72B896',
        'missingoutput'  : '#E29173',
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
    
    graph_theme = """

%%{
  init: {
    'theme': 'base',
    'themeVariables': {
        'textColor': '#191919',
        'primaryColor': '#BB2528',
        'primaryTextColor': '#fff',
        'primaryBorderColor': '#7C0000',
        'clusterBkg': '#E9EED9',
        'titleColor':'#54473F',
        'lineColor': '#B0B0B0',
        'secondaryColor': '#006100'
    }
  }
}%%

    """
    graph_content = graph_content.replace("graph TD", graph_theme + "graph TD")

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
           /* General reset for the page */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: Arial, sans-serif;
                background-color: #F8F8F8;
            }}

            .container {{
                display: flex; /* Use flexbox for layout */
                height: 100vh; /* Full height of the viewport */
                overflow: hidden; /* Prevent horizontal scroll */
            }}

            .hidden {{
                display: none;
            }}
            
            #graph {{
                border: 1px solid #ccc;
                background-color: #FFFFFF;
                overflow: hidden;
                position: relative;
                padding: 20px;
            }}
            
            #metadata-container {{
                border: 1px solid #ccc;           
                background-color: #FFFFFF;
                overflow: hidden;
                position: relative;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Visual effect */
            }}
            
            /* Left div with long scrollable content */
            .left-div {{
                flex: 2; /* Take up more space */
                background-color: #F8F8F8;
                padding: 20px;
                position: relative;
                overflow: hidden; /* Enable vertical scrolling */
                height: 100vh; /* Ensure it fills the full viewport height */
            }}

            /* Right div that stays visible while scrolling */
            .right-div {{
                flex: 1; /* Take up less space */
                background-color: #F8F8F8;
                padding: 20px;
                position: sticky;
                top: 20px; /* Maintain a gap from the top */
                height: fit-content; /* Ensure it only takes as much space as needed */
            }}

            .copy-button {{
                cursor: pointer;
                color: grey;
                text-decoration: underline;
            }}

            svg {{
                cursor: grab;
                transition: transform 0.1s; /* Smooth out dragging */
                width: 100%; /* Scale SVG to fit container */
                height: 100%;
            }}
            
            /* Container for the graph */
            .graph-container {{
                width: 100%;
                height: 99%;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: auto; /* Allow graph dragging */
            }}

            svg:active {{
                cursor: grabbing;
            }}
            h3 {{
                text-align: center;
                margin-bottom: 20px; /* Adjust this value as needed */
            }}
            h4 {{
                text-align: center;
                margin-bottom: 10px; /* Adjust this value as needed */
                }}

            table {{
                width: 100%;
                border-collapse: collapse; /* Remove space between cells */
                margin: 20px 0; /* Add some space above and below the table */
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* Add shadow effect */
            }}
            th, td {{
                padding: 12px; /* Add padding to cells */
                text-align: left; /* Align text to the left */
                border-bottom: 1px solid #ddd; /* Add a bottom border to cells */
            }}
            th {{
                background-color: #4CAF50; /* Green background for the header */
                color: white; /* White text color for the header */
            }}
            tr:hover {{
                background-color: #f1f1f1; /* Highlight row on hover */
            }}
            
            .highlight {{
                font-weight: bold; /* Optional: make the highlighted text bold */
            }}

        </style>
    </head>
    <body>

    <!-- Graph and Metadata Container -->
    <div class="container" id="graph-container">
        <div class="left-div">
            <h3>SnapFlow processing summary</h3>
            <div class="graph-container" id="graph">
                <div class="mermaid">
                    {graph_content}
                </div>
            </div>
        </div>
        <div class="right-div">
            <h4>Metadata:</h4>
            <div id="metadata-container">
                <div id="metadata">Click a node to display its metadata here.</div>
            </div>
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
                    <table>
                        <tbody>
                            <tr>
                                <td><span class="highlight">Name</span></td><td>${{data.label || 'Unnamed'}}</td>
                            </tr>
                                <td><span class="highlight">Status</span></td><td>${{data.status || 'Unknown'}}</td>
                            <tr>
                            </tr>
                                <td><span class="highlight">Time Spent</span></td><td>${{data.time_spent || 'N/A'}}</td>
                            <tr>
                                <td><span class="highlight">Workdir</span></td><td><span class="copy-button" onclick="copyHiddenText()"><i>copy path</i></span><span id="hidden-text" class="hidden">${{data.workdir || '??'}}</span></td>
                            </tr>
                        </tbody>
                    </table>
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
