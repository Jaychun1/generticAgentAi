import streamlit as st
import pandas as pd
import json

from config import Config
from services.api_client import api_client

def show_sql_page():
    """Display SQL query interface page"""
    
    st.header("🗄️ SQL Query Interface")
    st.markdown("Query employee and HR database using natural language or SQL")
    
    # Create tabs for different interfaces
    tab1, tab2, tab3 = st.tabs(["📝 Query", "📊 Schema", "📈 Analytics"])
    
    with tab1:
        # Query interface
        st.subheader("Database Query")
        
        # Query input
        query_input = st.text_area(
            "Enter your query (natural language or SQL):",
            height=150,
            placeholder="Example: 'Show me all employees in the Engineering department earning more than $100,000'",
            help="You can use natural language or direct SQL queries"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)
        
        with col2:
            if st.button("🔄 Validate", use_container_width=True):
                st.info("Query validation coming soon!")
        
        with col3:
            if st.button("📋 Examples", use_container_width=True):
                st.session_state.show_examples = True
        
        # Query examples
        if st.session_state.get('show_examples'):
            with st.expander("📚 Query Examples", expanded=True):
                examples = [
                    "Show top 10 highest paid employees",
                    "Count employees by department",
                    "Average salary by job title",
                    "Employees hired in the last year",
                    "Department with highest average salary",
                    "List all managers and their direct reports"
                ]
                
                for example in examples:
                    if st.button(example, key=f"example_{example}"):
                        st.session_state.query_input = example
                        st.rerun()
        
        # Execute query
        if execute_button and query_input:
            with st.spinner("Executing query..."):
                result = api_client.sql_query(
                    query=query_input,
                    session_id=st.session_state.get('current_session_id')
                )
                
                if "error" in result:
                    st.error(f"Query failed: {result['error']}")
                    
                    # Show error details
                    with st.expander("🔍 Error Details"):
                        st.code(json.dumps(result, indent=2), language="json")
                else:
                    st.success("✅ Query executed successfully!")
                    
                    # Display results
                    if result.get("results"):
                        st.subheader("📋 Results")
                        
                        # Try to display as table
                        try:
                            # If results are in a structured format
                            if isinstance(result["results"], list):
                                df = pd.DataFrame(result["results"])
                                st.dataframe(df, use_container_width=True)
                                
                                # Show statistics
                                st.metric("Rows Returned", len(df))
                                
                                # Download button
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name="query_results.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.json(result["results"])
                        except:
                            st.write(result["results"])
                    
                    # Show query metadata
                    if result.get("metadata"):
                        with st.expander("📊 Query Metadata"):
                            st.json(result["metadata"])
    
    with tab2:
        # Database schema
        st.subheader("📊 Database Schema")
        
        if st.button("🔄 Refresh Schema"):
            st.session_state.schema_refresh = True
        
        # Display schema information
        schema_info = """
        ### Employees Database Schema
        
        **Tables:**
        
        1. **employees**
           - employee_id (INT, PRIMARY KEY)
           - first_name (VARCHAR)
           - last_name (VARCHAR)
           - email (VARCHAR)
           - phone (VARCHAR)
           - hire_date (DATE)
           - job_id (INT, FOREIGN KEY)
           - salary (DECIMAL)
           - manager_id (INT, FOREIGN KEY)
           - department_id (INT, FOREIGN KEY)
        
        2. **departments**
           - department_id (INT, PRIMARY KEY)
           - department_name (VARCHAR)
           - location_id (INT, FOREIGN KEY)
        
        3. **jobs**
           - job_id (INT, PRIMARY KEY)
           - job_title (VARCHAR)
           - min_salary (DECIMAL)
           - max_salary (DECIMAL)
        
        4. **locations**
           - location_id (INT, PRIMARY KEY)
           - street_address (VARCHAR)
           - postal_code (VARCHAR)
           - city (VARCHAR)
           - state_province (VARCHAR)
           - country_id (CHAR)
        
        5. **countries**
           - country_id (CHAR, PRIMARY KEY)
           - country_name (VARCHAR)
           - region_id (INT, FOREIGN KEY)
        
        6. **regions**
           - region_id (INT, PRIMARY KEY)
           - region_name (VARCHAR)
        """
        
        st.markdown(schema_info)
        
        # Visual schema
        with st.expander("🕸️ Schema Diagram"):
            st.image("https://via.placeholder.com/800x400?text=Database+Schema+Diagram", 
                    caption="Database Schema Diagram")
    
    with tab3:
        # Analytics dashboard
        st.subheader("📈 Database Analytics")
        
        # Pre-built analytics queries
        analytics_queries = {
            "Employee Distribution": "Count employees by department",
            "Salary Statistics": "Average, min, max salary by job title",
            "Hiring Trends": "Employees hired by year and month",
            "Manager Hierarchy": "Count of employees per manager",
            "Salary Bands": "Distribution of salaries in $10k bands"
        }
        
        selected_analytics = st.selectbox(
            "Choose Analytics View:",
            list(analytics_queries.keys())
        )
        
        if st.button("📊 Generate Report"):
            query = analytics_queries[selected_analytics]
            
            with st.spinner(f"Generating {selected_analytics}..."):
                result = api_client.sql_query(
                    query=query,
                    session_id=st.session_state.get('current_session_id')
                )
                
                if "error" not in result and result.get("results"):
                    st.success(f"✅ {selected_analytics} Report")
                    
                    # Display chart if data is suitable
                    try:
                        df = pd.DataFrame(result["results"])
                        
                        if len(df) > 0:
                            # Choose appropriate chart based on data
                            if selected_analytics == "Employee Distribution":
                                st.bar_chart(df.set_index(df.columns[0]))
                            elif selected_analytics == "Salary Statistics":
                                st.line_chart(df.set_index(df.columns[0]))
                            elif selected_analytics == "Hiring Trends":
                                st.area_chart(df.set_index(df.columns[0]))
                            
                            # Show raw data
                            with st.expander("📋 Raw Data"):
                                st.dataframe(df)
                    except:
                        st.write(result["results"])

def show_query_history():
    """Display query history"""
    st.sidebar.subheader("📜 Query History")
    
    # Placeholder for query history
    if st.sidebar.button("Clear History"):
        st.sidebar.success("History cleared!")
