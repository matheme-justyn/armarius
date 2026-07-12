"""Page-level render helpers for the Streamlit UI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from armarius.config import ArmariusConfig
from armarius.ui_common import I18n


def render_analysis_task_frame(i18n: I18n) -> None:
    with st.container(border=True):
        st.markdown("**What this step is for**" if i18n.locale != "zh-TW" else "**這一步在做什麼**")
        st.markdown(
            "- Turn a prepared paper folder into structured reading outputs.\n- Choose only the paradigms you actually want to compare or carry forward.\n- Finish here when you have analysis cards worth reusing in synthesis."
            if i18n.locale != "zh-TW"
            else "- 把已整理好的論文資料夾轉成可重用的結構化閱讀成果。\n- 只選這次真的要比較或延伸的派典。\n- 當你拿到可用的 analysis cards，就算這一步完成。"
        )
        st.caption(
            "Good input: accepted / normalized material with a clear folder target."
            if i18n.locale != "zh-TW"
            else "好的輸入狀態：材料已 accepted / normalized，且你知道這次要分析哪個資料夾。"
        )


def render_analysis_done_signal(i18n: I18n) -> None:
    with st.container(border=True):
        st.markdown("**Done signal**" if i18n.locale != "zh-TW" else "**完成判斷**")
        st.markdown(
            "- You have generated cards for the paradigms that matter.\n- You can already tell which analyses are worth carrying into an output draft.\n- If inputs still feel messy, go back to Library instead of forcing this step."
            if i18n.locale != "zh-TW"
            else "- 你已經為這次重要的派典生成分析卡。\n- 你已經能判斷哪些分析值得帶進輸出初稿。\n- 如果輸入材料還很亂，先回 Library，不要硬做這一步。"
        )


def render_synthesis_task_frame(i18n: I18n) -> None:
    with st.container(border=True):
        st.markdown("**What this step is for**" if i18n.locale != "zh-TW" else "**這一步在做什麼**")
        st.markdown(
            "- Turn existing analysis outputs into a usable draft for a reader or task.\n- Choose a concerto that matches the kind of handoff you need.\n- Finish here when you have a draft that can be edited instead of a blank page."
            if i18n.locale != "zh-TW"
            else "- 把既有 analysis outputs 整理成可交付給特定讀者或任務使用的初稿。\n- 選擇符合這次交付目標的 concerto。\n- 當你拿到一份可編修、不是空白頁的 draft，就算這一步完成。"
        )
        st.caption(
            "Good input: analysis cards already exist and you know what kind of output you need next."
            if i18n.locale != "zh-TW"
            else "好的輸入狀態：analysis cards 已存在，而且你知道下一步想產出哪種型態的內容。"
        )


def render_synthesis_done_signal(i18n: I18n) -> None:
    with st.container(border=True):
        st.markdown("**Done signal**" if i18n.locale != "zh-TW" else "**完成判斷**")
        st.markdown(
            "- You have a draft that matches a real reader or output target.\n- The next work is editing and strengthening, not starting from zero.\n- If the draft feels weak because the source base is weak, go back upstream."
            if i18n.locale != "zh-TW"
            else "- 你已經有一份對應真實讀者或輸出目標的初稿。\n- 下一步是編修與補強，而不是從零開始。\n- 如果初稿太弱是因為材料太弱，就回上游補強。"
        )


def render_settings_intro(config: ArmariusConfig, i18n: I18n, library_root: Path) -> None:
    st.header("Settings" if i18n.locale != "zh-TW" else "設定")
    st.caption(
        "Use this page only when you need to confirm the active workspace, config file location, language, or theme. It is not part of the main research flow."
        if i18n.locale != "zh-TW"
        else "只有在你要確認目前工作區、設定檔位置、語言或主題時，才需要來這一頁；它不屬於主要研究流程。"
    )
    with st.container(border=True):
        st.caption("Current workspace" if i18n.locale != "zh-TW" else "目前工作區")
        st.code(str(library_root), language="text")
        st.caption(f"Config: {config.config_path}")
