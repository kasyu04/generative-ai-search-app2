"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")

def display_select_mode():
    """
    回答モードのラジオボタンを表示
    """
    with st.sidebar:
        st.radio(
            "利用目的を選択してください",
            options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
            index=0,
            key="mode"
        )
        st.markdown('<div style="background-color: #e0f7fa; padding: 10px; border-radius: 5px;">'
                    '<strong>【「社内文書検索」をした場合】</strong><br>'
                    '入力内容と関連性が高い社内文書のありかを検索できます。</div>', unsafe_allow_html=True)
        st.markdown('<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
                    '<strong>【入力例】</strong><br>'
                    '- 社員の育成方針に関するMTGの議事録</div>', unsafe_allow_html=True)
        st.markdown('<div style="background-color: #e0f7fa; padding: 10px; border-radius: 5px;">'
                    '<strong>【「社内問い合わせ」を選択した場合】</strong><br>'
                    '質問・要望に対して、社内文書の情報を元に回答を得られます。</div>', unsafe_allow_html=True)
        st.markdown('<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px;">'
                    '<strong>【入力例】</strong><br>'
                    '- 人事部に所属している従業員の情報を一覧化して</div>', unsafe_allow_html=True)


def display_initial_ai_message():
    """
    AIメッセージの初期表示
    """
    with st.chat_message("assistant"):
        st.markdown("こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。上記で利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。")
        st.markdown('<div style="background-color: #fff3cd; padding: 10px; border-radius: 5px;">'
                    '⚠具体的に入力したほうが期待通りの回答を得やすいです</div>', unsafe_allow_html=True)


def display_conversation_log():
    """
    会話ログの一覧表示
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:
        main_file_path = llm_response["context"][0].metadata["source"]
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        icon = utils.get_source_icon(main_file_path)
        if "page" in llm_response["context"][0].metadata:
            main_page_number = llm_response["context"][0].metadata["page"]
            st.success(f"{main_file_path} (ページ {main_page_number})", icon=icon)
        else:
            st.success(f"{main_file_path}", icon=icon)

        sub_choices = []
        duplicate_check_list = []
        for document in llm_response["context"][1:]:
            sub_file_path = document.metadata["source"]
            if sub_file_path == main_file_path or sub_file_path in duplicate_check_list:
                continue
            duplicate_check_list.append(sub_file_path)
            if "page" in document.metadata:
                sub_page_number = document.metadata["page"]
                sub_choice = {"source": sub_file_path, "page_number": sub_page_number}
            else:
                sub_choice = {"source": sub_file_path}
            sub_choices.append(sub_choice)

        if sub_choices:
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)
            for sub_choice in sub_choices:
                icon = utils.get_source_icon(sub_choice['source'])
                if "page_number" in sub_choice:
                    st.info(f"{sub_choice['source']} (ページ {sub_choice['page_number']})", icon=icon)
                else:
                    st.info(f"{sub_choice['source']}", icon=icon)

        content = {
            "mode": ct.ANSWER_MODE_1,
            "main_message": main_message,
            "main_file_path": main_file_path,
        }
        if "page" in llm_response["context"][0].metadata:
            content["main_page_number"] = main_page_number
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices
    else:
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)
        content = {
            "mode": ct.ANSWER_MODE_1,
            "answer": ct.NO_DOC_MATCH_MESSAGE,
            "no_file_path_flg": True,
        }
    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    st.markdown(llm_response["answer"])
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        st.divider()
        message = "情報源"
        st.markdown(f"##### {message}")
        file_path_list = []
        file_info_list = []
        for document in llm_response["context"]:
            file_path = document.metadata["source"]
            if file_path in file_path_list:
                continue
            if "page" in document.metadata:
                page_number = document.metadata["page"]
                file_info = f"{file_path} (ページ {page_number})"
            else:
                file_info = f"{file_path}"
            icon = utils.get_source_icon(file_path)
            st.info(file_info, icon=icon)
            file_path_list.append(file_path)
            file_info_list.append(file_info)

    content = {
        "mode": ct.ANSWER_MODE_2,
        "answer": llm_response["answer"],
    }
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content