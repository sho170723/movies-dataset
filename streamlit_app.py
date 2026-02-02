import streamlit as st
from supabase import create_client, Client

# アプリの基本設定
st.set_page_config(page_title="J-Rock & Punk Quiz Master", page_icon="🎸")

# --- 1. Supabase接続設定 ---
# Streamlit CloudのSecretsに設定したURLとKEYを読み込みます
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Secretsの設定が見つかりません。Streamlit CloudのSettingsを確認してください。")
        return None

supabase = init_connection()

# --- 2. データの読み込み ---
@st.cache_data(ttl=600) # 10分間キャッシュを保持
def fetch_quiz_data():
    if supabase:
        try:
            # quiz_questionsテーブルから全データを取得
            response = supabase.table("quiz_questions").select("*").order("id").execute()
            return response.data
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            return []
    return []

quiz_data = fetch_quiz_data()

# --- 3. セッション状態（一時保存データ）の初期化 ---
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = False

# --- 4. クイズ画面の構成 ---
st.title("🎸 邦楽ロック・パンク クイズ")
st.caption("Supabase連携版 - データの永続化を実現")

# データが空の場合の警告
if not quiz_data:
    st.warning("現在クイズデータがありません。SupabaseのテーブルにデータをInsertしてください。")
    st.info("SQL Editorでデータを追加すると、ここに問題が表示されます。")

# 全問解き終わった後の処理
elif st.session_state.current_q >= len(quiz_data):
    st.balloons()
    st.header("🎉 全問終了！")
    final_score = st.session_state.score
    total = len(quiz_data)
    
    col1, col2 = st.columns(2)
    col1.metric("あなたの正解数", f"{final_score} / {total}")
    col2.metric("正解率", f"{(final_score/total)*100:.1f}%")

    st.divider()
    
    # --- スコア記録機能 ---
    st.subheader("ランキングに記録する")
    user_name = st.text_input("ニックネームを入力してください", "名無しさん")
    
    if st.button("スコアをSupabaseに保存してリセット"):
        try:
            # quiz_scoresテーブルにデータを挿入
            supabase.table("quiz_scores").insert({
                "username": user_name,
                "score": final_score,
                "total_questions": total
            }).execute()
            st.success(f"{user_name}さんのスコアを保存しました！")
        except Exception as e:
            st.error(f"スコア保存失敗: {e}")
        
        # セッションをリセットして最初に戻る
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.rerun()

# クイズ進行中の表示
else:
    q = quiz_data[st.session_state.current_q]
    
    st.subheader(f"第 {st.session_state.current_q + 1} 問")
    st.markdown(f"### {q['question']}")
    
    # 選択肢ボタン（Supabaseの配列データをそのまま利用）
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
        # 解説の表示
        with st.expander("📝 解説を見る", expanded=True):
            st.write(q['explanation'])
        
        if st.button("次の問題へ"):
            st.session_state.current_q += 1
            st.session_state.answered = False
            st.rerun()

# --- 5. サイドバー（進行状況） ---
st.sidebar.title("🎮 Status")
if quiz_data:
    progress_val = st.session_state.current_q / len(quiz_data)
    st.sidebar.progress(progress_val)
    st.sidebar.write(f"進行度: {st.session_state.current_q} / {len(quiz_data)}")
    st.sidebar.write(f"現在のスコア: {st.session_state.score}")
