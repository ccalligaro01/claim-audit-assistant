import streamlit as st
import pandas as pd

# Load core datasets
citation_data = pd.read_csv('Citation_Knowledge_Base.csv')
payer_logic_data = pd.read_csv('Payer_Denial_Logic_Matrix.csv')

# ✅ Load pre-written Q&A
qa_bank_df = pd.read_csv('Cleaned_Custom_QA_Bank.csv')
qa_bank_df['Question'] = qa_bank_df['Question'].astype(str).str.lower().str.strip()

st.title("🩺 AI Claim Audit Assistant (v3 - Q&A Enhanced)")

st.sidebar.header("Upload Claims CSV File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean columns
    df['CPT Code'] = df['CPT Code'].astype(str).str.strip()
    df['Modifier'] = df['Modifier'].astype(str).str.strip()
    df['Denial Reason'] = df['Denial Reason'].astype(str).str.strip()

    st.success(f"Uploaded {uploaded_file.name} successfully!")
    st.dataframe(df)

    st.subheader("📊 Dashboard Overview")
    total_claims = len(df)
    denied_claims = df[df['Denial Reason'] != "None"]
    clean_claims = df[df['Denial Reason'] == "None"]

    st.metric("Total Claims", total_claims)
    st.metric("Flagged Claims (Denials)", len(denied_claims))
    st.metric("Clean Claims", len(clean_claims))

    st.subheader("🔍 Detailed Claim Analysis")
    for _, row in df.iterrows():
        st.markdown("---")
        st.markdown(f"### 🆔 Claim ID: {row['Claim ID']}")
        st.markdown(f"- CPT Code: **{row['CPT Code']}**")
        st.markdown(f"- ICD-10 Code: **{row['ICD-10 Code']}**")
        st.markdown(f"- Modifier: **{row['Modifier']}**")
        st.markdown(f"- Payer: **{row['Payer']}**")
        st.markdown(f"- Billed Amount: ${row['Billed Amount']}")
        st.markdown(f"- Allowed Amount: ${row['Allowed Amount']}")
        st.markdown(f"- Denial Reason: {row['Denial Reason']}")

        if row['Denial Reason'] != "None":
            st.error(f"⚠️ Denial Detected: {row['Denial Reason']}")
            payer_info = payer_logic_data[payer_logic_data['Payer'] == row['Payer']]
            if not payer_info.empty:
                st.markdown(f"**Payer Denial Tip:** {payer_info.iloc[0]['Appeals Tip']}")
                st.markdown(f"**Reference Policy:** {payer_info.iloc[0]['Source Policy']}")

            if pd.notna(row['Denial Reason']) and "Modifier" in row['Denial Reason']:
                citation_info = citation_data[citation_data['Source'].str.contains("Modifier", case=False)]
                if not citation_info.empty:
                    st.markdown("📚 **Relevant Coding Citations:**")
                    for _, cite in citation_info.iterrows():
                        st.markdown(f"- **{cite['Source']}**: {cite['Summary of Rule']} [More Info]({cite['Link or Document']})")
        else:
            st.success("✅ No denial detected!")

# Sidebar Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Built by YOU 🚀")

# Memory
if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []

st.subheader("💬 Ask a Claims Question!")

if uploaded_file is not None:
    user_question = st.chat_input("Ask about a CPT code, modifier, or denial situation...")
    if user_question:
        user_question_lower = user_question.lower().strip()
        st.markdown(f"🔎 **Searching for:** `{user_question}`")
        matches = []

        for _, row in df.iterrows():
            score = 0
            explanation = []
            if user_question_lower in str(row['CPT Code']).lower():
                score += 2
                explanation.append("CPT match")
            if user_question_lower in str(row['Modifier']).lower():
                score += 1
                explanation.append("Modifier match")
            if user_question_lower in str(row['Denial Reason']).lower():
                score += 0.5
                explanation.append("Denial reason match")

            if score > 0:
                matches.append({
                    "Score": score,
                    "Explanation": ", ".join(explanation),
                    "Claim": row
                })

        if matches:
            matches = sorted(matches, key=lambda x: x['Score'], reverse=True)
            st.success(f"✅ Found {len(matches)} matching claims, ranked by relevance!")
            examples_text = ""

            for match in matches:
                example = match["Claim"]
                st.markdown(f"**📋 Example Claim (Score: {match['Score']}, Reason: {match['Explanation']}):**")
                st.markdown(f"- **Claim ID:** {example['Claim ID']}")
                st.markdown(f"- **CPT Code:** {example['CPT Code']}")
                st.markdown(f"- **Modifier:** {example['Modifier']}")
                st.markdown(f"- **ICD-10 Code:** {example['ICD-10 Code']}")
                st.markdown(f"- **Payer:** {example['Payer']}")
                st.markdown(f"- **Denial Reason:** {example['Denial Reason']}")
                st.markdown("---")

                examples_text += f"- (Score {match['Score']}) Claim ID: {example['Claim ID']}, CPT: {example['CPT Code']}, Modifier: {example['Modifier']}, Payer: {example['Payer']}, Denial: {example['Denial Reason']} (Reason: {match['Explanation']})\n"

            st.session_state.qa_history.append({
                "Question": user_question,
                "Answer": f"✅ Found {len(matches)} matching claims ranked by relevance:\n\n{examples_text}"
            })

        else:
            match = qa_bank_df[qa_bank_df['Question'].str.contains(user_question_lower)]
            if not match.empty:
                answer = match.iloc[0]['Answer']
                st.success(f"📘 Preloaded Answer:\n\n{answer}")
                st.session_state.qa_history.append({
                    "Question": user_question,
                    "Answer": answer
                })
            else:
                generated_answer = "⚠️ No matching claims or preloaded answers found. Try rephrasing or using keywords like 'global period' or 'modifier 59'."
                st.warning(generated_answer)
                st.session_state.qa_history.append({
                    "Question": user_question,
                    "Answer": generated_answer
                })

# 🧠 Memory
if st.session_state.qa_history:
    st.subheader("📜 Conversation History (Memory)")
    for entry in st.session_state.qa_history:
        st.markdown(f"**Q:** {entry['Question']}")
        st.markdown(f"**A:** {entry['Answer']}")
        st.markdown("---")
