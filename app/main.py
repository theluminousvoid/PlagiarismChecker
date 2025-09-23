from pathlib import Path
from functools import reduce
import json
import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.domain import Document, User, Submission, Rule
from core.transforms import normalize, tokenize, ngrams, jaccard


@st.cache_data
def load_data():
    data_path = Path(__file__).parent.parent / "data" / "seed.json"
    if not data_path.exists():
        raise FileNotFoundError(f"{data_path} не найден")
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    documents = tuple(Document(**doc) for doc in raw.get("documents", []))
    users = tuple(User(**user) for user in raw.get("users", []))
    submissions = tuple(Submission(**sub) for sub in raw.get("submissions", []))
    rules = tuple(Rule(**rule) for rule in raw.get("rules", []))

    return documents, users, submissions, rules, raw


def main():
    st.set_page_config(
        page_title="Проверка оригинальности",
        layout="wide",
    )

    with st.sidebar:
        st.title("Меню навигации")
        page = st.selectbox("Выберите страницу:", ["Overview", "Data", "Functional Core"])
        st.markdown("---")
        st.markdown("**Лаба №1**: Чистые функции + неизменяемость + HOF")

    try:
        documents, users, submissions, rules, raw = load_data()
    except FileNotFoundError as e:
        st.error("Файл data/seed.json не найден!")
        st.info("Создайте файл с тестовыми данными (например, python3 1.py) и перезапустите.")
        st.stop()

    if page == "Overview":
        st.title("Обзор системы")
        total_doc_chars = reduce(lambda acc, d: acc + len(d.text), documents, 0)
        total_sub_chars = reduce(lambda acc, s: acc + len(s.text), submissions, 0)

        avg_doc_length = total_doc_chars / len(documents) if documents else 0
        avg_sub_length = total_sub_chars / len(submissions) if submissions else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Документов", len(documents))
        c2.metric("Пользователей", len(users))
        c3.metric("Проверок", len(submissions))
        c4.metric("Правил", len(rules))

        st.markdown("---")
        c5, c6 = st.columns(2)
        c5.metric("Средняя длина документа", f"{avg_doc_length:.0f} символов")
        c6.metric("Средняя длина проверки", f"{avg_sub_length:.0f} символов")

    elif page == "Data":
        st.title("Просмотр данных")
        tab1, tab2, tab3, tab4 = st.tabs(["Документы", "Пользователи", "Проверки", "Правила"])

        with tab1:
            st.subheader("Эталонные документы")
            for doc in documents[:10]:
                with st.expander(f" {doc.title} (автор: {doc.author})"):
                    st.write(f"**ID:** {doc.id}")
                    st.write(f"**Время:** {doc.ts}")
                    st.write(f"**Текст:** {doc.text}")

            if len(documents) > 10:
                st.info(f"Показаны первые 10 из {len(documents)} документов")

        with tab2:
            st.subheader("Пользователи системы")
            user_names = list(map(lambda u: f" {u.name} (ID: {u.id})", users))
            for name in user_names:
                st.write(name)

        with tab3:
            st.subheader("Проверки текстов")
            for sub in submissions[:10]:
                with st.expander(f" {sub.id} — {sub.user_id}"):
                    st.write(f"**Время:** {sub.ts}")
                    st.write(sub.text)

        with tab4:
            st.subheader("Правила проверки")
            for rule in rules:
                st.write(f"⚙️ **{rule.kind}**: {rule.payload}")

    elif page == "Functional Core":
        st.title("Демонстрация функций")
        st.markdown("Тут мы показываем `normalize`, `tokenize`, `ngrams`, `jaccard` и HOF (map/filter/reduce).")

        test_text = st.text_area(
            "Введите текст для обработки:",
            value="Привет, Мир! Это тестовый текст для демонстрации функций.",
            height=120,
        )

        ngram_n = st.slider("Размер n-граммы для сравнения", 1, 5, 3)

        if test_text is not None:
            st.markdown("---")
            st.subheader("normalize / tokenize / ngrams")
            normalized = normalize(test_text)
            tokens = tokenize(normalized)
            gram = ngrams(tokens, n=ngram_n)

            st.write("**normalize:**", normalized)
            st.write("**tokenize:**", tokens)
            st.write(f"**{ngram_n}-grams:**", gram)

            st.markdown("---")
            st.subheader("map / filter / reduce (демонстрация)")

            token_lengths = list(map(len, tokens))
            filtered_tokens = list(filter(lambda t: len(t) > 2, tokens))
            total_chars = reduce(lambda a, b: a + b, token_lengths, 0)

            st.write("map(len, tokens) ->", token_lengths)
            st.write("filter(len>2) ->", filtered_tokens)
            st.write("reduce(sum lengths) ->", total_chars)

            st.markdown("---")
            st.subheader("Сравнение с документами (по n-граммам)")

            sims = []
            for doc in documents:
                doc_tokens = tokenize(normalize(doc.text))
                doc_grams = ngrams(doc_tokens, n=ngram_n)
                sim = jaccard(gram, doc_grams)
                sims.append((sim, doc))

            sims_sorted = sorted(sims, key=lambda x: x[0], reverse=True)
            top = sims_sorted[:5]

            st.write("Топ-5 похожих документов (по n-граммам):")
            for sim, doc in top:
                st.write(f"- {doc.id} — **{doc.title}** (автор: {doc.author}) — похожесть: {sim:.3f}")

            thr_rule = next((r for r in rules if r.kind == "similarity_threshold"), None)
            if thr_rule:
                thr = thr_rule.payload.get("threshold", 0.0)
                st.info(f"Порог схожести по правилу: {thr} (из rules)")
                if top and top[0][0] >= thr:
                    st.warning("Есть документ с похожестью выше порога!")

if __name__ == "__main__":
    main()
