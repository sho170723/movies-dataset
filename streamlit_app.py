import streamlit as st
from supabase import create_client, Client

# アプリの設定
st.set_page_config(page_title="J-Rock Quiz with Supabase", page_icon="🎸")

# --- 1. Supabase接続設定 ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. データの読み込み ---
@st.cache_data(ttl=600) # 10分間キャッシュ
def fetch_quiz_data():
    response = supabase.table("quiz_questions").select("*").execute()
    return response.data

quiz_data = fetch_quiz_data()

# --- 3. セッション状態の初期化 ---
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False

# --- 4. クイズ画面 ---
st.title("🎸 邦楽ロック・パンク クイズ (Supabase版)")

if not quiz_data:
    st.error("クイズデータが取得できません。Supabaseのテーブルを確認してください。")
elif st.session_state.current_q >= len(quiz_data):
    st.balloons()
    st.header("全問終了！")
    final_score = st.session_state.score
    total = len(quiz_data)
    st.metric("最終スコア", f"{final_score} / {total}")
    
    # スコアをSupabaseに保存
    if st.button("スコアを記録してリセット"):
        supabase.table("quiz_scores").insert({
            "username": "Guest User", # 必要に応じて入力フォームを作る
            "score": final_score,
            "total_questions": total
        }).execute()
        
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.rerun()
else:
    q = quiz_data[st.session_state.current_q]
    
    st.subheader(f"第 {st.session_state.current_q + 1} 問")
    st.markdown(f"### {q['question']}")
    
    choice = st.radio("答えを選んでください：", q['options'], index=None, key=f"q_{q['id']}")

    if not st.session_state.answered:
        if st.button("回答を確定する"):
            if choice:
                st.session_state.answered = True
                if choice == q['answer']:
                    st.session_state.score += 1
                    st.success("正解！ ✅")
                else:
                    st.error(f"残念！ ❌ 正解は「{q['answer']}」でした。")
                st.rerun()
            else:
                st.warning("選択肢を選んでください。")
    else:
        with st.expander("📝 解説を見る", expanded=True):
            st.write(q['explanation'])
        
        if st.button("次の問題へ"):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.rerun()

# サイドバー
st.sidebar.title("Progress")
st.sidebar.progress(st.session_state.current_q / len(quiz_data) if quiz_data else 0)
