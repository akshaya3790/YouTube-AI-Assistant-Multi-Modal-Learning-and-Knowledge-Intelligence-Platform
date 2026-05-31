import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def extract_knowledge_graph_data(transcript, title, chapters, learning_mode, selected_model="gemini-2.5-flash"):
    """
    Queries the Gemini model to parse key concepts, parent-child trees, and relationships from the transcript
    and returns a clean structured JSON schema matching concepts, technologies, edges, and scores.
    """
    chapters_text = ""
    if chapters:
        for i, ch in enumerate(chapters):
            chapters_text += f"- Chapter {i+1}: {ch.get('title', 'Chapter')} ({ch.get('start_time', '00:00')}) - Summary: {ch.get('summary', '')}\n"
            
    # Inject learning mode guidelines
    mode_guideline = ""
    if learning_mode == "Beginner Mode":
        mode_guideline = "Focus only on the 10-15 most fundamental/introductory concepts. Exclude complex sub-details."
    elif learning_mode == "Student Mode":
        mode_guideline = "Focus on definitions, examples, and educational concept hierarchies (around 20 nodes)."
    elif learning_mode == "Professional Mode":
        mode_guideline = "Highlight technical frameworks, system architectures, workflows, algorithms, and real-world tools (25-30 nodes)."
    else:  # Research Mode
        mode_guideline = "Provide maximum granularity. Extract all possible nodes, deep academic connections, libraries, tools, and dependencies (35+ nodes)."

    prompt = f"""
    You are an expert Knowledge Graph Architect and NLP Analyst.
    Your task is to analyze the video transcript titled "{title}" and extract a structured knowledge graph.
    
    Active Learning Mode: {learning_mode}
    Guideline for this mode: {mode_guideline}

    Here is the video breakdown and content:
    {chapters_text}
    
    Transcript snippet:
    {transcript[:28000]}
    
    Extract:
    1. Nodes:
       - Include: Concept, Technology, Framework, Algorithm, Tool, Company, or Application.
       - A short unique ID for each node (e.g. "n1", "n2", "ml", "tf").
       - A descriptive label (e.g., "TensorFlow").
       - Importance Score (1-100) based on how central the topic is to the video content.
       - Short definition (1-2 sentences).
       - Timestamps and Chapter names where this topic is mentioned in the video.
    2. Edges:
       - Directed connections between nodes.
       - Types: "Depends On", "Part Of", "Uses", "Extends", "Related To", "Influences", "Requires", "Produces".
       - Strength score (1-10) of the connection.
       - Relevance score (1-100) of the edge.

    Return ONLY a raw, valid JSON object following the schema below. 
    Do NOT include markdown syntax (like ```json or ```), backticks, comments, or any other surrounding text. It must be directly parseable by json.loads().

    JSON Schema:
    {{
      "nodes": [
        {{
          "id": "unique_id",
          "label": "Topic Name",
          "category": "Concept",  // Must be one of: Concept, Technology, Framework, Algorithm, Tool, Company, Application
          "importance_score": 90,
          "definition": "Brief definition here.",
          "timestamp": "MM:SS",
          "chapter": "Chapter Name"
        }}
      ],
      "edges": [
        {{
          "source": "source_node_id",
          "target": "target_node_id",
          "type": "Uses",       // Must be one of: Depends On, Part Of, Uses, Extends, Related To, Influences, Requires, Produces
          "strength": 8,
          "relevance_score": 85
        }}
      ]
    }}
    """
    
    try:
        model = ChatGoogleGenerativeAI(model=selected_model)
        response = model.invoke([HumanMessage(content=prompt)])
        
        # Clean markdown code block markers
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        
        # Sometimes the model returns trailing comments or extra text. Try to isolate the JSON block.
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
            
        data = json.loads(clean_text)
        return data
    except Exception as e:
        # Return fallback mock graph to prevent errors
        print(f"Error extracting knowledge graph: {e}")
        return get_fallback_graph(title)

def get_fallback_graph(title):
    """
    Generates a basic fallback graph structure if LLM extraction fails.
    """
    return {
        "nodes": [
            {"id": "n1", "label": title, "category": "Concept", "importance_score": 100, "definition": "Main topic of the video.", "timestamp": "00:00", "chapter": "Introduction"},
            {"id": "n2", "label": "Key Insight A", "category": "Concept", "importance_score": 80, "definition": "A primary takeaway discussed in the video.", "timestamp": "02:15", "chapter": "Overview"},
            {"id": "n3", "label": "Key Insight B", "category": "Concept", "importance_score": 85, "definition": "Another important concept covered.", "timestamp": "04:30", "chapter": "Deep Dive"},
            {"id": "n4", "label": "Standard Tools", "category": "Tool", "importance_score": 75, "definition": "Techniques or utilities mentioned.", "timestamp": "07:45", "chapter": "Application"}
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "Part Of", "strength": 9, "relevance_score": 90},
            {"source": "n1", "target": "n3", "type": "Part Of", "strength": 8, "relevance_score": 85},
            {"source": "n2", "target": "n4", "type": "Uses", "strength": 7, "relevance_score": 80},
            {"source": "n3", "target": "n4", "type": "Uses", "strength": 8, "relevance_score": 85}
        ]
    }

def generate_vis_html(graph_data, layout_mode="network"):
    """
    Generates highly interactive HTML containing Vis.js graph network container.
    Features local interactive search, custom colors, sizing, legends, info sidebar panels, and layout toggle.
    """
    nodes_json = json.dumps(graph_data.get("nodes", []))
    edges_json = json.dumps(graph_data.get("edges", []))
    
    # Render vis.js script
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style type="text/css">
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #F8F9FE;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            #mynetwork {{
                width: 100vw;
                height: 100vh;
                position: absolute;
                top: 0;
                left: 0;
            }}
            /* Glassmorphic Control Panel */
            .controls {{
                position: absolute;
                top: 15px;
                left: 15px;
                z-index: 10;
                display: flex;
                gap: 10px;
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(147, 112, 219, 0.2);
                border-radius: 12px;
                padding: 10px 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                align-items: center;
            }}
            .controls input {{
                padding: 8px 12px;
                border-radius: 8px;
                border: 1px solid rgba(147, 112, 219, 0.3);
                outline: none;
                font-size: 13px;
                width: 170px;
            }}
            .controls select {{
                padding: 8px 12px;
                border-radius: 8px;
                border: 1px solid rgba(147, 112, 219, 0.3);
                outline: none;
                font-size: 13px;
                background: white;
                cursor: pointer;
            }}
            /* Legend Overlay */
            .legend {{
                position: absolute;
                bottom: 15px;
                left: 15px;
                z-index: 10;
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(147, 112, 219, 0.2);
                border-radius: 12px;
                padding: 10px 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                font-size: 11px;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 5px;
                gap: 8px;
            }}
            .legend-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
            }}
            /* Glassmorphic Side Info Card */
            .info-card {{
                position: absolute;
                top: 15px;
                right: 15px;
                width: 300px;
                max-height: calc(100vh - 30px);
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(147, 112, 219, 0.3);
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(147, 112, 219, 0.15);
                padding: 18px;
                overflow-y: auto;
                display: none;
                z-index: 20;
                transition: transform 0.3s ease;
            }}
            .info-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(147, 112, 219, 0.1);
                padding-bottom: 8px;
                margin-bottom: 12px;
            }}
            .info-header h3 {{
                margin: 0;
                color: #4B0082;
                font-size: 18px;
            }}
            .close-btn {{
                border: none;
                background: none;
                font-size: 20px;
                cursor: pointer;
                color: #999;
            }}
            .info-field {{
                margin-bottom: 12px;
                font-size: 13px;
                line-height: 1.4;
            }}
            .info-label {{
                font-weight: bold;
                color: #6A5ACD;
                margin-bottom: 3px;
            }}
            .info-val {{
                color: #333;
            }}
            .badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div id="mynetwork"></div>
        
        <div class="controls">
            <input type="text" id="searchBox" placeholder="🔍 Search node..." onkeyup="searchNode()"/>
            <select id="layoutSelect" onchange="changeLayout(this.value)">
                <option value="network" {'selected' if layout_mode == 'network' else ''}>Force Directed</option>
                <option value="hierarchical" {'selected' if layout_mode == 'hierarchical' else ''}>Hierarchical Tree</option>
            </select>
        </div>

        <div class="legend">
            <div style="font-weight: bold; margin-bottom: 6px; color:#4B0082;">Categories</div>
            <div class="legend-item"><span class="legend-dot" style="background:#9370DB;"></span> Concept</div>
            <div class="legend-item"><span class="legend-dot" style="background:#1E90FF;"></span> Technology</div>
            <div class="legend-item"><span class="legend-dot" style="background:#008080;"></span> Framework</div>
            <div class="legend-item"><span class="legend-dot" style="background:#2E7D32;"></span> Algorithm</div>
            <div class="legend-item"><span class="legend-dot" style="background:#FF8C00;"></span> Tool</div>
            <div class="legend-item"><span class="legend-dot" style="background:#708090;"></span> Company</div>
            <div class="legend-item"><span class="legend-dot" style="background:#C71585;"></span> Application</div>
        </div>

        <div id="infoCard" class="info-card">
            <div class="info-header">
                <h3 id="cardLabel">Node Label</h3>
                <button class="close-btn" onclick="closeCard()">&times;</button>
            </div>
            <div class="info-field">
                <div class="info-label">Category</div>
                <div id="cardCategory" class="info-val">Concept</div>
            </div>
            <div class="info-field">
                <div class="info-label">Importance Score</div>
                <div id="cardScore" class="info-val">80</div>
            </div>
            <div class="info-field">
                <div class="info-label">Definition</div>
                <div id="cardDefinition" class="info-val">No definition available.</div>
            </div>
            <div class="info-field">
                <div class="info-label">Reference Timestamp</div>
                <div id="cardTimestamp" class="info-val">00:00</div>
            </div>
            <div class="info-field">
                <div class="info-label">Chapter</div>
                <div id="cardChapter" class="info-val">General</div>
            </div>
        </div>

        <script type="text/javascript">
            // Color Mapping
            const colors = {{
                "Concept": "#9370DB",      // Purple
                "Technology": "#1E90FF",   // Blue
                "Framework": "#008080",    // Teal
                "Algorithm": "#2E7D32",    // Green
                "Tool": "#FF8C00",         // Orange
                "Company": "#708090",      // Slate Gray
                "Application": "#C71585"   // Magenta
            }};

            const rawNodes = {nodes_json};
            const rawEdges = {edges_json};

            // Format Nodes for Vis.js
            const nodesArray = rawNodes.map(n => {{
                const size = 15 + (n.importance_score || 50) * 0.25;
                const nodeColor = colors[n.category] || "#9370DB";
                return {{
                    id: n.id,
                    label: n.label,
                    title: n.definition || n.label,
                    size: size,
                    color: {{
                        background: nodeColor,
                        border: nodeColor,
                        highlight: {{
                            background: "#D8BFD8",
                            border: "#6A5ACD"
                        }}
                    }},
                    font: {{ color: "#111", size: 13 }},
                    shape: "dot",
                    // Attach original data properties
                    category: n.category,
                    score: n.importance_score,
                    definition: n.definition,
                    timestamp: n.timestamp,
                    chapter: n.chapter
                }};
            }});

            // Format Edges for Vis.js
            const edgesArray = rawEdges.map(e => {{
                return {{
                    from: e.source,
                    to: e.target,
                    label: e.type,
                    arrows: "to",
                    width: e.strength ? Math.max(1, e.strength * 0.4) : 1.5,
                    color: {{ color: "#A9A9A9", highlight: "#4B0082" }},
                    font: {{ size: 9, align: "horizontal" }}
                }};
            }});

            const container = document.getElementById('mynetwork');
            const data = {{
                nodes: new vis.DataSet(nodesArray),
                edges: new vis.DataSet(edgesArray)
            }};

            let options = {{
                nodes: {{
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    shadow: false,
                    smooth: {{
                        type: "continuous"
                    }}
                }},
                interaction: {{
                    hover: true,
                    navigationButtons: true,
                    keyboard: true
                }},
                physics: {{
                    enabled: true,
                    solver: "forceAtlas2Based",
                    forceAtlas2Based: {{
                        gravitationalConstant: -50,
                        centralGravity: 0.015,
                        springLength: 120,
                        springConstant: 0.05
                    }}
                }}
            }};

            const network = new vis.Network(container, data, options);

            // Pre-apply layout mode
            if ("{layout_mode}" === "hierarchical") {{
                applyHierarchical();
            }}

            // Handle Node Selection
            network.on("selectNode", function (params) {{
                const nodeId = params.nodes[0];
                const nodeData = nodesArray.find(n => n.id === nodeId);
                if (nodeData) {{
                    document.getElementById('cardLabel').innerText = nodeData.label;
                    document.getElementById('cardCategory').innerText = nodeData.category;
                    document.getElementById('cardCategory').style.background = colors[nodeData.category] || "#9370DB";
                    document.getElementById('cardScore').innerText = nodeData.score + " / 100";
                    document.getElementById('cardDefinition').innerText = nodeData.definition || "No definition available.";
                    document.getElementById('cardTimestamp').innerText = nodeData.timestamp || "N/A";
                    document.getElementById('cardChapter').innerText = nodeData.chapter || "N/A";
                    document.getElementById('infoCard').style.display = 'block';
                }}
            }});

            network.on("deselectNode", function (params) {{
                closeCard();
            }});

            function closeCard() {{
                document.getElementById('infoCard').style.display = 'none';
            }}

            // Search Filter
            function searchNode() {{
                const query = document.getElementById('searchBox').value.toLowerCase();
                if (!query) {{
                    network.fit();
                    return;
                }}
                const matchedNode = nodesArray.find(n => n.label.toLowerCase().includes(query));
                if (matchedNode) {{
                    network.selectNodes([matchedNode.id]);
                    network.focus(matchedNode.id, {{
                        scale: 1.2,
                        animation: {{ duration: 500 }}
                    }});
                    // Update card
                    document.getElementById('cardLabel').innerText = matchedNode.label;
                    document.getElementById('cardCategory').innerText = matchedNode.category;
                    document.getElementById('cardCategory').style.background = colors[matchedNode.category] || "#9370DB";
                    document.getElementById('cardScore').innerText = matchedNode.score + " / 100";
                    document.getElementById('cardDefinition').innerText = matchedNode.definition || "No definition available.";
                    document.getElementById('cardTimestamp').innerText = matchedNode.timestamp || "N/A";
                    document.getElementById('cardChapter').innerText = matchedNode.chapter || "N/A";
                    document.getElementById('infoCard').style.display = 'block';
                }}
            }}

            // Change layout algorithm dynamically
            function changeLayout(val) {{
                if (val === 'hierarchical') {{
                    applyHierarchical();
                }} else {{
                    applyForceDirected();
                }}
            }}

            function applyHierarchical() {{
                network.setOptions({{
                    layout: {{
                        hierarchical: {{
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed',
                            nodeSpacing: 130,
                            levelSeparation: 130
                        }}
                    }},
                    physics: {{ enabled: false }}
                }});
            }}

            function applyForceDirected() {{
                network.setOptions({{
                    layout: {{
                        hierarchical: {{ enabled: false }}
                    }},
                    physics: {{
                        enabled: true,
                        solver: "forceAtlas2Based"
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html_content

def export_graph_mermaid(graph_data):
    """
    Converts graph data into a Mermaid.js diagram definition string.
    """
    lines = ["graph TD"]
    # Node declarations with styled brackets
    for n in graph_data.get("nodes", []):
        label_safe = n["label"].replace('"', '\\"')
        lines.append(f'    {n["id"]}["{label_safe} ({n["category"]})"]')
        
    # Edge connections
    for e in graph_data.get("edges", []):
        lines.append(f'    {e["source"]} -->|"{e["type"]}"| {e["target"]}')
        
    return "\n".join(lines)

def export_graph_markdown(graph_data):
    """
    Converts graph structure to structured Markdown.
    """
    lines = [f"# Topic Mind Map Structure\n"]
    
    lines.append("## Key Concepts Tree\n")
    for n in graph_data.get("nodes", []):
        lines.append(f"- **{n['label']}** ({n['category']})")
        lines.append(f"  - *Definition*: {n['definition']}")
        lines.append(f"  - *Importance Score*: {n['importance_score']}/100")
        lines.append(f"  - *Reference*: Chapter: {n.get('chapter', 'N/A')} | Timestamp: {n.get('timestamp', '00:00')}\n")
        
    lines.append("## Topic Relationships\n")
    for e in graph_data.get("edges", []):
        source_label = next((n["label"] for n in graph_data["nodes"] if n["id"] == e["source"]), e["source"])
        target_label = next((n["label"] for n in graph_data["nodes"] if n["id"] == e["target"]), e["target"])
        lines.append(f"- **{source_label}** {e['type']} **{target_label}** (Strength: {e['strength']}/10)")
        
    return "\n".join(lines)

def export_graph_csv(graph_data):
    """
    Generates CSV lists of nodes and edges.
    """
    import io
    output = io.StringIO()
    
    # Nodes section
    output.write("--- NODES ---\n")
    output.write("ID,Label,Category,Importance Score,Definition,Timestamp,Chapter\n")
    for n in graph_data.get("nodes", []):
        definition = n["definition"].replace('"', '""')
        chapter = n.get("chapter", "").replace('"', '""')
        output.write(f'"{n["id"]}","{n["label"]}","{n["category"]}",{n["importance_score"]},"{definition}","{n.get("timestamp", "00:00")}","{chapter}"\n')
        
    # Edges section
    output.write("\n--- EDGES ---\n")
    output.write("Source ID,Target ID,Relationship Type,Strength,Relevance Score\n")
    for e in graph_data.get("edges", []):
        output.write(f'"{e["source"]}","{e["target"]}","{e["type"]}",{e["strength"]},{e.get("relevance_score", 80)}\n')
        
    return output.getvalue()

def generate_recommendations(graph_data):
    """
    Generates actionable learning recommendations based on knowledge graph centrality.
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    if not nodes:
        return []
        
    # Calculate simple degree centrality to find core topics
    in_degrees = {n["id"]: 0 for n in nodes}
    out_degrees = {n["id"]: 0 for n in nodes}
    for e in edges:
        s, t = e["source"], e["target"]
        if s in out_degrees: out_degrees[s] += 1
        if t in in_degrees: in_degrees[t] += 1
        
    # Map back to titles
    recommendations = []
    
    # Core nodes
    core_nodes = sorted(nodes, key=lambda n: in_degrees.get(n["id"], 0) + out_degrees.get(n["id"], 0), reverse=True)
    if len(core_nodes) > 0:
        main_topic = core_nodes[0]["label"]
        recommendations.append({
            "topic": f"Deepen knowledge of: {main_topic}",
            "reason": "This is the most connected core concept in this content and serves as the structural foundation."
        })
        
    # Technology nodes
    tech_nodes = [n for n in nodes if n["category"] in ["Technology", "Framework", "Tool"]]
    if tech_nodes:
        rec_tech = tech_nodes[0]["label"]
        recommendations.append({
            "topic": f"Implement project using: {rec_tech}",
            "reason": f"This tool/technology is highly recommended for applied practice of the concepts covered in this video."
        })
        
    # Pre-requisite dependencies
    dependency_edges = [e for e in edges if e["type"] in ["Depends On", "Requires"]]
    if dependency_edges:
        edge = dependency_edges[0]
        source_label = next((n["label"] for n in nodes if n["id"] == edge["source"]), "Pre-requisite")
        target_label = next((n["label"] for n in nodes if n["id"] == edge["target"]), "Main topic")
        recommendations.append({
            "topic": f"Master pre-requisite: {source_label}",
            "reason": f"Required understanding before exploring {target_label}."
        })
        
    # Fallback recommendations if empty
    if len(recommendations) < 3:
        recommendations.append({
            "topic": "Review primary concepts",
            "reason": "Master the initial structural concepts before moving to complex relationship workflows."
        })
        
    return recommendations
