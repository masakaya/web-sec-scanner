# mypy型チェックガイド

## 📋 目次

1. [mypyとは](#mypyとは)
2. [型チェックの実行](#型チェックの実行)
3. [型アノテーションの書き方](#型アノテーションの書き方)
4. [段階的な型導入](#段階的な型導入)
5. [よくあるエラーと対処法](#よくあるエラーと対処法)

---

## 🔍 mypyとは

mypyはPythonの静的型チェッカーです。コードを実行する前に型の問題を検出できます。

**メリット:**
- 🐛 バグを早期に発見
- 📚 コードの可読性向上（型が明示的）
- 🔧 IDEのサポート強化（自動補完、リファクタリング）
- 📖 ドキュメントとしての役割

---

## 🚀 型チェックの実行

### 基本的な実行

```bash
# 型チェック実行
poe typecheck

# または直接mypy
uv run mypy .
```

### strictモードで実行

```bash
# より厳格なチェック
poe typecheck-strict

# または
uv run mypy . --strict
```

### reviewdogと連携（ローカル）

```bash
# reviewdogで結果を表示
poe typecheck-review

# または直接実行
./scripts/mypy-review.sh
```

### 特定のファイルのみチェック

```bash
# 単一ファイル
poe typecheck main.py

# 複数ファイル
poe typecheck main.py generate_review_doc.py

# ディレクトリ
poe typecheck src/

# または直接mypy
uv run mypy main.py
```

### 統合チェック

```bash
# lint + format + typecheck + test
poe check

# CI用（カバレッジ + レビュー含む）
poe ci
```

---

## ✍️ 型アノテーションの書き方

### 基本的な型

```python
# 変数の型アノテーション
name: str = "Alice"
age: int = 30
height: float = 1.75
is_student: bool = False

# 複数の型を許可（Union）
from typing import Union
value: Union[int, str] = 42
# Python 3.10+では | を使用可
value: int | str = 42
```

### 関数の型アノテーション

```python
def greet(name: str) -> str:
    """挨拶を返す"""
    return f"Hello, {name}!"

def calculate(x: int, y: int) -> int:
    """計算を行う"""
    return x + y

# 返り値がない場合
def log_message(message: str) -> None:
    """メッセージをログに出力"""
    print(message)
```

### コレクションの型

```python
from typing import List, Dict, Set, Tuple, Optional

# リスト
numbers: list[int] = [1, 2, 3]
names: list[str] = ["Alice", "Bob"]

# 辞書
user: dict[str, int] = {"age": 30, "score": 100}

# セット
tags: set[str] = {"python", "mypy"}

# タプル（固定長）
point: tuple[int, int] = (10, 20)

# タプル（可変長）
values: tuple[int, ...] = (1, 2, 3, 4, 5)

# Optional（Noneを許可）
name: Optional[str] = None
# または
name: str | None = None
```

### カスタム型エイリアス

```python
from typing import Any

# 型エイリアス
UserId = int
UserName = str
RuffIssue = dict[str, Any]

def get_user(user_id: UserId) -> UserName:
    """ユーザー名を取得"""
    return f"User{user_id}"

def process_issues(issues: list[RuffIssue]) -> None:
    """Ruffの問題を処理"""
    for issue in issues:
        print(issue["message"])
```

### クラスの型アノテーション

```python
class User:
    """ユーザークラス"""

    def __init__(self, name: str, age: int) -> None:
        self.name: str = name
        self.age: int = age

    def greet(self) -> str:
        """挨拶を返す"""
        return f"Hello, I'm {self.name}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """辞書からUserを作成"""
        return cls(data["name"], data["age"])
```

### ジェネリクス

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Box(Generic[T]):
    """汎用的なボックス"""

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        """値を取得"""
        return self.value

# 使用例
int_box: Box[int] = Box(42)
str_box: Box[str] = Box("Hello")
```

---

## 📈 段階的な型導入

### レベル1: 最低限の型アノテーション

```python
# 関数のシグネチャのみ
def process_data(data):  # type: ignore
    """データ処理"""
    return data

# 徐々に追加
def process_data(data: dict) -> dict:
    """データ処理"""
    return data
```

### レベル2: 明示的な型

```python
# より具体的に
def process_data(data: dict[str, Any]) -> dict[str, Any]:
    """データ処理"""
    return data
```

### レベル3: 厳密な型

```python
from typing import TypedDict

class UserData(TypedDict):
    """ユーザーデータの型定義"""
    name: str
    age: int
    email: str

def process_data(data: UserData) -> UserData:
    """データ処理"""
    return data
```

### プロジェクトの設定

`pyproject.toml`で段階的に厳格化：

```toml
[tool.mypy]
# 初期設定（緩い）
disallow_untyped_defs = false

# 中級設定
disallow_untyped_defs = true
disallow_incomplete_defs = true

# 厳格設定
strict = true
```

---

## 🐛 よくあるエラーと対処法

### 1. Incompatible types

```python
# ❌ エラー
name: str = 123  # error: Incompatible types in assignment

# ✅ 修正
name: str = "Alice"
# または型を変更
name: int = 123
```

### 2. Missing return statement

```python
# ❌ エラー
def get_name() -> str:
    if condition:
        return "Alice"
    # error: Missing return statement

# ✅ 修正
def get_name() -> str:
    if condition:
        return "Alice"
    return "Unknown"
```

### 3. Argument type mismatch

```python
# ❌ エラー
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(123)  # error: Argument 1 has incompatible type

# ✅ 修正
greet("Alice")
```

### 4. Returning Any

```python
import json

# ❌ エラー
def load_data() -> dict[str, str]:
    return json.loads('{"key": "value"}')
    # error: Returning Any from function

# ✅ 修正
def load_data() -> dict[str, str]:
    data: dict[str, str] = json.loads('{"key": "value"}')
    return data
```

### 5. Missing type hints

```python
# ❌ エラー（strict mode）
def process(data):  # error: Missing type hints
    return data

# ✅ 修正
def process(data: Any) -> Any:
    return data

# または型を明示
def process(data: dict[str, int]) -> dict[str, int]:
    return data
```

### 6. サードパーティライブラリの型

```python
# ❌ エラー
import some_library  # error: Library stubs not installed

# ✅ 修正1: 型スタブをインストール
# uv add --dev types-some_library

# ✅ 修正2: pyproject.tomlで無視
# [tool.mypy]
# [[tool.mypy.overrides]]
# module = ["some_library.*"]
# ignore_missing_imports = true
```

---

## 🎯 ベストプラクティス

### 1. 公開APIには型を付ける

```python
# 公開関数・クラスには必ず型を付ける
def public_function(arg: str) -> int:
    """公開API"""
    return _private_helper(arg)

# プライベート関数は任意
def _private_helper(arg):
    """内部関数"""
    return len(arg)
```

### 2. 複雑な型は型エイリアスを使う

```python
# ❌ 読みにくい
def process(data: dict[str, list[tuple[int, str]]]) -> dict[str, list[tuple[int, str]]]:
    pass

# ✅ 読みやすい
DataMap = dict[str, list[tuple[int, str]]]

def process(data: DataMap) -> DataMap:
    pass
```

### 3. Anyは最小限に

```python
# ❌ Anyを多用
def process(data: Any) -> Any:
    pass

# ✅ できるだけ具体的に
def process(data: dict[str, int]) -> list[str]:
    pass
```

### 4. 型ガードを活用

```python
from typing import Union

def process_value(value: Union[int, str]) -> str:
    if isinstance(value, int):
        # この中では value は int として扱われる
        return str(value * 2)
    else:
        # この中では value は str として扱われる
        return value.upper()
```

---

## 📚 参考リンク

- [mypy公式ドキュメント](https://mypy.readthedocs.io/)
- [Python typing モジュール](https://docs.python.org/3/library/typing.html)
- [Type hinting cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)

---

## 🔧 設定ファイル

プロジェクトの設定は `pyproject.toml` で管理：

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # 段階的に true へ
check_untyped_defs = true
strict_equality = true
```

詳細は `pyproject.toml` の `[tool.mypy]` セクションを参照してください。

---

## 🤖 CI/CD統合

### GitHub Actions + reviewdog

`.github/workflows/mypy.yml` でmypyチェックが自動実行されます。

**動作:**
1. **PR作成時に自動実行**
2. **reviewdogによる自動レビュー**
   - PRの該当行に型エラーをコメント
   - エラーレベル: error（重要度高）
   - すべてのPRに対応

**表示例:**
```
📝 Files changed タブ

main.py
  15  | def process(data):
      | ^^^^^^^^^^^^ error: Missing return type annotation
      |
      | 💡 関数には戻り値の型アノテーションを追加してください
      | 📚 詳細: https://mypy.readthedocs.io/
```

**ローカルで同じチェック:**
```bash
poe typecheck-review
# または
./.github/scripts/mypy-review.sh
```
