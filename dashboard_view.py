import streamlit as st
import pandas as pd
import plotly.express as px
from analytics_manager import AnalyticsManager
import os

def render_dashboard():
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            text-align: center;
        }
        .metric-title {
            color: #6c757d;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            color: #4B0082;
            font-size: 32px;
            font-weight: 800;
            margin-top: 10px;
        }
        .level-badge {
            background: linear-gradient(135deg, #9370DB, #6A5ACD);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 My Learning Dashboard")
    st.write("Welcome to your personal AI Learning Command Center.")
    
    am = AnalyticsManager()
    
    # Overview Tab
    tab1, tab2, tab3, tab4 = st.tabs(["Overview & Streaks", "Skill Growth", "Content Library", "Activity Timeline"])
    
    with tab1:
        score, level = am.get_knowledge_score()
        st.markdown(f"### Personal Knowledge Score: **{score:,}** <span class='level-badge'>{level}</span>", unsafe_allow_html=True)
        st.write("")
        
        kpis = am.get_kpi_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Videos Processed</div><div class='metric-value'>{kpis['videos_summarized']}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Hours Learned</div><div class='metric-value'>{kpis['hours_processed']}</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Skills Acquired</div><div class='metric-value'>{kpis['skills_learned']}</div></div>", unsafe_allow_html=True)
        with col4:
            streak = am.get_streak_data()
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Day Streak</div><div class='metric-value'>🔥 {streak['current_streak']}</div></div>", unsafe_allow_html=True)
            
        st.write("")
        st.write("")
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Notes Gen.</div><div class='metric-value'>{kpis['notes_generated']}</div></div>", unsafe_allow_html=True)
        with col6:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Flashcards</div><div class='metric-value'>{kpis['flashcards_generated']}</div></div>", unsafe_allow_html=True)
        with col7:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Quizzes</div><div class='metric-value'>{kpis['quizzes_taken']}</div></div>", unsafe_allow_html=True)
        with col8:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>PDF Exports</div><div class='metric-value'>{kpis['pdf_exports']}</div></div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("💡 AI Learning Insights")
        with st.spinner("Generating insights..."):
            insights = am.generate_ai_insights()
            for insight in insights:
                st.info(f"✨ {insight}")
                
        st.divider()
        st.subheader("🎯 Quiz Performance")
        q_data = am.get_quiz_analytics()
        q1, q2, q3 = st.columns(3)
        q1.metric("Average Score", f"{q_data['avg_score']}%")
        q2.metric("Highest Score", f"{q_data['highest']}%")
        q3.metric("Total Quizzes Taken", q_data['total'])

    with tab2:
        st.subheader("📈 Skill Acquisition Velocity")
        dates, counts = am.get_skill_growth()
        if dates and counts:
            df = pd.DataFrame({'Date': dates, 'Total Skills': counts})
            fig = px.line(df, x='Date', y='Total Skills', markers=True, title="Cumulative Skills Over Time", line_shape='spline')
            fig.update_traces(line_color='#6A5ACD', marker=dict(color='#4B0082', size=8))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skills tracked yet. Use the Resume Learning Mode to extract skills from your videos!")

    with tab3:
        st.subheader("📚 Content Library (Generated Artifacts)")
        # Displaying generated content logs
        am.cursor.execute("SELECT timestamp, content_type, video_id FROM generated_content ORDER BY timestamp DESC")
        data = am.cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=["Date", "Content Type", "Video Source"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Your library is empty. Process a video to start filling it up!")

    with tab4:
        st.subheader("⏱️ Activity Timeline")
        timeline = am.get_activity_timeline(limit=50)
        if timeline:
            for item in timeline:
                st.markdown(f"**{item['timestamp']}** — 🟢 *{item['action']}*")
                st.caption(f"↳ {item['details']}")
                st.write("")
        else:
            st.info("No activity logged yet.")
