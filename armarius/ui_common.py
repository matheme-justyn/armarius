"""Common UI components for Cardex Streamlit app.

This module provides shared UI elements (sidebar, i18n) used across all pages.
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Any
import toml

from armarius.config import CardexConfig


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
        # Get project root (parent of cardex package)
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


def render_sidebar_settings(config: CardexConfig, i18n: I18n):
    """Render common sidebar settings (language, theme) on all pages.

    This function should be called by all pages to ensure consistent sidebar.

    Args:
        config: CardexConfig instance
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
        "dark": i18n.t("theme.dark"),
        "auto": i18n.t("theme.auto"),
    }
    selected_theme = st.selectbox(
        i18n.t("sidebar.theme_label"),
        options=list(themes.keys()),
        format_func=lambda x: themes[x],
        index=list(themes.keys()).index(st.session_state.theme),
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
        use_container_width=True,
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

    # Display Cardex version at bottom
    from armarius import __version__

    st.caption(f"📦 {i18n.t('sidebar.app_version')}: v{__version__}")
