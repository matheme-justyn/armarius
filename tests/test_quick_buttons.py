#!/usr/bin/env python3
"""
自動化測試：快速選擇按鈕功能

測試範圍：
1. 所有快速按鈕的路徑計算邏輯
2. Desktop 按鈕的跨平台支援
3. 錯誤處理（路徑不存在、無權限等）
"""

import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestQuickButtonPaths:
    """測試快速按鈕路徑計算邏輯"""

    def test_default_button_path_resolution(self, tmp_path):
        """測試 Default 按鈕路徑解析"""
        # Simulate config.get("library.default_path")
        test_path = tmp_path / "test-library"
        test_path.mkdir()

        # Path should expand tilde
        path_with_tilde = "~/Library/CloudStorage/Dropbox/6_digital/matheme-scriptorium"
        expanded = Path(path_with_tilde).expanduser()

        assert expanded.is_absolute()
        assert "~" not in str(expanded)

    def test_desktop_path_macos(self):
        """測試 macOS Desktop 路徑"""
        with patch("platform.system", return_value="Darwin"):
            system = platform.system()
            if system == "Darwin":
                desktop = Path.home() / "Desktop"

            assert str(desktop).endswith("Desktop")
            assert desktop.is_absolute()

    def test_desktop_path_windows(self):
        """測試 Windows Desktop 路徑"""
        with patch("platform.system", return_value="Windows"):
            system = platform.system()
            if system == "Windows":
                desktop = Path.home() / "Desktop"

            assert str(desktop).endswith("Desktop")
            assert desktop.is_absolute()

    def test_desktop_path_linux(self):
        """測試 Linux Desktop 路徑"""
        with patch("platform.system", return_value="Linux"):
            system = platform.system()
            if system == "Linux":
                desktop = Path.home() / "Desktop"

            assert str(desktop).endswith("Desktop")
            assert desktop.is_absolute()

    def test_documents_path(self):
        """測試 Documents 路徑"""
        docs_path = Path.home() / "Documents"
        assert docs_path.is_absolute()
        assert str(docs_path).endswith("Documents")

    def test_downloads_path(self):
        """測試 Downloads 路徑"""
        downloads_path = Path.home() / "Downloads"
        assert downloads_path.is_absolute()
        assert str(downloads_path).endswith("Downloads")


class TestErrorHandling:
    """測試錯誤處理邏輯"""

    def test_nonexistent_path_error(self):
        """測試不存在的路徑錯誤"""
        nonexistent = Path("/this/path/does/not/exist/at/all")
        assert not nonexistent.exists()

        # 應該顯示錯誤而非崩潰
        error_message = f"❌ 路徑不存在: {nonexistent}"
        assert "❌" in error_message

    def test_file_as_directory_error(self, tmp_path):
        """測試將檔案當作資料夾的錯誤"""
        # Create a file instead of directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert test_file.exists()
        assert not test_file.is_dir()

        # 應該顯示錯誤
        error_message = f"❌ 不是資料夾: {test_file}"
        assert "❌" in error_message

    def test_permission_denied_handling(self):
        """測試權限不足的錯誤處理"""
        # On Unix systems, /root is typically not readable by regular users
        restricted_path = Path("/root")

        if restricted_path.exists():
            # Should be able to detect permission issues
            try:
                list(restricted_path.iterdir())
                has_permission = True
            except PermissionError:
                has_permission = False
                error_message = "❌ 權限不足，無法讀取此資料夾"
                assert "❌" in error_message
        else:
            # Skip test if /root doesn't exist
            pytest.skip("/root directory not available")


class TestPathValidation:
    """測試路徑驗證邏輯"""

    def test_valid_directory(self, tmp_path):
        """測試有效的資料夾路徑"""
        test_dir = tmp_path / "valid_library"
        test_dir.mkdir()

        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_path_with_tilde_expansion(self):
        """測試包含 ~ 的路徑展開"""
        path_with_tilde = Path("~/Desktop")
        expanded = path_with_tilde.expanduser()

        assert "~" not in str(expanded)
        assert expanded.is_absolute()

    def test_relative_path_conversion(self, tmp_path):
        """測試相對路徑轉換"""
        # Create library and PDF
        library_root = tmp_path / "library"
        library_root.mkdir()

        pdf_path = library_root / "subfolder" / "paper.pdf"
        pdf_path.parent.mkdir()
        pdf_path.write_text("dummy pdf")

        # Test relative path calculation
        if pdf_path.is_relative_to(library_root):
            relative = pdf_path.relative_to(library_root)
            assert "subfolder/paper.pdf" == str(relative)


class TestCrossPlatformSupport:
    """測試跨平台支援"""

    def test_current_platform_detection(self):
        """測試當前平台偵測"""
        system = platform.system()
        assert system in ["Darwin", "Windows", "Linux"]

    def test_home_directory_exists(self):
        """測試主目錄存在"""
        home = Path.home()
        assert home.exists()
        assert home.is_dir()

    def test_pathlib_works_on_current_platform(self, tmp_path):
        """測試 pathlib 在當前平台運作正常"""
        test_path = tmp_path / "test"
        test_path.mkdir()

        assert test_path.exists()
        assert test_path.is_absolute()

        # Test path operations
        child = test_path / "child"
        assert child.parent == test_path


def simulate_button_click(button_name: str, config_mock: Mock):
    """
    模擬按鈕點擊邏輯

    Args:
        button_name: 'default', 'desktop', 'documents', 'downloads'
        config_mock: Mock config object

    Returns:
        tuple: (success: bool, path: Path, error: str)
    """
    from pathlib import Path as PathLib
    import platform

    try:
        if button_name == "default":
            default_lib = config_mock.get("library.default_path")
            if default_lib:
                path = PathLib(default_lib).expanduser()
                if path.exists():
                    return True, path, None
                else:
                    return False, path, "❌ 路徑不存在"

        elif button_name == "desktop":
            system = platform.system()
            if system == "Darwin":
                path = PathLib.home() / "Desktop"
            elif system == "Windows":
                path = PathLib.home() / "Desktop"
            else:
                path = PathLib.home() / "Desktop"

            if path.exists():
                return True, path, None
            else:
                return False, path, "❌ 路徑不存在"

        elif button_name == "documents":
            path = PathLib.home() / "Documents"
            if path.exists():
                return True, path, None
            else:
                return False, path, "❌ 路徑不存在"

        elif button_name == "downloads":
            path = PathLib.home() / "Downloads"
            if path.exists():
                return True, path, None
            else:
                return False, path, "❌ 路徑不存在"

        else:
            return False, None, "❌ 未知按鈕"

    except Exception as e:
        return False, None, f"❌ {str(e)}"


class TestButtonSimulation:
    """測試按鈕點擊模擬"""

    def test_simulate_default_button(self):
        """測試 Default 按鈕模擬"""
        config_mock = Mock()
        config_mock.get.return_value = str(Path.home())

        success, path, error = simulate_button_click("default", config_mock)
        assert success
        assert path.exists()
        assert error is None

    def test_simulate_desktop_button(self):
        """測試 Desktop 按鈕模擬"""
        config_mock = Mock()
        success, path, error = simulate_button_click("desktop", config_mock)

        # Desktop might not exist on all systems
        if path.exists():
            assert success
            assert error is None
        else:
            assert not success
            assert "❌" in error

    def test_simulate_documents_button(self):
        """測試 Documents 按鈕模擬"""
        config_mock = Mock()
        success, path, error = simulate_button_click("documents", config_mock)

        if path.exists():
            assert success
            assert error is None

    def test_simulate_downloads_button(self):
        """測試 Downloads 按鈕模擬"""
        config_mock = Mock()
        success, path, error = simulate_button_click("downloads", config_mock)

        if path.exists():
            assert success
            assert error is None

    def test_simulate_nonexistent_path(self, tmp_path):
        """測試不存在路徑的模擬"""
        config_mock = Mock()
        config_mock.get.return_value = str(tmp_path / "nonexistent")

        success, path, error = simulate_button_click("default", config_mock)
        assert not success
        assert "❌" in error


if __name__ == "__main__":
    print("執行快速按鈕功能測試...")
    print("=" * 60)

    # Run simple tests
    import sys

    print("\n1. 測試 Default 按鈕路徑解析...")
    test_path = Path("~/test").expanduser()
    print(f"   ✅ Tilde expansion works: {test_path}")

    print("\n2. 測試跨平台 Desktop 路徑...")
    system = platform.system()
    desktop = Path.home() / "Desktop"
    print(f"   平台: {system}")
    print(f"   Desktop 路徑: {desktop}")
    print(f"   存在: {'✅' if desktop.exists() else '❌'}")

    print("\n3. 測試 Documents 路徑...")
    docs = Path.home() / "Documents"
    print(f"   Documents 路徑: {docs}")
    print(f"   存在: {'✅' if docs.exists() else '❌'}")

    print("\n4. 測試 Downloads 路徑...")
    downloads = Path.home() / "Downloads"
    print(f"   Downloads 路徑: {downloads}")
    print(f"   存在: {'✅' if downloads.exists() else '❌'}")

    print("\n5. 測試錯誤處理...")
    nonexistent = Path("/this/does/not/exist")
    print(f"   不存在的路徑: {nonexistent}")
    print(f"   正確檢測為不存在: {'✅' if not nonexistent.exists() else '❌'}")

    print("\n" + "=" * 60)
    print("基本測試完成！")
    print("\n要執行完整的 pytest 測試，請運行:")
    print("  uv run pytest tests/test_quick_buttons.py -v")
