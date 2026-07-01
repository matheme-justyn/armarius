"""Common UI components for Armarius Streamlit app.

This module provides shared UI elements (sidebar, i18n) used across all pages.
"""

from pathlib import Path
from typing import Dict, Any

import streamlit as st
import toml

from armarius.config import ArmariusConfig


class I18n:
    """Simple i18n handler for Streamlit UI."""

    def __init__(self, locale: str = "en-US"):
        """Initialize i18n with specified locale.

        Args:
            locale: BCP 47 language tag (e.g., "en-US", "zh-TW")
        """
        self.locale = locale
        self.translations = self._load_translations(locale)
        self.fallback = self._load_translations("en-US") if locale != "en-US" else {}

    def _load_translations(self, locale: str) -> Dict[str, Any]:
        """Load translations from i18n/locales/{locale}/app.toml.

        Args:
            locale: Language code

        Returns:
            Translation dictionary
        """
        # Get project root (parent of armarius package)
        project_root = Path(__file__).parent.parent
        translation_file = project_root / "i18n" / "locales" / locale / "app.toml"

        if translation_file.exists():
            return toml.load(translation_file)
        return {}

    def t(self, key: str, **kwargs) -> str:
        """Get translated string by dot-separated key.

        Args:
            key: Dot-separated translation key (e.g., "page.title")
            **kwargs: Variables to format into the string

        Returns:
            Translated and formatted string

        Example:
            >>> i18n.t("search.showing", count=5, total=10)
            "Showing 5 of 10 files"
        """
        keys = key.split(".")
        value = self.translations

        # Try to get from current locale
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Fallback to English
                value = self.fallback
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return key  # Return key itself if not found

        # Format with variables if provided
        if isinstance(value, str) and kwargs:
            return value.format(**kwargs)
        return value


def render_sidebar_settings(config: ArmariusConfig, i18n: I18n):
    """Render common sidebar settings (language, theme) on all pages.

    This function should be called by all pages to ensure consistent sidebar.

    Args:
        config: ArmariusConfig instance
        i18n: I18n instance for translations
    """
    # Language selector
    st.subheader(i18n.t("sidebar.settings_header"))

    languages = {
        "en-US": "English (US)",
        "zh-TW": "繁體中文（台灣）",
    }
    selected_lang = st.selectbox(
        i18n.t("sidebar.language_label"),
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(st.session_state.locale),
        key="language_selector",
    )

    # Update locale if changed
    if selected_lang != st.session_state.locale:
        st.session_state.locale = selected_lang
        st.rerun()

    # Theme selector
    themes = {
        "light": i18n.t("theme.light"),
    }
    saved_theme = st.session_state.theme if st.session_state.theme in themes else "light"
    selected_theme = st.selectbox(
        i18n.t("sidebar.theme_label"),
        options=list(themes.keys()),
        format_func=lambda x: themes[x],
        index=list(themes.keys()).index(saved_theme),
        key="theme_selector",
    )

    # Update theme if changed
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    # Save preferences button
    if st.button(
        i18n.t("sidebar.save_preferences_button")
        if i18n.t("sidebar.save_preferences_button") != "sidebar.save_preferences_button"
        else "💾 儲存偏好設定",
        width="stretch",
    ):
        config.set("i18n.locale", st.session_state.locale)
        config.set("theme.mode", st.session_state.theme)
        config.save()
        st.success(
            i18n.t("messages.preferences_saved")
            if i18n.t("messages.preferences_saved") != "messages.preferences_saved"
            else "✅ 偏好設定已儲存"
        )

    st.divider()

    # Display Armarius version at bottom
    from armarius import __version__

    st.caption(f"📦 {i18n.t('sidebar.app_version')}: v{__version__}")


def apply_theme(theme_mode: str) -> None:
    """Apply the selected theme mode to the Streamlit app.

    Args:
        theme_mode: Theme mode string: ``light``, ``dark``, or ``auto``.
    """
    effective_mode = theme_mode if theme_mode in {"light", "dark"} else "light"

    chip_background = "rgba(56, 189, 248, 0.16)" if effective_mode == "dark" else "rgba(37, 99, 235, 0.12)"
    nav_background = "rgba(148, 163, 184, 0.12)" if effective_mode == "dark" else "rgba(15, 23, 42, 0.04)"

    if effective_mode == "dark":
        background = "#0f172a"
        secondary_background = "#111827"
        card_background = "#111827"
        header_background = "rgba(15, 23, 42, 0.92)"
        surface_background = "#111827"
        text_color = "#e5e7eb"
        muted_text = "#94a3b8"
        border_color = "rgba(148, 163, 184, 0.25)"
        accent = "#38bdf8"
    else:
        background = "#f6f8fb"
        secondary_background = "#f3f6fa"
        card_background = "#ffffff"
        text_color = "#0f172a"
        muted_text = "#475569"
        border_color = "rgba(15, 23, 42, 0.10)"
        accent = "#2563eb"
        header_background = "rgba(246, 248, 251, 0.92)"
        surface_background = "#ffffff"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {background};
            color: {text_color};
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background: {background};
        }}
        [data-testid="stHeader"] {{
            background: {header_background};
            border-bottom: 1px solid {border_color};
        }}
        .stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stMarkdown, .stText, .stCaption {{
            color: {text_color};
        }}
        [data-testid="stSidebar"] {{
            background: {secondary_background};
            border-right: 1px solid {border_color};
        }}
        [data-testid="stSidebar"], [data-testid="stSidebar"] * {{
            color: {text_color};
        }}
        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stAlert"],
        div[data-testid="stCodeBlock"],
        .stDataFrame,
        div[data-testid="stMarkdownContainer"] > div:has(> .armarius-panel) {{
            background: {surface_background};
        }}
        div[data-testid="stMetric"] {{
            background: {card_background};
            border: 1px solid {border_color};
            border-radius: 14px;
            padding: 0.9rem 1rem;
        }}
        div[data-testid="stMetric"] *,
        div[data-testid="stExpander"] *,
        .stAlert *,
        .stDataFrame *,
        table, th, td {{
            color: {text_color};
        }}
        div[data-testid="stExpander"] {{
            border: 1px solid {border_color};
            border-radius: 14px;
            background: {card_background};
        }}
        .stDataFrame,
        [data-testid="stDataFrame"] {{
            border: 1px solid {border_color};
            border-radius: 14px;
            overflow: hidden;
            background: {surface_background};
        }}
        input, textarea, select,
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background: {card_background} !important;
            color: {text_color} !important;
            border-color: {border_color} !important;
        }}
        code, pre {{
            color: {text_color} !important;
            background: {surface_background} !important;
        }}
        div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button,
        div.stButton > button {{
            border-radius: 10px;
            color: {text_color};
            border: 1px solid {border_color};
            background: {card_background};
        }}
        div.stButton > button:hover {{
            border-color: rgba(37, 99, 235, 0.25);
            color: {accent};
        }}
        .armarius-panel {{
            background: {card_background};
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }}
        .armarius-panel h3, .armarius-panel h4, .armarius-panel p, .armarius-panel li {{
            color: {text_color};
        }}
        .armarius-muted {{
            color: {muted_text};
        }}
        .armarius-chip {{
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: {chip_background};
            color: {accent};
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }}
        .armarius-card-title {{
            margin-bottom: 0.25rem;
            font-weight: 700;
        }}
        .armarius-card-body {{
            color: {muted_text};
            min-height: 2.8rem;
            margin-bottom: 0.75rem;
        }}
        div[role="radiogroup"] {{
            background: {nav_background};
            border: 1px solid {border_color};
            border-radius: 14px;
            padding: 0.35rem;
            gap: 0.35rem;
        }}
        div[role="radiogroup"] label {{
            background: {card_background};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 0.2rem 0.8rem;
        }}
        .armarius-sidebar-section {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {muted_text};
            margin-top: 0.35rem;
            margin-bottom: 0.35rem;
        }}
        .armarius-hero {{
            background: linear-gradient(135deg, {card_background} 0%, {secondary_background} 100%);
            border: 1px solid {border_color};
            border-radius: 18px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 1rem;
        }}
        @media (prefers-color-scheme: dark) {{
            .armarius-auto-note {{
                color: #94a3b8;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
