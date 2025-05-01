# ------------------------------
# 💬 Chat Feature with Custom Q&A Bank
# ------------------------------

# Load Custom Q&A CSV once per session
if 'qa_bank' not in st.session_state:
    try:
        qa_data = pd.read_csv("Custom_QA_Bank.csv")
        qa_data['Question'] = qa_data['Question'].astype(str).str.lower().str.strip()
        st.session_state.qa_bank = qa_data
    except FileNotFoundError:
        st.session_state.qa_bank = pd.DataFrame(columns=['Question', 'Answer'])

if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []

st.subheader("💬 Ask a Claims Question!")

if uploaded_file is not None:
    user_question = st.chat_input("Ask about a CPT code, modifier, denial reason, or concept...")

    if user_question:
        user_question_lower = user_question.lower().strip()
        st.markdown(f"🔎 **Searching for:** `{user_question}`")

        # --- 1. Search for claim matches ---
        matches = []
        for idx, row in df.iterrows():
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

        # --- 2. Return top-ranked matches if any ---
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
            # --- 3. Fallback to Q&A bank ---
            bank_matches = st.session_state.qa_bank[
                st.session_state.qa_bank['Question'].str.contains(user_question_lower, case=False, na=False)
            ]

            if not bank_matches.empty:
                answer = bank_matches.iloc[0]['Answer']
                st.success(f"📘 Preloaded Answer:\n\n{answer}")
                st.session_state.qa_history.append({
                    "Question": user_question,
                    "Answer": answer
                })
            else:
                generated_answer = "⚠️ No matching claims or preloaded answers found. Try rephrasing or using keywords like 'modifier 59' or 'global period'."
                st.warning(generated_answer)
                st.session_state.qa_history.append({
                    "Question": user_question,
                    "Answer": generated_answer
                })

# 🧠 Conversation memory
if st.session_state.qa_history:
    st.subheader("📜 Conversation History (Memory)")
    for entry in st.session_state.qa_history:
        st.markdown(f"**Q:** {entry['Question']}")
        st.markdown(f"**A:** {entry['Answer']}")
        st.markdown("---")
