"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import constants as ct
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI


############################################################
# 設定関連
############################################################
# 「.env」ファイルで定義した環境変数の読み込み
load_dotenv()


############################################################
# 関数定義
############################################################

def get_source_icon(source):
    """
    メッセージと一緒に表示するアイコンの種類を取得

    Args:
        source: 参照元のありか

    Returns:
        メッセージと一緒に表示するアイコンの種類
    """
    # 参照元がWebページの場合とファイルの場合で、取得するアイコンの種類を変える
    if source.startswith("http"):
        icon = ct.LINK_SOURCE_ICON
    else:
        icon = ct.DOC_SOURCE_ICON
    
    return icon


def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def get_llm_response(chat_message):
    """
    LLMからの回答を取得する関数
    Args:
        chat_message: ユーザーからのメッセージ
    Returns:
        llm_response: LLMからの回答
    """
    # ベクターストアの設定
    loader = CSVLoader(file_path="data/documents.csv", encoding='utf-8')
    docs = loader.load()

    docs_contents = []
    for doc in docs:
        docs_contents.append(doc.page_content)

    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(docs, embedding=embeddings)

    retriever = db.as_retriever(search_kwargs={"k": ct.NUM_RELATED_DOCUMENTS})  # 定数を使用
    bm25_retriever = BM25Retriever.from_texts(
        docs_contents,
        preprocess_func=preprocess_func,
        k=ct.NUM_RELATED_DOCUMENTS  # 定数を使用
    )
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, retriever],
        weights=[0.5, 0.5]
    )

    # RetrievalQAの設定
    llm = OpenAI(model_name="gpt-4", temperature=0.5)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=ensemble_retriever,
        return_source_documents=True
    )

    # ユーザーメッセージに対する回答を取得
    result = qa_chain({"query": chat_message})
    llm_response = result["result"]

    return llm_response