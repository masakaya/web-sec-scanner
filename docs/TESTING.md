# テストガイド

## 📋 目次

1. [インストール済みツール](#インストール済みツール)
2. [テストの実行](#テストの実行)
3. [カバレッジレポート](#カバレッジレポート)
4. [テストの書き方](#テストの書き方)
5. [ベストプラクティス](#ベストプラクティス)

---

## 🛠️ インストール済みツール

- **pytest** - Pythonテストフレームワーク
- **pytest-cov** - カバレッジレポート生成

設定は `pyproject.toml` で管理されています。

---

## 🚀 テストの実行

### 基本的な実行

```bash
# すべてのテストを実行
uv run poe test

# または直接pytest
uv run pytest
```

### カバレッジ付き実行

```bash
# カバレッジレポートを生成（ターミナル + HTML）
uv run poe test-cov

# HTMLレポートを確認
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 詳細な出力

```bash
# より詳細な出力
uv run poe test-verbose

# または
uv run pytest -v
```

### 特定のテストを実行

```bash
# ファイル単位
uv run pytest tests/test_example.py

# 特定のテスト関数
uv run pytest tests/test_example.py::test_example

# 特定のクラス
uv run pytest tests/test_example.py::TestExample

# 特定のメソッド
uv run pytest tests/test_example.py::TestExample::test_addition
```

### マーカーを使った実行

```bash
# unitテストのみ実行
uv run pytest -m unit

# slowテストを除外
uv run pytest -m "not slow"

# integrationテストのみ実行
uv run pytest -m integration
```

### パターンマッチング

```bash
# 名前でフィルタ
uv run pytest -k "test_addition"

# 複数パターン
uv run pytest -k "test_addition or test_subtraction"
```

---

## 📊 カバレッジレポート

### カバレッジの確認

```bash
# ターミナルでカバレッジを表示
uv run pytest --cov=. --cov-report=term-missing

# HTMLレポートを生成
uv run poe test-cov
```

### カバレッジレポートの見方

**ターミナル出力:**
```
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
main.py                      2      0   100%
my_module.py                20      5    75%   10-15
------------------------------------------------------
TOTAL                       22      5    77%
```

- **Stmts**: 実行可能な文の数
- **Miss**: カバーされていない文の数
- **Cover**: カバレッジの割合
- **Missing**: カバーされていない行番号

**HTMLレポート:**
- `htmlcov/index.html` をブラウザで開く
- ファイルごとの詳細なカバレッジ
- カバーされていない行がハイライト表示

---

## ✍️ テストの書き方

### 基本的なテスト

```python
# tests/test_basic.py

def test_simple():
    """Basic test."""
    assert 1 + 1 == 2
```

### クラスベースのテスト

```python
class TestCalculator:
    """Calculator test class."""

    def test_add(self):
        """Test addition."""
        assert 2 + 2 == 4

    def test_subtract(self):
        """Test subtraction."""
        assert 5 - 3 == 2
```

### パラメータ化テスト

```python
import pytest

@pytest.mark.parametrize(
    "input_value,expected",
    [
        (1, 2),
        (2, 4),
        (3, 6),
    ],
)
def test_double(input_value, expected):
    """Test with multiple inputs."""
    assert input_value * 2 == expected
```

### フィクスチャの使用

```python
import pytest

@pytest.fixture
def sample_data():
    """Setup test data."""
    return {"name": "Test", "value": 42}

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["name"] == "Test"
```

### マーカーの使用

```python
import pytest

@pytest.mark.unit
def test_unit():
    """Unit test."""
    assert True

@pytest.mark.integration
def test_integration():
    """Integration test."""
    assert True

@pytest.mark.slow
def test_slow():
    """Slow test."""
    import time
    time.sleep(1)
    assert True
```

### 例外のテスト

```python
import pytest

def test_exception():
    """Test that exception is raised."""
    with pytest.raises(ValueError):
        raise ValueError("Expected error")

def test_exception_message():
    """Test exception with specific message."""
    with pytest.raises(ValueError, match="Expected error"):
        raise ValueError("Expected error")
```

---

## 🎯 ベストプラクティス

### 1. テストの構造

```
tests/
├── __init__.py
├── conftest.py              # 共有フィクスチャ
├── test_module1.py
├── test_module2.py
└── integration/
    ├── __init__.py
    └── test_integration.py
```

### 2. テスト名の命名規則

- `test_` で始める
- 何をテストするか明確に
- 動詞で始める

**良い例:**
```python
def test_user_can_login()
def test_validates_email_format()
def test_returns_empty_list_when_no_data()
```

**悪い例:**
```python
def test1()
def test_user()
def test_data()
```

### 3. Arrange-Act-Assert パターン

```python
def test_user_creation():
    # Arrange - テストデータを準備
    username = "testuser"
    email = "test@example.com"

    # Act - 実行
    user = User(username, email)

    # Assert - 検証
    assert user.username == username
    assert user.email == email
```

### 4. テストの独立性

各テストは独立して実行可能にする：

```python
# ❌ 悪い例（共有状態に依存）
shared_data = []

def test_append():
    shared_data.append(1)
    assert len(shared_data) == 1

def test_append_again():
    shared_data.append(2)
    assert len(shared_data) == 2  # 実行順序に依存！

# ✅ 良い例（フィクスチャを使用）
@pytest.fixture
def data():
    return []

def test_append(data):
    data.append(1)
    assert len(data) == 1

def test_append_again(data):
    data.append(2)
    assert len(data) == 1  # 独立！
```

### 5. マーカーの活用

```python
# 遅いテストをマーク
@pytest.mark.slow
def test_slow_operation():
    ...

# 環境依存のテストをマーク
@pytest.mark.integration
def test_api_call():
    ...

# スキップ
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    ...
```

### 6. カバレッジ目標

- **目標**: 80%以上
- **重要な部分**: ビジネスロジック、データ処理
- **除外可能**: テストコード、デバッグコード、`if __name__ == "__main__"`

---

## 📚 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [カバレッジ.py](https://coverage.readthedocs.io/)

---

## 🔄 CI/CD統合

GitHub Actionsで自動テスト実行：

```yaml
# .github/workflows/ruff.yml に統合済み
- name: Run tests
  run: uv run pytest --cov=. --cov-report=term --cov-report=xml
```

カバレッジレポートは自動的にCodecovにアップロードされます（CODECOV_TOKEN設定時）。
