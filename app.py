import streamlit as st
import pandas as pd
from graph_db import KnowledgeGraph
from llm_extractor import extract_triples

st.set_page_config(page_title="Graph Builder", page_icon="🧠", layout="wide")

st.title("🧠 Knowledge Graph Builder")
st.markdown("Extract knowledge from text using LLMs and store it in a Neo4j Graph Database!")

# Initialize Graph DB connection
@st.cache_resource
def get_db():
    try:
        return KnowledgeGraph()
    except Exception as e:
        st.error(f"Failed to connect to Neo4j. Is it running? Error: {e}")
        return None

db = get_db()

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Extract Knowledge")
    text_input = st.text_area(
        "Enter some text to extract relationships from:", 
        height=200, 
        placeholder="E.g., Elon Musk is the CEO of Tesla and founded SpaceX. Tesla is located in Austin."
    )
    
    if st.button("Extract and Save to Graph", type="primary"):
        if not text_input:
            st.warning("Please enter some text first.")
        elif db is None:
            st.error("Graph DB is not connected. Check your Neo4j configuration.")
        else:
            with st.spinner("Analyzing text with LLM..."):
                try:
                    triples = extract_triples(text_input)
                    
                    if triples:
                        st.success(f"Extracted {len(triples)} relationships!")
                        st.json(triples)
                        
                        with st.spinner("Saving to Neo4j..."):
                            for t in triples:
                                source = t.get('source')
                                relation = t.get('relation', 'RELATED_TO')
                                target = t.get('target')
                                if source and target:
                                    db.add_relationship(source, relation, target)
                        st.success("Successfully saved to Graph DB! 👉 Check the view on the right.")
                    else:
                        st.warning("No relationships were found in the text.")
                except Exception as e:
                    st.error(f"Failed to extract relationships: {e}")

with col2:
    st.subheader("2. View Interactive Graph")
    st.markdown("Here is the visual representation of your Graph Database.")
    
    if st.button("Refresh Graph View"):
        if db is not None:
            try:
                triples = db.get_all_triples()
                if triples:
                    from pyvis.network import Network
                    import streamlit.components.v1 as components
                    import tempfile
                    import os
                    
                    # Create a PyVis network
                    net = Network(height='500px', width='100%', directed=True, bgcolor='#ffffff', font_color='#333333')
                    
                    # Add nodes and edges
                    added_nodes = set()
                    for t in triples:
                        src = t['source']
                        tgt = t['target']
                        rel = t['relation']
                        
                        if src not in added_nodes:
                            net.add_node(src, label=src, color="#4A90E2", size=25)
                            added_nodes.add(src)
                        if tgt not in added_nodes:
                            net.add_node(tgt, label=tgt, color="#50E3C2", size=25)
                            added_nodes.add(tgt)
                            
                        net.add_edge(src, tgt, title=rel, label=rel, color="#999999", arrows="to")
                    
                    # Turn on some physics for a cooler layout
                    net.toggle_physics(True)
                    
                    # Save and render the graph
                    path = os.path.join(os.getcwd(), 'graph.html')
                    net.save_graph(path)
                    
                    with open(path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                        
                    # Display in Streamlit
                    st.components.v1.html(source_code, height=520)
                else:
                    st.info("The graph is currently empty. Extract some text on the left first!")
            except Exception as e:
                st.error(f"Failed to fetch or render graph: {e}")
